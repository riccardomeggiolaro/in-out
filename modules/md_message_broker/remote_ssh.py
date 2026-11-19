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
- `ssh_user` (default "root" su Linux, l'utente dell'in-out su Windows): utente con cui si apre il terminale;
- `ssh_port` (default 22): porta del sshd locale.

Linux: la chiave va in ~<ssh_user>/.ssh/authorized_keys.
Windows (Win32-OpenSSH): se OpenSSH Server manca, l'in-out ne avvia l'installazione
(Add-WindowsCapability, serve che giri come amministratore) e lo avvia; la chiave va in
C:\\ProgramData\\ssh\\administrators_authorized_keys se l'utente è amministratore, altrimenti
in %USERPROFILE%\\.ssh\\authorized_keys, con i permessi richiesti da sshd. Su Windows
l'utente di default è quello con cui gira l'in-out.
"""

import getpass
import os
import re
import socket
import subprocess
import tempfile
import threading
from typing import Callable, Dict, Optional

import libs.lb_config as lb_config
import libs.lb_log as lb_log

try:
	import pwd
except ImportError:  # Windows
	pwd = None

IS_WINDOWS = os.name == "nt"
# Commento che identifica la riga installata dall'in-out in authorized_keys
KEY_MARKER = "in-out-remote-broker"
KEY_OPTIONS = 'from="127.0.0.1,::1",no-agent-forwarding,no-X11-forwarding,no-port-forwarding'
RE_PUBLIC_KEY = re.compile(r"^(ssh-ed25519|ecdsa-sha2-nistp256|ecdsa-sha2-nistp384|ecdsa-sha2-nistp521|ssh-rsa) [A-Za-z0-9+/]+={0,3}$")
# Linux: nomi POSIX. Windows: anche maiuscole, spazi e dominio (DOMINIO\utente)
RE_USER = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_. \\@-]{0,63}$")
CONNECT_TIMEOUT = 10
READ_SIZE = 32 * 1024
MAX_SESSIONS = 8
# Windows: SID dei gruppi usati nei permessi dei file delle chiavi (indipendenti dalla lingua)
SID_ADMINISTRATORS = "*S-1-5-32-544"
SID_SYSTEM = "*S-1-5-18"
WINDOWS_CAPABILITY = "OpenSSH.Server~~~~0.0.1.0"
SUBPROCESS_FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _settings() -> dict:
	broker = (lb_config.g_config.get("app_api", {}).get("message_broker") or {}).get("broker")
	return broker if isinstance(broker, dict) else {}


def enabled() -> bool:
	return _settings().get("remote_ssh", True) is not False


def ssh_user() -> str:
	user = str(_settings().get("ssh_user") or "").strip()
	if IS_WINDOWS and user in ("", "root"):
		# Su Windows "root" non esiste: utente con cui gira l'in-out
		user = getpass.getuser()
	return user or "root"


def ssh_port() -> int:
	try:
		return int(_settings().get("ssh_port") or 22)
	except (TypeError, ValueError):
		return 22


def supported() -> bool:
	return IS_WINDOWS or (os.name == "posix" and pwd is not None)


def sshd_listening(timeout: float = 1.0) -> bool:
	try:
		with socket.create_connection(("127.0.0.1", ssh_port()), timeout=timeout):
			return True
	except OSError:
		return False


def _run(args, timeout: float = 60) -> subprocess.CompletedProcess:
	return subprocess.run(args, capture_output=True, text=True, timeout=timeout, creationflags=SUBPROCESS_FLAGS)


def _powershell(script: str, timeout: float = 60) -> subprocess.CompletedProcess:
	return _run(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script], timeout)


# ----------------------------------------------------------------------
# File delle chiavi
# ----------------------------------------------------------------------
class _KeyFile:
	"""Un file authorized_keys da tenere aggiornato, con i permessi giusti per sshd."""

	def __init__(self, path: str, fix_permissions: Callable[[str], None]):
		self.path = path
		self.fix_permissions = fix_permissions

	def read(self) -> list:
		try:
			with open(self.path, "r", encoding="utf-8-sig", errors="replace") as f:
				return f.read().splitlines()
		except FileNotFoundError:
			return []

	def write(self, lines) -> None:
		directory = os.path.dirname(self.path)
		os.makedirs(directory, exist_ok=True)
		fd, tmp = tempfile.mkstemp(dir=directory, prefix=".authorized_keys.")
		try:
			with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
				f.write("".join(line + "\n" for line in lines))
			os.replace(tmp, self.path)
		except Exception:
			try:
				os.unlink(tmp)
			except OSError:
				pass
			raise
		self.fix_permissions(self.path)


def _linux_key_files(user: str) -> list:
	try:
		account = pwd.getpwnam(user)
	except KeyError:
		raise RuntimeError(f"l'utente '{user}' non esiste sull'in-out")
	if os.geteuid() != 0 and account.pw_uid != os.geteuid():
		raise RuntimeError(f"l'in-out non ha i permessi per configurare l'utente '{user}'")
	ssh_dir = os.path.join(account.pw_dir, ".ssh")

	def fix(path: str) -> None:
		os.chmod(ssh_dir, 0o700)
		os.chmod(path, 0o600)
		if os.geteuid() == 0:
			os.chown(ssh_dir, account.pw_uid, account.pw_gid)
			os.chown(path, account.pw_uid, account.pw_gid)

	return [_KeyFile(os.path.join(ssh_dir, "authorized_keys"), fix)]


def _windows_is_admin(user: str) -> Optional[bool]:
	"""True/False se l'utente è (o non è) nel gruppo Administrators; None se non si riesce a saperlo."""
	name = user.split("\\")[-1].lower()
	try:
		res = _powershell(
			f"Get-LocalGroupMember -SID S-1-5-32-544 | ForEach-Object {{ $_.Name }}", timeout=30,
		)
	except (OSError, subprocess.SubprocessError):
		return None
	if res.returncode != 0:
		return None
	members = [line.strip().split("\\")[-1].lower() for line in res.stdout.splitlines() if line.strip()]
	return name in members


def _windows_key_files(user: str) -> list:
	"""Win32-OpenSSH: gli amministratori usano solo C:\\ProgramData\\ssh\\administrators_authorized_keys,
	gli altri utenti %USERPROFILE%\\.ssh\\authorized_keys. Se non si sa se l'utente è
	amministratore si aggiornano entrambi."""
	program_data = os.environ.get("ProgramData", r"C:\ProgramData")
	admin_file = os.path.join(program_data, "ssh", "administrators_authorized_keys")
	short = user.split("\\")[-1]
	if short.lower() == getpass.getuser().lower():
		profile = os.path.expanduser("~")
	else:
		profile = os.path.join(os.environ.get("SystemDrive", "C:") + "\\", "Users", short)

	def fix_admin(path: str) -> None:
		_run(["icacls", path, "/inheritance:r", "/grant", f"{SID_ADMINISTRATORS}:F", "/grant", f"{SID_SYSTEM}:F"])

	def fix_user(path: str) -> None:
		_run(["icacls", path, "/inheritance:r", "/grant", f"{short}:F", "/grant", f"{SID_SYSTEM}:F",
			  "/grant", f"{SID_ADMINISTRATORS}:F"])

	admin = _windows_is_admin(user)
	files = []
	if admin is not False:
		files.append(_KeyFile(admin_file, fix_admin))
	if admin is not True:
		if not os.path.isdir(profile):
			if admin is False:
				raise RuntimeError(f"cartella dell'utente '{user}' non trovata ({profile})")
		else:
			files.append(_KeyFile(os.path.join(profile, ".ssh", "authorized_keys"), fix_user))
	return files


def _key_files(user: str) -> list:
	if not supported():
		raise RuntimeError("terminale remoto non disponibile su questo sistema operativo")
	if not RE_USER.match(user or ""):
		raise RuntimeError(f"utente SSH non valido: {user!r}")
	if IS_WINDOWS:
		if user.endswith("$"):
			raise RuntimeError("l'in-out gira come servizio di sistema: imposta l'utente SSH nelle impostazioni del broker")
		return _windows_key_files(user)
	return _linux_key_files(user)


def install_key(user: str, public_key: str, client_id: str) -> None:
	"""Installa (o aggiorna) la chiave del broker in authorized_keys dell'utente."""
	parts = (public_key or "").strip().split()
	if len(parts) < 2 or not RE_PUBLIC_KEY.match(f"{parts[0]} {parts[1]}"):
		raise RuntimeError("chiave SSH del broker non valida")
	line = f"{KEY_OPTIONS} {parts[0]} {parts[1]} {KEY_MARKER}:{client_id}"
	changed = False
	for key_file in _key_files(user):
		lines = key_file.read()
		others = [l for l in lines if KEY_MARKER not in l]
		if others + [line] != lines:
			key_file.write(others + [line])
			changed = True
	if changed:
		lb_log.info(f"Terminale remoto: chiave del broker installata per l'utente '{user}'")


def remove_key(user: Optional[str]) -> None:
	"""Toglie la chiave del broker da authorized_keys (accesso SSH disattivato o utente cambiato)."""
	if not user or not supported():
		return
	if IS_WINDOWS and user == "root":
		user = getpass.getuser()
	try:
		for key_file in _key_files(user):
			lines = key_file.read()
			others = [l for l in lines if KEY_MARKER not in l]
			if others != lines:
				key_file.write(others)
				lb_log.info(f"Terminale remoto: chiave del broker rimossa da {key_file.path}")
	except Exception as e:
		lb_log.warning(f"Terminale remoto: impossibile rimuovere la chiave del broker per '{user}': {e}")


# ----------------------------------------------------------------------
# Windows: OpenSSH Server
# ----------------------------------------------------------------------
_install_lock = threading.Lock()
_install_state = {"running": False, "error": None}


def _windows_service_state() -> Optional[str]:
	"""'RUNNING', 'STOPPED'... oppure None se il servizio sshd non esiste."""
	try:
		res = _run(["sc", "query", "sshd"], timeout=15)
	except (OSError, subprocess.SubprocessError):
		return None
	if res.returncode != 0:
		return None
	m = re.search(r"STATE\s*:\s*\d+\s+(\w+)", res.stdout)
	return m.group(1) if m else "UNKNOWN"


def _windows_install_sshd() -> None:
	try:
		lb_log.info("Terminale remoto: installazione di OpenSSH Server in corso")
		res = _powershell(f"Add-WindowsCapability -Online -Name {WINDOWS_CAPABILITY} | Out-Null", timeout=1800)
		if res.returncode != 0:
			raise RuntimeError((res.stderr or res.stdout).strip()[:300] or "installazione non riuscita")
		_powershell("Set-Service -Name sshd -StartupType Automatic; Start-Service sshd", timeout=120)
		_install_state["error"] = None
		lb_log.info("Terminale remoto: OpenSSH Server installato e avviato")
	except Exception as e:
		_install_state["error"] = f"installazione di OpenSSH Server non riuscita: {e}"
		lb_log.error(f"Terminale remoto: {_install_state['error']}")
	finally:
		_install_state["running"] = False


def ensure_windows_sshd() -> None:
	"""Su Windows avvia sshd o, se manca, ne avvia l'installazione in background.
	Solleva RuntimeError con un messaggio per il pannello se il server non è ancora pronto."""
	if not IS_WINDOWS or sshd_listening():
		return
	state = _windows_service_state()
	if state is not None:
		if state != "RUNNING":
			res = _powershell("Set-Service -Name sshd -StartupType Automatic; Start-Service sshd", timeout=60)
			if res.returncode != 0:
				raise RuntimeError("impossibile avviare il servizio sshd di Windows (serve che l'in-out "
								   "giri come amministratore): " + (res.stderr or "").strip()[:200])
		return
	with _install_lock:
		if _install_state["running"]:
			raise RuntimeError("installazione di OpenSSH Server in corso sull'in-out: riprova tra qualche minuto")
		if _install_state["error"]:
			error, _install_state["error"] = _install_state["error"], None
			raise RuntimeError(error)
		_install_state["running"] = True
	threading.Thread(target=_windows_install_sshd, name="remote-ssh-install", daemon=True).start()
	raise RuntimeError("OpenSSH Server non era installato: installazione avviata sull'in-out, "
					   "riprova tra qualche minuto")


def status() -> dict:
	"""Stato del terminale remoto per il pannello del broker."""
	info = {
		"supported": supported(),
		"enabled": enabled(),
		"user": ssh_user() if supported() else None,
		"port": ssh_port(),
		"listening": sshd_listening() if supported() else False,
		"installing": _install_state["running"],
	}
	if IS_WINDOWS:
		info["service"] = _windows_service_state()
	return info


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
			ensure_windows_sshd()
			install_key(user, str(header.get("key") or ""), self.client_id)
		except Exception as e:
			fail(str(e))
			return
		try:
			sock = socket.create_connection(("127.0.0.1", ssh_port()), timeout=CONNECT_TIMEOUT)
		except OSError as e:
			hint = ("avvia il servizio OpenSSH Server" if IS_WINDOWS
					else "installa e avvia openssh-server: sudo apt-get install -y openssh-server && sudo systemctl enable --now ssh")
			fail(f"sshd non raggiungibile su 127.0.0.1:{ssh_port()} ({e}): {hint}")
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
