# ==== LIBRERIE DA IMPORTARE ===================================
import threading
import requests
import libs.lb_log as lb_log
import libs.lb_config as lb_config
# ==============================================================

name_module = "md_updating"

CALL_INTERVAL_SECONDS = 5 * 60  # 5 minuti

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
			response = requests.get(self.domain, timeout=5)
			lb_log.info(f"[md_updating] chiamata a {self.domain} -> status {response.status_code}")
		except Exception as e:
			lb_log.error(f"[md_updating] errore chiamando {self.domain}: {e}")

	def stop(self):
		self._stop_event.set()
		if self.thread and self.thread.is_alive():
			self.thread.join(timeout=1)
