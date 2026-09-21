# ==== LIBRERIE DA IMPORTARE ===================================
import time
import requests
import libs.lb_log as lb_log
import libs.lb_config as lb_config
from libs.lb_utils import createThread, startThread
# ==============================================================

name_module = "md_updating"

CALL_INTERVAL_SECONDS = 5 * 60  # 5 minuti

def init():
	global module_updating
	lb_log.info("init")
	module_updating = ModuleUpdating()
	thread = createThread(module_updating.start)
	startThread(thread=thread)
	lb_log.info("end")

def start():
	lb_log.info("start")
	lb_log.info("end")

def stop():
	pass

class ModuleUpdating:
	def __init__(self):
		self.domain = lb_config.g_config["app_api"]["updating"]["domain"]

	def start(self):
		while lb_config.g_enabled:
			if self.domain:
				self.call_domain()
			for _ in range(CALL_INTERVAL_SECONDS):
				if not lb_config.g_enabled:
					break
				time.sleep(1)

	def call_domain(self):
		try:
			response = requests.get(self.domain, timeout=5)
			lb_log.info(f"[md_updating] chiamata a {self.domain} -> status {response.status_code}")
		except Exception as e:
			lb_log.error(f"[md_updating] errore chiamando {self.domain}: {e}")
