# ==============================================================
# = Module......: md_rfid                                      =
# = Description.: Modulo RFID multi-istanza multi-protocollo   =
# = Author......: Riccardo Meggiolaro                          =
# ==============================================================

import libs.lb_log as lb_log
import libs.lb_config as lb_config
import time
from typing import Callable, Optional
from libs.lb_utils import createThread, startThread
from modules.md_rfid.globals import protocolsClasses
from modules.md_rfid.protocols.rfid_serial import RfidSerial
from modules.md_rfid.protocols.apromix_rfid_serial import ApromixRfidSerial
from modules.md_rfid.dto import RfidConfigurationDTO, RfidConnectionDTO, RfidSetupDTO
from fastapi import HTTPException

name_module = "md_rfid"

# Registra i protocolli disponibili
protocolsClasses[RfidSerial.NAME] = RfidSerial
protocolsClasses[ApromixRfidSerial.NAME] = ApromixRfidSerial

def init():
	global module_rfid
	lb_log.info("init")
	module_rfid = RfidModule()
	lb_log.info("end")

def start():
	lb_log.info("start")
	while lb_config.g_enabled:
		time.sleep(1)
	lb_log.info("end")

def stop():
	pass

class RfidModule:
	def __init__(self):
		self.instances = {}

	def initialize_from_config(self, weighers_config: dict):
		"""Inizializza le istanze RFID dal config delle pese.
		   weighers_config = { "0": { ..., "rfid": {...} }, ... }
		"""
		for instance_name, weigher_cfg in weighers_config.items():
			rfid_cfg = weigher_cfg.get("rfid")
			if not rfid_cfg:
				continue
			try:
				cfg = RfidConfigurationDTO(name=instance_name, **rfid_cfg)
				instance = RfidInstance(instance_name, cfg)
				self.instances[instance_name] = instance
			except Exception as e:
				lb_log.error(f"Error initializing RFID for weigher '{instance_name}': {e}")

	def set_application_callback(self, cb_cardcode: Callable[[str], any] = None):
		"""Imposta la callback per tutti i lettori."""
		for instance in self.instances.values():
			instance.set_action(cb_cardcode)

	def get_all_instances(self) -> dict:
		return {name: instance.get_instance() for name, instance in self.instances.items()}

	def get_instance(self, instance_name: str) -> Optional[dict]:
		if instance_name not in self.instances:
			return None
		return self.instances[instance_name].get_instance()

	def set_instance(self, instance_name: str, configuration: RfidConfigurationDTO) -> dict:
		"""Crea o sostituisce l'istanza RFID per una pesa."""
		# Ferma eventuale istanza precedente
		if instance_name in self.instances:
			self.instances[instance_name].stop()
			del self.instances[instance_name]

		instance = RfidInstance(instance_name, configuration)
		self.instances[instance_name] = instance

		# Salva nel config della pesa corrispondente
		lb_config.g_config["app_api"]["weighers"][instance_name]["rfid"] = {
			"protocol": configuration.protocol,
			"connection": configuration.connection.dict() if configuration.connection else None,
			"setup": configuration.setup.dict() if configuration.setup else {}
		}
		lb_config.saveconfig()
		return instance.get_instance()

	def delete_instance(self, instance_name: str) -> bool:
		"""Elimina l'istanza RFID di una pesa."""
		if instance_name not in self.instances:
			return False
		self.instances[instance_name].stop()
		del self.instances[instance_name]
		# Rimuove dalla config della pesa
		lb_config.g_config["app_api"]["weighers"][instance_name].pop("rfid", None)
		lb_config.saveconfig()
		return True


class RfidInstance:
	def __init__(self, name: str, configuration: RfidConfigurationDTO):
		self.m_enabled = True
		self.name = name
		self.protocol_name = configuration.protocol
		self.protocol = protocolsClasses[configuration.protocol]()

		if configuration.connection:
			setup = configuration.setup or RfidSetupDTO()
			self.protocol.initialize(configuration.connection, setup)

		self.thread = createThread(self._run)
		startThread(self.thread)

	def _run(self):
		self.protocol.start(lambda: self.m_enabled)

	def stop(self):
		self.m_enabled = False
		self.protocol.delete_config()

	def get_instance(self) -> dict:
		return {
			"protocol": self.protocol_name,
			**self.protocol.get_config()
		}

	def set_action(self, cb_cardcode: Callable[[str], any] = None):
		self.protocol.set_action(cb_cardcode)
