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

	def initialize_from_config(self, config: dict):
		"""Inizializza le istanze dalla configurazione JSON."""
		for name, configuration in config.items():
			try:
				cfg = RfidConfigurationDTO(name=name, **configuration)
				instance = RfidInstance(name, cfg)
				self.instances[name] = instance
			except Exception as e:
				lb_log.error(f"Error initializing RFID instance '{name}': {e}")

	def set_application_callback(self, cb_cardcode: Callable[[str], any] = None):
		"""Imposta la callback per tutti i lettori."""
		for instance in self.instances.values():
			instance.set_action(cb_cardcode)

	def get_all_instances(self) -> dict:
		return {name: instance.get_instance() for name, instance in self.instances.items()}

	def get_instance(self, name: str) -> dict:
		if name not in self.instances:
			raise HTTPException(status_code=404, detail=f"Istanza '{name}' non trovata")
		return {name: self.instances[name].get_instance()}

	def create_instance(self, configuration: RfidConfigurationDTO) -> dict:
		if configuration.name in self.instances:
			raise HTTPException(status_code=400, detail=[{
				"type": "value_error", "loc": ["", "name"],
				"msg": "Nome già esistente", "input": configuration.name, "ctx": {"error": {}}
			}])
		instance = RfidInstance(configuration.name, configuration)
		self.instances[configuration.name] = instance
		# Salva in config
		lb_config.g_config["app_api"]["rfid"][configuration.name] = {
			"protocol": configuration.protocol,
			"connection": configuration.connection.dict() if configuration.connection else None,
			"setup": configuration.setup.dict() if configuration.setup else {}
		}
		lb_config.saveconfig()
		return {configuration.name: instance.get_instance()}

	def delete_instance(self, name: str) -> bool:
		if name not in self.instances:
			raise HTTPException(status_code=404, detail=f"Istanza '{name}' non trovata")
		self.instances[name].stop()
		del self.instances[name]
		# Rimuove dalla config
		lb_config.g_config["app_api"]["rfid"].pop(name, None)
		lb_config.saveconfig()
		return True

	def set_instance_connection(self, name: str, connection: RfidConnectionDTO) -> dict:
		if name not in self.instances:
			raise HTTPException(status_code=404, detail=f"Istanza '{name}' non trovata")
		result = self.instances[name].set_connection(connection)
		# Aggiorna config
		lb_config.g_config["app_api"]["rfid"][name]["connection"] = connection.dict()
		lb_config.saveconfig()
		return result

	def delete_instance_connection(self, name: str) -> bool:
		if name not in self.instances:
			raise HTTPException(status_code=404, detail=f"Istanza '{name}' non trovata")
		result = self.instances[name].delete_connection()
		lb_config.g_config["app_api"]["rfid"][name]["connection"] = None
		lb_config.saveconfig()
		return result


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

	def set_connection(self, connection: RfidConnectionDTO) -> dict:
		self.protocol.initialize(connection, RfidSetupDTO())
		return self.get_instance()

	def delete_connection(self) -> bool:
		return self.protocol.delete_config()
