"""
Modulo md_message_broker
========================

Invia ogni pesata (dati + foto + report PDF/CSV) a un broker MQTT.

Funzionamento:
- `enqueue_weighing(...)` crea un messaggio JSON (allegati in base64) e lo salva
  come file nella cartella "outbox" su disco, in modo che sopravviva a riavvii
  e cadute di rete.
- Un thread dedicato legge i file dell'outbox in ordine di creazione (FIFO) e li
  pubblica sul broker. Un messaggio viene eliminato dall'outbox solo dopo la
  conferma di consegna del broker (PUBACK, QoS 1 fisso).
- Se l'invio di un messaggio fallisce, il thread riprova LO STESSO messaggio
  (con attesa crescente) e non passa ai successivi finché non è stato inviato:
  l'ordine delle pesate è sempre rispettato.
- I file illeggibili/corrotti vengono spostati nella sottocartella "failed"
  per non bloccare la coda all'infinito.
- Il certificato client si ottiene da solo (vedi `enrollment.py`): basta impostare
  l'host del broker. L'in-out genera la sua chiave, si registra sul servizio di
  registrazione del broker (porta 8884) e rinnova il certificato prima della scadenza.
- Accesso remoto (vedi `remote_tunnel.py`): sulla stessa connessione il pannello del
  broker inoltra richieste HTTP e websocket all'API locale dell'in-out, e apre un
  terminale SSH verso il sshd locale (vedi `remote_ssh.py`).
"""

import base64
import getpass
import json
import os
import shutil
import socket
import threading
import time
import uuid
from datetime import datetime
from typing import List, Optional, Tuple, Union

import paho.mqtt.client as mqtt

import libs.lb_config as lb_config
import libs.lb_log as lb_log
from libs.lb_utils import base_path, createThread, startThread
from modules.md_message_broker.dto import MessageBrokerDTO
from modules.md_message_broker import enrollment
from modules.md_message_broker.remote_tunnel import RemoteTunnel
from modules.md_message_broker import remote_ssh

name_module = "md_message_broker"

DEFAULT_OUTBOX_DIR = "/var/opt/in-out/message_broker_outbox"
DEFAULT_CERT_DIR = "/var/opt/in-out/message_broker_certs"
# Nomi dei file TLS salvati nella cartella dei certificati
CERT_FILES = {
	"ca": "ca.crt",
	"cert": "client.crt",
	"key": "client.key",
}
# Host del broker a cui appartengono i certificati: se cambia host si riparte da zero
OWNER_FILE = "broker_host"
# Ultima richiesta di nuovo certificato ricevuta dal broker ed eseguita
CONTROL_REQUEST_FILE = "control_request"
# Topic dei comandi dal broker: <client_id>/control
CONTROL_SUFFIX = "control"
FAILED_SUB_DIR = "failed"
CONNECT_TIMEOUT = 10
BACKOFF_MIN = 1
BACKOFF_MAX = 60
# QoS 1: il broker conferma ogni pesata (PUBACK), necessario per la coda con riprova
QOS = 1
# Registrazione: nuovo tentativo dopo un errore (senza certificato / rinnovo fallito)
ENROLL_RETRY = 30
RENEW_RETRY = 3600
# Ogni quanto si controlla la scadenza del certificato
CERT_CHECK_INTERVAL = 3600

module_message_broker = None


def init():
	global module_message_broker
	lb_log.info("init")
	module_message_broker = ModuleMessageBroker()
	thread = createThread(module_message_broker.run)
	startThread(thread=thread)
	lb_log.info("end")


def start():
	lb_log.info("start")
	lb_log.info("end")


def stop():
	if module_message_broker:
		module_message_broker.stop()


def get_settings() -> dict:
	"""Ritorna (creandola se mancante) la sezione di configurazione del modulo."""
	app_api = lb_config.g_config.setdefault("app_api", {})
	settings = app_api.get("message_broker")
	if not isinstance(settings, dict):
		settings = {}
		app_api["message_broker"] = settings
	settings.setdefault("outbox_dir", DEFAULT_OUTBOX_DIR)
	settings.setdefault("cert_dir", DEFAULT_CERT_DIR)
	settings.setdefault("broker", None)
	# Client ID generato una sola volta e mantenuto anche se il broker viene eliminato
	if not settings.get("client_id"):
		hostname = "".join(c for c in socket.gethostname().lower() if c.isalnum() or c == "-") or "host"
		settings["client_id"] = f"in-out-{hostname}-{uuid.uuid4().hex[:8]}"
		try:
			lb_config.saveconfig()
		except Exception:
			pass
	return settings


def enqueue_weighing(
	instance_name: str,
	weigher_name: str,
	event_type: str,
	weighing: dict,
	images: Optional[List[Tuple[str, bytes]]] = None,
	pdf: Optional[Tuple[str, bytes]] = None,
	csv: Optional[Tuple[str, Union[str, bytes]]] = None,
	ids: Optional[dict] = None,
) -> Optional[str]:
	"""Accoda una pesata da inviare al broker. Ritorna il message_id o None se il broker non è configurato."""
	if module_message_broker is None:
		return None
	return module_message_broker.enqueue_weighing(
		instance_name=instance_name,
		weigher_name=weigher_name,
		event_type=event_type,
		weighing=weighing,
		images=images,
		pdf=pdf,
		csv=csv,
		ids=ids,
	)


def _b64(content: Union[str, bytes]) -> str:
	if isinstance(content, str):
		content = content.encode("utf-8")
	return base64.b64encode(content).decode("ascii")


class ModuleMessageBroker:
	def __init__(self):
		settings = get_settings()
		self.config: Optional[MessageBrokerDTO] = None
		if settings.get("broker"):
			try:
				self.config = MessageBrokerDTO(**settings["broker"])
				if not self.config.remote_ssh:
					remote_ssh.remove_key(self.config.ssh_user)
			except Exception as e:
				lb_log.error(f"Configurazione message broker non valida: {e}")
		self.outbox_dir = self._resolve_dir(settings.get("outbox_dir") or DEFAULT_OUTBOX_DIR)
		self.cert_dir = self._resolve_dir(settings.get("cert_dir") or DEFAULT_CERT_DIR)
		self.client_id: str = settings["client_id"]

		self._lock = threading.RLock()  # protegge config/client
		self._write_lock = threading.Lock()  # protegge la generazione dei nomi file
		self._wake = threading.Event()
		self._stop = threading.Event()
		self._connected = threading.Event()

		self.client: Optional[mqtt.Client] = None
		self.last_error: Optional[str] = None
		self.last_sent_at: Optional[str] = None
		self.last_sent_id: Optional[str] = None
		self._backoff = BACKOFF_MIN

		self._enroll_lock = threading.Lock()
		self._next_cert_check = 0.0
		self._next_enroll_attempt = 0.0
		self._renewed = threading.Event()
		self._next_status_check = 0.0
		# Nuovo certificato richiesto dal broker (request_id del comando), None se nessuna richiesta
		self._renew_request: Optional[str] = None
		self._next_idle_connect = 0.0
		# Problema del certificato rilevato dalla CRL (es. canale chiuso), più chiaro dell'errore TLS
		self.certificate_problem: Optional[str] = None
		# File dei certificati non accessibili all'utente che esegue l'in-out
		self.access_problem: Optional[str] = None
		self.enroll_error: Optional[str] = None
		self.last_enrolled_at: Optional[str] = None
		# Accesso remoto dal pannello del broker: HTTP e websocket attraverso MQTT
		self.remote = RemoteTunnel(self.client_id, lambda: self.client)

		os.makedirs(self.outbox_dir, exist_ok=True)

	# ------------------------------------------------------------------
	# Configurazione
	# ------------------------------------------------------------------
	@staticmethod
	def _resolve_dir(path: str) -> str:
		if not path.startswith("/") and not (len(path) > 1 and path[1] == ":"):
			path = os.path.join(base_path, path)
		return path

	def cert_path(self, kind: str) -> str:
		return os.path.join(self.cert_dir, CERT_FILES[kind])

	def has_ca(self) -> bool:
		return os.path.isfile(self.cert_path("ca"))

	def has_client_certificate(self) -> bool:
		return os.path.isfile(self.cert_path("cert")) and os.path.isfile(self.cert_path("key"))

	def _owner_path(self) -> str:
		return os.path.join(self.cert_dir, OWNER_FILE)

	def _certificates_owner(self) -> Optional[str]:
		try:
			with open(self._owner_path(), "r", encoding="utf-8") as f:
				return f.read().strip() or None
		except OSError:
			return None

	def _clear_certificates(self) -> None:
		"""Elimina CA e certificato. La chiave resta: se il "nuovo" host è lo stesso broker
		(es. da IP a nome DNS) la riconosce e rilascia subito un nuovo certificato."""
		for path in (self.cert_path("ca"), self.cert_path("cert"), self._owner_path()):
			try:
				os.remove(path)
			except FileNotFoundError:
				pass

	def _replace_certificate(self, config: MessageBrokerDTO) -> bool:
		"""Nuovo certificato richiesto dal pannello del broker: nuova chiave e nuovo certificato."""
		now = time.monotonic()
		with self._enroll_lock:
			request_id = self._renew_request
			if not request_id or now < self._next_enroll_attempt:
				return True
			try:
				lb_log.info("Nuovo certificato richiesto dal broker: generazione di una nuova chiave")
				cert = enrollment.enroll(
					config.host, config.enroll_port, self.client_id,
					self.cert_path("ca"), self.cert_path("cert"), self.cert_path("key"),
					hostname=socket.gethostname(), rotate_key=True,
				)
			except enrollment.EnrollmentError as e:
				self.enroll_error = f"Sostituzione del certificato fallita: {e}"
				self._next_enroll_attempt = now + ENROLL_RETRY
				lb_log.error(self.enroll_error)
				return True
			try:
				with open(os.path.join(self.cert_dir, CONTROL_REQUEST_FILE), "w", encoding="utf-8") as f:
					f.write(request_id)
			except OSError:
				pass
			self._renew_request = None
			self.enroll_error = None
			self._next_enroll_attempt = 0.0
			self._next_cert_check = now + CERT_CHECK_INTERVAL
			self.last_enrolled_at = datetime.now().isoformat()
			lb_log.info(f"Nuovo certificato installato, scade il {cert.not_valid_after_utc.date()}: riconnessione")
			self._renewed.set()
			return True

	def _last_control_request(self) -> Optional[str]:
		try:
			with open(os.path.join(self.cert_dir, CONTROL_REQUEST_FILE), "r", encoding="utf-8") as f:
				return f.read().strip() or None
		except OSError:
			return None

	def _on_message(self, client, userdata, msg):
		"""Comandi dal broker sul topic <client_id>/control (messaggio retained) e accesso remoto."""
		if msg.topic == self.remote.topic_req:
			self.remote.handle(msg.payload)
			return
		if msg.topic != f"{self.client_id}/{CONTROL_SUFFIX}" or not msg.payload:
			return
		try:
			command = json.loads(msg.payload)
		except ValueError:
			lb_log.warning("Comando dal broker non leggibile")
			return
		if not isinstance(command, dict) or command.get("command") != "renew_certificate":
			return
		request_id = str(command.get("request_id") or "")
		if not request_id or request_id in (self._renew_request, self._last_control_request()):
			return
		lb_log.info("Il broker ha richiesto un nuovo certificato")
		self._renew_request = request_id
		self._next_enroll_attempt = 0.0
		self._wake.set()

	def _check_certificate_after_failure(self, config: MessageBrokerDTO) -> None:
		"""
		Connessione MQTT fallita: controlla sulla CRL del broker se il certificato è stato
		revocato (es. dispositivo eliminato dal pannello) e in quel caso lo elimina, così
		al giro successivo l'in-out si registra di nuovo. Se è sospeso (canale chiuso)
		lo segnala e aspetta. Al massimo un controllo ogni ENROLL_RETRY secondi.
		"""
		now = time.monotonic()
		if now < self._next_status_check or not (self.has_ca() and self.has_client_certificate()):
			return
		self._next_status_check = now + ENROLL_RETRY
		try:
			status = enrollment.certificate_status(config.host, config.enroll_port, self.cert_path("ca"), self.cert_path("cert"))
		except enrollment.EnrollmentError as e:
			lb_log.warning(f"Impossibile verificare lo stato del certificato: {e}")
			return
		if status == enrollment.STATUS_REVOKED:
			with self._enroll_lock:
				try:
					os.remove(self.cert_path("cert"))
				except FileNotFoundError:
					pass
				self._next_enroll_attempt = 0.0
				self._next_cert_check = 0.0
			self.certificate_problem = "Certificato revocato dal broker: nuova registrazione in corso"
			lb_log.warning(self.certificate_problem)
		elif status == enrollment.STATUS_HOLD:
			self.certificate_problem = "Canale chiuso sul broker: le pesate restano in coda finché non viene riaperto"
			lb_log.warning(self.certificate_problem)
		else:
			self.certificate_problem = None

	def _check_files_access(self) -> bool:
		"""
		Verifica che chiave, certificati e cartella siano accessibili all'utente corrente.
		Succede se l'in-out è stato avviato una volta con un altro utente (es. sudo): in quel
		caso non si tocca nulla (una nuova chiave non sarebbe riconosciuta dal broker) e si
		segnala come correggere i permessi.
		"""
		files = [self.cert_path(kind) for kind in CERT_FILES] + [self._owner_path()]
		bad = [path for path in files if os.path.exists(path) and not os.access(path, os.R_OK)]
		if os.path.isdir(self.cert_dir) and not os.access(self.cert_dir, os.W_OK | os.X_OK):
			bad.append(self.cert_dir)
		if not bad:
			self.access_problem = None
			return True
		try:
			user = getpass.getuser()
		except Exception:
			user = "corrente"
		problem = (
			f"File dei certificati non accessibili all'utente '{user}' ({', '.join(bad)}): "
			f"probabilmente l'in-out è stato avviato con un altro utente (es. sudo). "
			f"Correggi con: sudo chown -R {user} {self.cert_dir}"
		)
		if problem != self.access_problem:
			lb_log.error(problem)
		self.access_problem = problem
		return False

	def _ensure_certificate(self, config: MessageBrokerDTO, force: bool = False) -> bool:
		"""
		Garantisce un certificato client valido, registrandosi sul broker se manca o
		rinnovandolo se sta per scadere. Ritorna True se c'è un certificato utilizzabile.
		I tentativi falliti vengono ripetuti dopo ENROLL_RETRY / RENEW_RETRY secondi.
		"""
		if not self._check_files_access():
			return False
		now = time.monotonic()
		has = self.has_ca() and self.has_client_certificate()
		if has and self._renew_request:
			return self._replace_certificate(config)
		if has and not force and now < self._next_cert_check:
			return True
		with self._enroll_lock:
			has = self.has_ca() and self.has_client_certificate()
			if has and not enrollment.needs_renewal(self.cert_path("cert")):
				self._next_cert_check = now + CERT_CHECK_INTERVAL
				self.enroll_error = None
				return True
			if not force and now < self._next_enroll_attempt:
				return has
			action = "Rinnovo" if has else "Registrazione"
			try:
				lb_log.info(f"{action} del certificato sul broker {config.host}:{config.enroll_port}")
				cert = enrollment.enroll(
					config.host, config.enroll_port, self.client_id,
					self.cert_path("ca"), self.cert_path("cert"), self.cert_path("key"),
					hostname=socket.gethostname(),
				)
				with open(self._owner_path(), "w", encoding="utf-8") as f:
					f.write(config.host)
			except enrollment.EnrollmentError as e:
				self.enroll_error = f"{action} del certificato fallita: {e}"
				self._next_enroll_attempt = now + (RENEW_RETRY if has else ENROLL_RETRY)
				lb_log.error(self.enroll_error)
				if not has:
					self.last_error = self.enroll_error
				return has
			self.enroll_error = None
			self._next_enroll_attempt = 0.0
			self._next_cert_check = now + CERT_CHECK_INTERVAL
			self.last_enrolled_at = datetime.now().isoformat()
			lb_log.info(f"Certificato client ottenuto dal broker, scade il {cert.not_valid_after_utc.date()}")
			if has:
				# Nuovo certificato: la prossima connessione lo userà
				self._renewed.set()
			return True

	def get_certificates_info(self) -> dict:
		"""Ritorna per ogni file TLS se è presente e, per i certificati, soggetto e scadenza."""
		info = {}
		for kind in CERT_FILES:
			path = self.cert_path(kind)
			item = {"present": os.path.isfile(path)}
			if item["present"] and kind != "key":
				try:
					from cryptography import x509
					with open(path, "rb") as f:
						cert = x509.load_pem_x509_certificate(f.read())
					item["subject"] = cert.subject.rfc4514_string()
					item["expires_at"] = cert.not_valid_after_utc.isoformat()
				except Exception:
					pass
			info[kind] = item
		return info

	def set_config(self, config: Optional[MessageBrokerDTO]) -> bool:
		"""Imposta (o rimuove con None) la configurazione del broker e prova a connettersi."""
		with self._lock:
			self._disconnect()
			# Terminale remoto disattivato o utente cambiato: la chiave del broker non deve restare
			old_ssh_user = self.config.ssh_user if self.config and self.config.remote_ssh else None
			new_ssh_user = config.ssh_user if config and config.remote_ssh else None
			if old_ssh_user and old_ssh_user != new_ssh_user:
				remote_ssh.remove_key(old_ssh_user)
			# Configurazione eliminata: via anche CA e certificato, così reimpostandola
			# (anche con lo stesso host, es. broker reinstallato) si scarica la nuova CA
			if config is None:
				if self.has_ca() or self.has_client_certificate():
					lb_log.info("Configurazione del broker eliminata: CA e certificato eliminati")
				self._clear_certificates()
			# Certificati di un altro broker: si eliminano e ci si registra sul nuovo
			else:
				owner = self._certificates_owner() or (self.config.host if self.config else None)
				if owner and owner != config.host:
					lb_log.info(f"Host del broker cambiato ({owner} -> {config.host}): certificati eliminati")
					self._clear_certificates()
			self.config = config
			self.last_error = None
			self.enroll_error = None
			self.certificate_problem = None
			self._backoff = BACKOFF_MIN
			self._next_cert_check = 0.0
			self._next_enroll_attempt = 0.0
			self._next_idle_connect = 0.0
			self._next_status_check = 0.0
		connected = self._ensure_connected() if config else False
		self._wake.set()
		return connected

	def stop(self):
		self._stop.set()
		self._wake.set()
		with self._lock:
			self._disconnect()

	# ------------------------------------------------------------------
	# Outbox (coda persistente su disco)
	# ------------------------------------------------------------------
	def enqueue_weighing(self, instance_name, weigher_name, event_type, weighing, images=None, pdf=None, csv=None, ids=None) -> Optional[str]:
		config = self.config
		if config is None:
			return None

		files = []
		if config.include_images:
			for name, content in images or []:
				if content:
					files.append({"type": "image", "name": name, "content_type": "image/png", "data": _b64(content)})
		if config.include_pdf and pdf and pdf[1]:
			files.append({"type": "pdf", "name": pdf[0], "content_type": "application/pdf", "data": _b64(pdf[1])})
		if config.include_csv and csv and csv[1]:
			files.append({"type": "csv", "name": csv[0], "content_type": "text/csv", "data": _b64(csv[1])})

		message = {
			"message_id": str(uuid.uuid4()),
			"created_at": datetime.now().isoformat(),
			"instance_name": instance_name,
			"weigher_name": weigher_name,
			"event_type": event_type,
			**(ids or {}),
			"weighing": weighing,
			"files": files,
		}
		return self.enqueue(message)

	def enqueue(self, message: dict) -> str:
		"""Salva il messaggio nell'outbox in modo atomico. Ritorna il message_id."""
		message.setdefault("message_id", str(uuid.uuid4()))
		os.makedirs(self.outbox_dir, exist_ok=True)
		with self._write_lock:
			# Il nome inizia con un timestamp in nanosecondi: l'ordinamento alfabetico = ordine di arrivo
			name = f"{time.time_ns():020d}_{message['message_id']}.json"
			final_path = os.path.join(self.outbox_dir, name)
			tmp_path = final_path + ".tmp"
			with open(tmp_path, "w", encoding="utf-8") as f:
				json.dump(message, f, default=str)
				f.flush()
				os.fsync(f.fileno())
			os.replace(tmp_path, final_path)
		lb_log.info(f"Pesata accodata per il broker: {name}")
		self._wake.set()
		return message["message_id"]

	def list_pending(self) -> List[str]:
		try:
			names = [n for n in os.listdir(self.outbox_dir) if n.endswith(".json")]
		except FileNotFoundError:
			return []
		names.sort()
		return [os.path.join(self.outbox_dir, n) for n in names]

	def list_failed(self) -> List[str]:
		failed_dir = os.path.join(self.outbox_dir, FAILED_SUB_DIR)
		try:
			return sorted(os.path.join(failed_dir, n) for n in os.listdir(failed_dir) if n.endswith(".json"))
		except FileNotFoundError:
			return []

	def retry_failed(self) -> int:
		"""Rimette in coda i messaggi spostati in "failed"."""
		count = 0
		for path in self.list_failed():
			try:
				shutil.move(path, os.path.join(self.outbox_dir, os.path.basename(path)))
				count += 1
			except Exception as e:
				lb_log.error(f"Impossibile rimettere in coda {path}: {e}")
		self._wake.set()
		return count

	def _move_to_failed(self, path: str, reason: str):
		failed_dir = os.path.join(self.outbox_dir, FAILED_SUB_DIR)
		os.makedirs(failed_dir, exist_ok=True)
		try:
			shutil.move(path, os.path.join(failed_dir, os.path.basename(path)))
			lb_log.error(f"Messaggio {os.path.basename(path)} spostato in '{FAILED_SUB_DIR}': {reason}")
		except Exception as e:
			lb_log.error(f"Impossibile spostare {path} in '{FAILED_SUB_DIR}': {e}")

	# ------------------------------------------------------------------
	# MQTT
	# ------------------------------------------------------------------
	def _on_connect(self, client, userdata, flags, reason_code, properties):
		if reason_code.is_failure:
			self.last_error = f"Connessione rifiutata dal broker: {reason_code}"
			lb_log.error(self.last_error)
			self._connected.clear()
		else:
			lb_log.info("Connesso al message broker")
			self._connected.set()
			# Comandi dal broker (es. nuovo certificato richiesto dal pannello)
			client.subscribe(f"{self.client_id}/{CONTROL_SUFFIX}", qos=QOS)
			# Accesso remoto dal pannello del broker (richieste HTTP e websocket)
			client.subscribe(self.remote.topic_req, qos=0)

	def _on_disconnect(self, client, userdata, flags, reason_code, properties):
		self._connected.clear()
		self.remote.close_all()
		if reason_code.is_failure:
			self.last_error = f"Disconnesso dal broker: {reason_code}"
			lb_log.warning(self.last_error)

	def _create_client(self, config: MessageBrokerDTO) -> mqtt.Client:
		client = mqtt.Client(
			callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
			client_id=self.client_id,
			clean_session=True,
		)
		# Connessione sempre in TLS con il certificato ottenuto dalla registrazione
		if not (self.has_ca() and self.has_client_certificate()):
			raise RuntimeError("Certificato client non ancora ottenuto dal broker")
		client.tls_set(
			ca_certs=self.cert_path("ca"),
			certfile=self.cert_path("cert"),
			keyfile=self.cert_path("key"),
		)
		client.on_connect = self._on_connect
		client.on_message = self._on_message
		client.on_disconnect = self._on_disconnect
		return client

	def _ensure_connected(self) -> bool:
		config = self.config
		if config is None:
			return False
		if not self._ensure_certificate(config):
			return False
		if self._renewed.is_set():
			self._renewed.clear()
			self._disconnect()
		with self._lock:
			config = self.config
			if config is None:
				return False
			if self.client is not None and self._connected.is_set():
				return True
			# Client assente o connessione persa: si ricrea da zero
			self._disconnect()
			try:
				self._connected.clear()
				client = self._create_client(config)
				client.connect(config.host, config.port, keepalive=config.keepalive)
				client.loop_start()
				self.client = client
			except Exception as e:
				self.last_error = f"Impossibile connettersi a {config.host}:{config.port}: {e}"
				lb_log.error(self.last_error)
				self._disconnect()
				failed = True
			else:
				failed = False
		if failed:
			self._check_certificate_after_failure(config)
			return False
		if not self._connected.wait(CONNECT_TIMEOUT):
			if not self.last_error:
				self.last_error = "Timeout in attesa della conferma di connessione (CONNACK)"
			with self._lock:
				self._disconnect()
			self._check_certificate_after_failure(config)
			return False
		self._next_status_check = 0.0
		self.certificate_problem = None
		return True

	def _disconnect(self):
		with self._lock:
			client = self.client
			self.client = None
			self._connected.clear()
		self.remote.close_all()
		if client is not None:
			try:
				client.disconnect()
			except Exception:
				pass
			try:
				client.loop_stop()
			except Exception:
				pass

	def _publish(self, message: dict, raw: str) -> bool:
		with self._lock:
			config = self.config
			client = self.client
		if config is None or client is None:
			return False
		# Il topic coincide con il client ID dell'impianto
		topic = self.client_id
		try:
			info = client.publish(topic, raw, qos=QOS, retain=False)
			if info.rc != mqtt.MQTT_ERR_SUCCESS:
				self.last_error = f"Publish fallito: {mqtt.error_string(info.rc)}"
				return False
			info.wait_for_publish(timeout=config.publish_timeout)
			if not info.is_published():
				self.last_error = "Timeout in attesa della conferma di consegna dal broker"
				return False
			return True
		except Exception as e:
			self.last_error = f"Errore durante il publish: {e}"
			return False

	# ------------------------------------------------------------------
	# Stato
	# ------------------------------------------------------------------
	def get_status(self) -> dict:
		return {
			"configured": self.config is not None,
			"client_id": self.client_id,
			"topic": self.client_id,
			"connected": self.client is not None and self._connected.is_set(),
			"pending": len(self.list_pending()),
			"failed": len(self.list_failed()),
			"outbox_dir": self.outbox_dir,
			"last_error": self.access_problem or self.certificate_problem or self.last_error,
			"last_sent_at": self.last_sent_at,
			"last_sent_id": self.last_sent_id,
			"enroll_error": self.enroll_error,
			"last_enrolled_at": self.last_enrolled_at,
		}

	# ------------------------------------------------------------------
	# Loop di invio
	# ------------------------------------------------------------------
	def _wait_backoff(self):
		self._wake.clear()
		self._stop.wait(self._backoff)
		self._backoff = min(self._backoff * 2, BACKOFF_MAX)

	def run(self):
		while lb_config.g_enabled and not self._stop.is_set():
			try:
				if self.config is None:
					self._wake.wait(1)
					self._wake.clear()
					continue

				pending = self.list_pending()
				if not pending:
					# Anche senza pesate da inviare la connessione resta aperta: registrazione al
					# primo avvio, rinnovo del certificato e comandi dal broker arrivano subito
					config = self.config
					if config is not None:
						self._ensure_certificate(config)
						needs_connect = self._renewed.is_set() or not self._connected.is_set()
						if needs_connect and time.monotonic() >= self._next_idle_connect:
							if self._ensure_connected():
								self._backoff = BACKOFF_MIN
							else:
								self._next_idle_connect = time.monotonic() + self._backoff
								self._backoff = min(self._backoff * 2, BACKOFF_MAX)
					self._wake.wait(1)
					self._wake.clear()
					continue

				# Sempre il messaggio più vecchio: finché non parte non si passa al successivo
				path = pending[0]
				try:
					with open(path, "r", encoding="utf-8") as f:
						raw = f.read()
					message = json.loads(raw)
					if not isinstance(message, dict):
						raise ValueError("il contenuto non è un oggetto JSON")
				except FileNotFoundError:
					continue
				except Exception as e:
					self._move_to_failed(path, f"file non leggibile: {e}")
					continue

				if not self._ensure_connected():
					lb_log.warning(f"Broker non raggiungibile, {len(pending)} pesate in attesa. Nuovo tentativo tra {self._backoff}s")
					self._wait_backoff()
					continue

				if self._publish(message, raw):
					try:
						os.remove(path)
					except FileNotFoundError:
						pass
					self.last_sent_at = datetime.now().isoformat()
					self.last_sent_id = message.get("message_id")
					self.last_error = None
					self._backoff = BACKOFF_MIN
					lb_log.info(f"Pesata inviata al broker: {os.path.basename(path)}")
				else:
					lb_log.warning(f"Invio di {os.path.basename(path)} fallito ({self.last_error}). Nuovo tentativo tra {self._backoff}s")
					# Si scarta la connessione per evitare che paho ritrasmetta in parallelo
					self._disconnect()
					self._wait_backoff()
			except Exception as e:
				self.last_error = str(e)
				lb_log.error(f"Errore nel loop del message broker: {e}")
				self._wait_backoff()
