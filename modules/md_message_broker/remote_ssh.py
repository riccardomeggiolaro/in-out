"""
Terminale SSH remoto dal pannello del broker
============================================

Il pannello del broker apre un terminale sull'in-out passando dalla connessione MQTT
già aperta (stesso canale dell'accesso remoto, vedi `remote_tunnel.py`): i byte della
connessione SSH viaggiano nel tunnel e l'in-out li inoltra al suo sshd locale
(127.0.0.1:<ssh_port>). La sessione SSH è cifrata da un capo all'altro: il broker fa
da client SSH, l'in-out vede solo byte cifrati.

Autenticazione con chiave: il broker ha una sua chiave SSH (la privata resta sul broker)
e manda la chiave pubblica in ogni richiesta di apertura. L'in-out la installa in
`~<ssh_user>/.ssh/authorized_keys` con il vincolo `from="127.0.0.1,::1"`: la chiave
vale solo per le connessioni arrivate attraverso il tunnel. Il topic delle richieste
(<client_id>/tunnel/req) può essere scritto solo dal broker (ACL di Mosquitto).

Messaggi (intestazione JSON + "\\n" + corpo, come il resto del tunnel):

    pannello -> in-out                         in-out -> pannello
    {"t":"ssh_open","id","key"}                {"t":"ssh_open","id","ok","user","error"}
    {"t":"ssh_data","id"} + byte               {"t":"ssh_data","id"} + byte
    {"t":"ssh_close","id"}                     {"t":"ssh_close","id"}

Impostazioni (configurazione del broker sull'in-out):
- `remote_ssh` (default true): se false le richieste vengono rifiutate e la chiave
  del broker viene tolta da authorized_keys;
- `ssh_user` (default "root"): utente Linux con cui si apre il terminale;
- `ssh_port` (default 22): porta del sshd locale.

Solo Linux: su Windows le richieste vengono rifiutate.
"""

import os
import re
import socket
import tempfile
import threading
from typing import Callable, Dict, Optional

import libs.lb_config as lb_config
import libs.lb_log as lb_log

try:
	import pwd
except ImportError:  # Windows
	pwd = None

# Commento che identifica la riga installata dall'in-out in authorized_keys
KEY_MARKER = "in-out-remote-broker"
KEY_OPTIONS = 'from="127.0.0.1,::1",no-agent-forwarding,no-X11-forwarding,no-port-forwarding'
RE_PUBLIC_KEY = re.compile(r"^(ssh-ed25519|ecdsa-sha2-nistp256|ecdsa-sha2-nistp384|ecdsa-sha2-nistp521|ssh-rsa) [A-Za-z0-9+/]+={0,3}$")
RE_USER = re.compile(r"^[a-z_][a-z0-9_.-]{0,31}$")
CONNECT_TIMEOUT = 10
READ_SIZE = 32 * 1024
MAX_SESSIONS = 8


def _settings() -> dict:
	broker = (lb_config.g_config.get("app_api", {}).get("message_broker") or {}).get("broker")
	return broker if isinstance(broker, dict) else {}


def enabled() -> bool:
	return _settings().get("remote_ssh", True) is not False


def ssh_user() -> str:
	return str(_settings().get("ssh_user") or "root").strip()


def ssh_port() -> int:
	try:
		return int(_settings().get("ssh_port") or 22)
	except (TypeError, ValueError):
		return 22


def supported() -> bool:
	return os.name == "posix" and pwd is not None


# ----------------------------------------------------------------------
# authorized_keys
# ----------------------------------------------------------------------
def _account(user: str):
	if not supported():
		raise RuntimeError("terminale remoto disponibile solo sugli in-out Linux")
	if not RE_USER.match(user or ""):
		raise RuntimeError(f"utente SSH non valido: {user!r}")
	try:
		return pwd.getpwnam(user)
	except KeyError:
		raise RuntimeError(f"l'utente '{user}' non esiste sull'in-out")


def _write_keys(account, lines) -> None:
	ssh_dir = os.path.join(account.pw_dir, ".ssh")
	path = os.path.join(ssh_dir, "authorized_keys")
	if not os.path.isdir(ssh_dir):
		os.makedirs(ssh_dir, mode=0o700, exist_ok=True)
		if os.geteuid() == 0:
			os.chown(ssh_dir, account.pw_uid, account.pw_gid)
	fd, tmp = tempfile.mkstemp(dir=ssh_dir, prefix=".authorized_keys.")
	try:
		with os.fdopen(fd, "w") as f:
			f.write("".join(line + "\n" for line in lines))
		os.chmod(tmp, 0o600)
		if os.geteuid() == 0:
			os.chown(tmp, account.pw_uid, account.pw_gid)
		os.replace(tmp, path)
	except Exception:
		try:
			os.unlink(tmp)
		except OSError:
			pass
		raise


def _read_keys(account) -> list:
	path = os.path.join(account.pw_dir, ".ssh", "authorized_keys")
	try:
		with open(path, "r", encoding="utf-8", errors="replace") as f:
			return f.read().splitlines()
	except FileNotFoundError:
		return []


def install_key(user: str, public_key: str, client_id: str) -> None:
	"""Installa (o aggiorna) la chiave del broker in authorized_keys dell'utente."""
	parts = (public_key or "").strip().split()
	if len(parts) < 2 or not RE_PUBLIC_KEY.match(f"{parts[0]} {parts[1]}"):
		raise RuntimeError("chiave SSH del broker non valida")
	account = _account(user)
	if os.geteuid() != 0 and account.pw_uid != os.geteuid():
		raise RuntimeError(f"l'in-out non ha i permessi per configurare l'utente '{user}'")
	line = f"{KEY_OPTIONS} {parts[0]} {parts[1]} {KEY_MARKER}:{client_id}"
	lines = _read_keys(account)
	others = [l for l in lines if KEY_MARKER not in l]
	if others + [line] == lines:
		return
	_write_keys(account, others + [line])
	lb_log.info(f"Terminale remoto: chiave del broker installata per l'utente '{user}'")


def remove_key(user: Optional[str]) -> None:
	"""Toglie la chiave del broker da authorized_keys (accesso SSH disattivato o utente cambiato)."""
	if not user or not supported():
		return
	try:
		account = _account(user)
		lines = _read_keys(account)
		others = [l for l in lines if KEY_MARKER not in l]
		if others != lines:
			_write_keys(account, others)
			lb_log.info(f"Terminale remoto: chiave del broker rimossa per l'utente '{user}'")
	except Exception as e:
		lb_log.warning(f"Terminale remoto: impossibile rimuovere la chiave del broker per '{user}': {e}")


# ----------------------------------------------------------------------
# Sessioni
# ----------------------------------------------------------------------
class RemoteSSH:
	def __init__(self, client_id: str, send: Callable[[dict, bytes], bool]):
		self.client_id = client_id
		self.send = send
		self._sockets: Dict[str, socket.socket] = {}
		self._lock = threading.Lock()

	def handle(self, kind: str, sid: str, header: dict, body: bytes) -> None:
		"""Chiamato dal thread di rete di paho: l'apertura va in un thread a parte."""
		if kind == "ssh_open":
			threading.Thread(target=self._open, args=(sid, header), name=f"remote-ssh-{sid[:8]}", daemon=True).start()
		elif kind == "ssh_data":
			with self._lock:
				sock = self._sockets.get(sid)
			if sock is None:
				self.send({"t": "ssh_close", "id": sid})
				return
			try:
				sock.sendall(body)
			except OSError:
				self._close(sid, notify=True)
		elif kind == "ssh_close":
			self._close(sid, notify=False)

	def close_all(self) -> None:
		with self._lock:
			sockets = list(self._sockets.values())
			self._sockets.clear()
		for sock in sockets:
			try:
				sock.close()
			except OSError:
				pass

	def _close(self, sid: str, notify: bool) -> None:
		with self._lock:
			sock = self._sockets.pop(sid, None)
		if sock is None:
			return
		try:
			sock.shutdown(socket.SHUT_RDWR)
		except OSError:
			pass
		try:
			sock.close()
		except OSError:
			pass
		if notify:
			self.send({"t": "ssh_close", "id": sid})

	def _open(self, sid: str, header: dict) -> None:
		def fail(message: str) -> None:
			self.send({"t": "ssh_open", "id": sid, "ok": False, "error": message})

		if not enabled():
			fail("terminale remoto disattivato sull'in-out")
			return
		with self._lock:
			if len(self._sockets) >= MAX_SESSIONS:
				fail("troppi terminali aperti su questo in-out")
				return
		user = ssh_user()
		try:
			install_key(user, str(header.get("key") or ""), self.client_id)
		except Exception as e:
			fail(str(e))
			return
		try:
			sock = socket.create_connection(("127.0.0.1", ssh_port()), timeout=CONNECT_TIMEOUT)
		except OSError as e:
			fail(f"sshd non raggiungibile su 127.0.0.1:{ssh_port()} ({e}): è installato e attivo?")
			return
		sock.settimeout(None)
		sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
		with self._lock:
			self._sockets[sid] = sock
		if not self.send({"t": "ssh_open", "id": sid, "ok": True, "user": user}):
			self._close(sid, notify=False)
			return
		lb_log.info(f"Terminale remoto aperto dal broker (utente '{user}')")
		try:
			while True:
				data = sock.recv(READ_SIZE)
				if not data:
					break
				if not self.send({"t": "ssh_data", "id": sid}, data):
					break
		except OSError:
			pass
		# Chiuso da sshd (logout) o errore: lo si comunica al pannello
		self._close(sid, notify=True)
