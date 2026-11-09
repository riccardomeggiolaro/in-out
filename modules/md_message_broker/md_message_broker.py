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
  conferma di consegna del broker (PUBACK/PUBCOMP con QoS 1/2).
- Se l'invio di un messaggio fallisce, il thread riprova LO STESSO messaggio
  (con attesa crescente) e non passa ai successivi finché non è stato inviato:
  l'ordine delle pesate è sempre rispettato.
- I file illeggibili/corrotti vengono spostati nella sottocartella "failed"
  per non bloccare la coda all'infinito.
"""

import base64
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

name_module = "md_message_broker"

DEFAULT_OUTBOX_DIR = "/var/opt/in-out/message_broker_outbox"
FAILED_SUB_DIR = "failed"
CONNECT_TIMEOUT = 10
BACKOFF_MIN = 1
BACKOFF_MAX = 60

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
	settings.setdefault("broker", None)
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
			except Exception as e:
				lb_log.error(f"Configurazione message broker non valida: {e}")
		self.outbox_dir = self._resolve_dir(settings.get("outbox_dir") or DEFAULT_OUTBOX_DIR)

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

		os.makedirs(self.outbox_dir, exist_ok=True)

	# ------------------------------------------------------------------
	# Configurazione
	# ------------------------------------------------------------------
	@staticmethod
	def _resolve_dir(path: str) -> str:
		if not path.startswith("/") and not (len(path) > 1 and path[1] == ":"):
			path = os.path.join(base_path, path)
		return path

	def set_config(self, config: Optional[MessageBrokerDTO]) -> bool:
		"""Imposta (o rimuove con None) la configurazione del broker e prova a connettersi."""
		with self._lock:
			self._disconnect()
			self.config = config
			self.last_error = None
			self._backoff = BACKOFF_MIN
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

	def _on_disconnect(self, client, userdata, flags, reason_code, properties):
		self._connected.clear()
		if reason_code.is_failure:
			self.last_error = f"Disconnesso dal broker: {reason_code}"
			lb_log.warning(self.last_error)

	def _create_client(self, config: MessageBrokerDTO) -> mqtt.Client:
		client_id = config.client_id or f"in-out-{socket.gethostname()}"
		client = mqtt.Client(
			callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
			client_id=client_id,
			clean_session=True,
		)
		if config.username:
			client.username_pw_set(config.username, config.password)
		if config.tls:
			client.tls_set(ca_certs=config.ca_cert or None)
			if config.tls_insecure:
				client.tls_insecure_set(True)
		client.on_connect = self._on_connect
		client.on_disconnect = self._on_disconnect
		return client

	def _ensure_connected(self) -> bool:
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
				return False
		if not self._connected.wait(CONNECT_TIMEOUT):
			if not self.last_error:
				self.last_error = "Timeout in attesa della conferma di connessione (CONNACK)"
			with self._lock:
				self._disconnect()
			return False
		return True

	def _disconnect(self):
		with self._lock:
			client = self.client
			self.client = None
			self._connected.clear()
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
		topic = config.topic
		try:
			topic = topic.format(
				instance_name=message.get("instance_name") or "",
				weigher_name=message.get("weigher_name") or "",
				event_type=message.get("event_type") or "",
			)
		except (KeyError, IndexError, ValueError):
			pass
		try:
			info = client.publish(topic, raw, qos=config.qos, retain=config.retain)
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
			"connected": self.client is not None and self._connected.is_set(),
			"pending": len(self.list_pending()),
			"failed": len(self.list_failed()),
			"outbox_dir": self.outbox_dir,
			"last_error": self.last_error,
			"last_sent_at": self.last_sent_at,
			"last_sent_id": self.last_sent_id,
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
