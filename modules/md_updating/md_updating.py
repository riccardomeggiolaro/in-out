# ==== LIBRERIE DA IMPORTARE ===================================
import threading
import requests
import os
import io
import json
import zipfile
from datetime import datetime
from sqlalchemy.orm import joinedload
import libs.lb_log as lb_log
import libs.lb_config as lb_config
# ==============================================================

name_module = "md_updating"

CALL_INTERVAL_SECONDS = 5 * 60  # 5 minuti
MAX_WEIGHINGS_PER_CALL = 500  # le pesate eccedenti vengono inviate al giro successivo
STATE_FILE_NAME = "md_updating_state.json"

def init():
	global module_updating
	lb_log.info("init")
	module_updating = ModuleUpdating()
	lb_log.info("end")

def start():
	lb_log.info("start")
	while lb_config.g_enabled:
		threading.Event().wait(1)
	lb_log.info("end")

def stop():
	module_updating.stop()

# Funzione richiamabile da app_api per impostare/aggiornare il dominio letto da config.json
# e (ri)avviare il thread dedicato che lo richiama periodicamente.
def set_domain(domain: str):
	module_updating.set_domain(domain)

class ModuleUpdating:
	def __init__(self):
		self.domain = None
		self.thread = None
		self._stop_event = threading.Event()

	def set_domain(self, domain: str):
		self.domain = domain
		self._restart_thread()

	def _restart_thread(self):
		self.stop()
		self._stop_event = threading.Event()
		self.thread = threading.Thread(target=self._loop, daemon=True, name="md_updating")
		self.thread.start()

	def _loop(self):
		while lb_config.g_enabled and not self._stop_event.is_set():
			self._call_domain()
			self._stop_event.wait(CALL_INTERVAL_SECONDS)

	def _call_domain(self):
		if not self.domain:
			return
		try:
			weighings = self._get_unsent_weighings()
			files = None
			if weighings:
				files = {"file": ("weighings.zip", self._build_zip(weighings), "application/zip")}
			response = requests.post(self.domain, files=files, timeout=30)
			lb_log.info(f"[md_updating] chiamata a {self.domain} con {len(weighings)} pesate -> status {response.status_code}")
			if weighings and response.ok:
				self._save_last_sent_id(weighings[-1]["id"])
		except Exception as e:
			lb_log.error(f"[md_updating] errore chiamando {self.domain}: {e}")

	# ==== PESATE NON ANCORA INVIATE ==============================

	def _state_file_path(self):
		path_database = lb_config.g_config["app_api"]["path_database"]
		return os.path.join(os.path.dirname(os.path.abspath(path_database)), STATE_FILE_NAME)

	def _load_last_sent_id(self):
		try:
			with open(self._state_file_path(), "r") as f:
				return int(json.load(f).get("last_sent_weighing_id", 0))
		except Exception:
			return 0

	def _save_last_sent_id(self, last_id):
		with open(self._state_file_path(), "w") as f:
			json.dump({"last_sent_weighing_id": last_id, "updated_at": datetime.now().isoformat()}, f)

	def _get_unsent_weighings(self):
		from modules.md_database.md_database import SessionLocal, Weighing, InOut, Access

		last_id = self._load_last_sent_id()
		session = SessionLocal()
		try:
			weighings = (
				session.query(Weighing)
				.options(joinedload(Weighing.operator))
				.filter(Weighing.id > last_id)
				.order_by(Weighing.id.asc())
				.limit(MAX_WEIGHINGS_PER_CALL)
				.all()
			)
			result = []
			for w in weighings:
				in_out = (
					session.query(InOut)
					.options(
						joinedload(InOut.access).joinedload(Access.vehicle),
						joinedload(InOut.subject),
						joinedload(InOut.vector),
						joinedload(InOut.driver),
						joinedload(InOut.material),
						joinedload(InOut.weight1),
						joinedload(InOut.weight2),
					)
					.filter((InOut.idWeight1 == w.id) | (InOut.idWeight2 == w.id))
					.first()
				)
				result.append(self._serialize_weighing(w, in_out))
			return result
		finally:
			session.close()

	def _serialize_weighing(self, w, in_out):
		data = {
			"id": w.id,
			"date": w.date.isoformat() if w.date else None,
			"weigher": w.weigher,
			"weigher_serial_number": w.weigher_serial_number,
			"pid": w.pid,
			"weight": w.weight,
			"tare": w.tare,
			"is_preset_tare": w.is_preset_tare,
			"is_preset_weight": w.is_preset_weight,
			"operator": w.operator.description if w.operator else None,
			"in_out": None,
		}
		if in_out:
			access = in_out.access
			data["in_out"] = {
				"id": in_out.id,
				"idAccess": in_out.idAccess,
				"type_subject": in_out.typeSubject.value if in_out.typeSubject else None,
				"subject": in_out.subject.social_reason if in_out.subject else None,
				"vector": in_out.vector.social_reason if in_out.vector else None,
				"driver": in_out.driver.social_reason if in_out.driver else None,
				"plate": access.vehicle.plate if access and access.vehicle else None,
				"material": in_out.material.description if in_out.material else None,
				"weight1_pid": in_out.weight1.pid if in_out.weight1 else None,
				"weight1": in_out.weight1.weight if in_out.weight1 else None,
				"weight2_pid": in_out.weight2.pid if in_out.weight2 else None,
				"weight2": in_out.weight2.weight if in_out.weight2 else None,
				"net_weight": in_out.net_weight,
				"note": in_out.note,
				"document_reference": in_out.document_reference,
			}
		return data

	def _build_zip(self, weighings):
		buffer = io.BytesIO()
		with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
			zf.writestr("weighings.json", json.dumps(weighings, ensure_ascii=False, indent=2))
		buffer.seek(0)
		return buffer

	def stop(self):
		self._stop_event.set()
		if self.thread and self.thread.is_alive():
			self.thread.join(timeout=1)
