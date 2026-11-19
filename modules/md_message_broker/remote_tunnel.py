"""
Accesso remoto dal pannello del broker
======================================

Il pannello del broker inoltra all'in-out, attraverso la connessione MQTT già aperta,
le richieste HTTP e i websocket dell'interfaccia web: l'in-out li esegue sulla sua
API locale (http://127.0.0.1:<porta app_api>) e risponde sullo stesso canale.
Così l'in-out si controlla da remoto senza aprire porte verso l'impianto.

Topic (il broker permette all'in-out di leggere solo i propri):
- richieste dal pannello:  <client_id>/tunnel/req
- risposte al pannello:    <client_id>/tunnel/res

Ogni messaggio è: intestazione JSON su una riga, "\\n", corpo binario.

    pannello -> in-out                                     in-out -> pannello
    {"t":"http","id","method","path","headers"} + corpo     {"t":"http","id","status","headers"} + corpo
                                                            {"t":"http","id","error"}
    {"t":"ws_open","id","path","headers","subprotocols"}    {"t":"ws_open","id","ok","subprotocol","error"}
    {"t":"ws_msg","id","bin"} + dati                         {"t":"ws_msg","id","bin"} + dati
    {"t":"ws_close","id","code"}                             {"t":"ws_close","id","code"}

L'accesso remoto si può disattivare con `app_api.message_broker.remote_access = false`.

Sullo stesso canale passa anche il terminale SSH del pannello (messaggi ssh_*, vedi
`remote_ssh.py`), che ha un interruttore separato (`remote_ssh` nella configurazione del broker).
"""

import http.client
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, Optional

import libs.lb_config as lb_config
import libs.lb_log as lb_log
from modules.md_message_broker.remote_ssh import RemoteSSH

try:  # import a livello di modulo: così PyInstaller include anche websockets.sync
	from websockets.sync.client import connect as ws_connect
except ImportError:  # pragma: no cover
	ws_connect = None

TUNNEL_REQ_SUFFIX = "tunnel/req"
TUNNEL_RES_SUFFIX = "tunnel/res"
# QoS 0: sulla stessa connessione i messaggi arrivano in ordine; se cade, il pannello va in timeout
QOS = 0
HTTP_TIMEOUT = 60
WS_OPEN_TIMEOUT = 10
# Limite di una risposta inoltrata (il broker accetta messaggi fino a MAX_MESSAGE_MB, default 64 MB)
MAX_BODY = 32 * 1024 * 1024
MAX_WORKERS = 8
HOP_BY_HOP = {
	"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailer",
	"trailers", "transfer-encoding", "upgrade", "content-length", "proxy-connection",
}


def encode(header: dict, body: bytes = b"") -> bytes:
	return json.dumps(header, separators=(",", ":"), ensure_ascii=True).encode() + b"\n" + body


def decode(payload: bytes):
	head, _, body = payload.partition(b"\n")
	header = json.loads(head)
	if not isinstance(header, dict):
		raise ValueError("intestazione non valida")
	return header, body


def _local_port() -> int:
	return int(lb_config.g_config["app_api"]["port"])


def _valid_path(path) -> bool:
	# Solo percorsi locali: la richiesta va sempre a 127.0.0.1, mai ad altri host
	return isinstance(path, str) and path.startswith("/") and not path.startswith("//") and "\r" not in path and "\n" not in path


class RemoteTunnel:
	def __init__(self, client_id: str, get_client: Callable):
		self.client_id = client_id
		self.get_client = get_client
		self.topic_req = f"{client_id}/{TUNNEL_REQ_SUFFIX}"
		self.topic_res = f"{client_id}/{TUNNEL_RES_SUFFIX}"
		self._executor = ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="remote-http")
		self._sockets: Dict[str, object] = {}
		self._lock = threading.Lock()
		self.ssh = RemoteSSH(client_id, self._send)

	@staticmethod
	def enabled() -> bool:
		settings = lb_config.g_config.get("app_api", {}).get("message_broker") or {}
		return settings.get("remote_access", True) is not False

	# ------------------------------------------------------------------
	def _send(self, header: dict, body: bytes = b"") -> bool:
		client = self.get_client()
		if client is None:
			return False
		try:
			info = client.publish(self.topic_res, encode(header, body), qos=QOS, retain=False)
			return info.rc == 0
		except Exception as e:
			lb_log.warning(f"Accesso remoto: invio della risposta fallito: {e}")
			return False

	def handle(self, payload: bytes) -> None:
		"""Messaggio ricevuto su <client_id>/tunnel/req (chiamato dal thread di rete di paho: non deve bloccare)."""
		try:
			header, body = decode(payload)
		except (ValueError, UnicodeDecodeError):
			lb_log.warning("Accesso remoto: messaggio non leggibile")
			return
		sid = str(header.get("id") or "")
		kind = header.get("t")
		if not sid:
			return
		if isinstance(kind, str) and kind.startswith("ssh_"):
			self.ssh.handle(kind, sid, header, body)
			return
		if not self.enabled():
			if kind == "http":
				self._send({"t": "http", "id": sid, "error": "accesso remoto disattivato sull'in-out"})
			elif kind == "ws_open":
				self._send({"t": "ws_open", "id": sid, "ok": False, "error": "accesso remoto disattivato sull'in-out"})
			return
		if kind == "http":
			self._executor.submit(self._http, sid, header, body)
		elif kind == "ws_open":
			threading.Thread(target=self._websocket, args=(sid, header), name=f"remote-ws-{sid[:8]}", daemon=True).start()
		elif kind == "ws_msg":
			with self._lock:
				ws = self._sockets.get(sid)
			if ws is not None:
				try:
					ws.send(body if header.get("bin") else body.decode("utf-8", errors="replace"))
				except Exception:
					self._close_socket(sid)
		elif kind == "ws_close":
			self._close_socket(sid)

	def close_all(self) -> None:
		"""Connessione MQTT persa: i websocket e i terminali aperti non possono più rispondere."""
		self.ssh.close_all()
		with self._lock:
			sockets = list(self._sockets.items())
			self._sockets.clear()
		for _, ws in sockets:
			try:
				ws.close()
			except Exception:
				pass

	def _close_socket(self, sid: str) -> None:
		with self._lock:
			ws = self._sockets.pop(sid, None)
		if ws is not None:
			try:
				ws.close()
			except Exception:
				pass

	# ------------------------------------------------------------------
	# HTTP
	# ------------------------------------------------------------------
	def _http(self, sid: str, header: dict, body: bytes) -> None:
		method = str(header.get("method") or "GET").upper()
		path = header.get("path")
		if not _valid_path(path):
			self._send({"t": "http", "id": sid, "error": "percorso non valido"})
			return
		conn = http.client.HTTPConnection("127.0.0.1", _local_port(), timeout=HTTP_TIMEOUT)
		try:
			conn.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
			has_host = False
			for item in header.get("headers") or []:
				try:
					key, value = str(item[0]), str(item[1])
				except (IndexError, TypeError):
					continue
				if key.lower() in HOP_BY_HOP or "\n" in key + value or "\r" in key + value:
					continue
				has_host = has_host or key.lower() == "host"
				conn.putheader(key, value)
			if not has_host:
				conn.putheader("Host", f"127.0.0.1:{_local_port()}")
			if body or method in ("POST", "PUT", "PATCH"):
				conn.putheader("Content-Length", str(len(body)))
			conn.endheaders(body or None)
			resp = conn.getresponse()
			data = resp.read(MAX_BODY + 1)
			if len(data) > MAX_BODY:
				self._send({"t": "http", "id": sid, "error": "risposta troppo grande per l'accesso remoto"})
				return
			headers = [[k, v] for k, v in resp.getheaders() if k.lower() not in HOP_BY_HOP]
			self._send({"t": "http", "id": sid, "status": resp.status, "headers": headers}, data)
		except Exception as e:
			self._send({"t": "http", "id": sid, "error": f"API locale non raggiungibile: {e}"})
		finally:
			conn.close()

	# ------------------------------------------------------------------
	# Websocket
	# ------------------------------------------------------------------
	def _websocket(self, sid: str, header: dict) -> None:
		path = header.get("path")
		if not _valid_path(path):
			self._send({"t": "ws_open", "id": sid, "ok": False, "error": "percorso non valido"})
			return
		if ws_connect is None:
			self._send({"t": "ws_open", "id": sid, "ok": False, "error": "libreria websockets non disponibile"})
			return
		headers = []
		for item in header.get("headers") or []:
			try:
				key, value = str(item[0]), str(item[1])
			except (IndexError, TypeError):
				continue
			if "\n" in key + value or "\r" in key + value:
				continue
			headers.append((key, value))
		subprotocols = [str(p) for p in header.get("subprotocols") or []] or None
		try:
			ws = ws_connect(
				f"ws://127.0.0.1:{_local_port()}{path}",
				additional_headers=headers,
				subprotocols=subprotocols,
				open_timeout=WS_OPEN_TIMEOUT,
				max_size=MAX_BODY,
				compression=None,
			)
		except Exception as e:
			self._send({"t": "ws_open", "id": sid, "ok": False, "error": str(e)})
			return
		with self._lock:
			self._sockets[sid] = ws
		self._send({"t": "ws_open", "id": sid, "ok": True, "subprotocol": ws.subprotocol})
		code = 1000
		try:
			for message in ws:
				if isinstance(message, bytes):
					self._send({"t": "ws_msg", "id": sid, "bin": True}, message)
				else:
					self._send({"t": "ws_msg", "id": sid, "bin": False}, message.encode("utf-8"))
		except Exception:
			pass
		finally:
			try:
				if ws.close_code:
					code = ws.close_code
			except Exception:
				pass
			with self._lock:
				still_open = self._sockets.pop(sid, None) is not None
			try:
				ws.close()
			except Exception:
				pass
			# Chiuso dall'in-out (o errore): lo si comunica al pannello
			if still_open:
				self._send({"t": "ws_close", "id": sid, "code": code})
