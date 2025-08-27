from fastapi import HTTPException
from applications.router.weigher.dto import DataInExecutionDTO
from applications.router.weigher.types import Data
from applications.router.weigher.manager_weighers_data import weighers_data
from modules.md_weigher import md_weigher
import libs.lb_config as lb_config
from applications.utils.utils_weigher import NodeConnectionManager
from modules.md_database.md_database import TypeReservation
from modules.md_database.functions.unlock_record_by_attributes import unlock_record_by_attributes
from modules.md_database.functions.lock_record import lock_record
from applications.router.weigher.types import DataInExecution
from applications.utils.utils import just_locked_message

class Functions:
	def __init__(self):
		md_weigher.module_weigher.initializeModuleConfig(config=lb_config.g_config["app_api"]["weighers"])

		for instance_name, instance in md_weigher.module_weigher.instances.items():
			nodes_sockets = {}
			for weigher_name, weigher in instance.nodes.items():
				nodes_sockets[weigher_name] = {
					"sockets": NodeConnectionManager(),
					"data": Data(**lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"])
				}
			weighers_data[instance_name] = nodes_sockets

		md_weigher.module_weigher.setApplicationCallback(
			cb_realtime=self.Callback_Realtime, 
			cb_diagnostic=self.Callback_Diagnostic, 
			cb_weighing=self.Callback_Weighing, 
			cb_tare_ptare_zero=self.Callback_TarePTareZero,
			cb_action_in_execution=self.Callback_ActionInExecution,
			cb_rele=self.Callback_Rele,
			cb_code_identify=self.Callback_WeighingByIdentify
		)
	
	def getData(self, instance_name: str, weigher_name: str):
		return lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]

	def setDataInExecution(self, instance_name: str, weigher_name: str, source: DataInExecutionDTO, idReservation: int = None):
		# Per ogni chiave dei nuovi dati passati controlla se è un oggetto o None
		for key, value in vars(source).items():
			if isinstance(value, str) or isinstance(value, int):
				if value in ["", "undefined", -1]:
					value = None
				lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["data_in_execution"][key] = value
				lb_config.saveconfig()
			elif isinstance(value, object) and value is not None:
				is_allow_none = False
				is_passed_some_values = {sub_key: sub_value for sub_key, sub_value in vars(value).items() if sub_value is not None}
				current_data_contains_id = True if "id" in lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["data_in_execution"][key] and lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["data_in_execution"][key]["id"] is not None else False
				if is_passed_some_values:
					if current_data_contains_id:
						is_allow_none = True
						current_id = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["data_in_execution"][key]["id"]
						if current_id:
							unlock_record_by_attributes(key, current_id, None, weigher_name)
					if value.id and value.id not in [None, -1]:
						success, locked_record, error = lock_record(key, value.id, "SELECT", None, None, weigher_name)
						if success is False:
							message = just_locked_message("SELECT", key, locked_record.user.username if locked_record.user else None, locked_record.weigher_name)
							raise HTTPException(status_code=400, detail=message)
				for sub_key, sub_value in vars(value).items():
					if sub_value is not None or is_allow_none:
						# Se il valore è un tipo primitivo, aggiorna il nuovo valore
						if sub_value in ["", "undefined", -1]:
							sub_value = None
						lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["data_in_execution"][key][sub_key] = sub_value
						lb_config.saveconfig()
							
		self.Callback_DataInExecution(instance_name=instance_name, weigher_name=weigher_name)

	def deleteData(self, instance_name: str, weigher_name: str):
		lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["type"] = TypeReservation.MANUALLY.name
		lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["number_in_out"] = 1
		lb_config.saveconfig()
		self.deleteDataInExecution(instance_name=instance_name, weigher_name=weigher_name)
		self.deleteIdSelected(instance_name=instance_name, weigher_name=weigher_name)

	def deleteDataInExecution(self, instance_name: str, weigher_name: str):
		for key, value in lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["data_in_execution"].items():
			if isinstance(value, object) and value is not None:
				if "id" in value and value["id"] is not None:
					unlock_record_by_attributes(key, value["id"], None, weigher_name)
		# Per ogni chiave dei dati correnti
		lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["data_in_execution"] = DataInExecution(**{}).dict()
		lb_config.saveconfig()
		self.Callback_DataInExecution(instance_name=instance_name, weigher_name=weigher_name)
	
	def setIdSelected(self, instance_name: str, weigher_name: str, new_id: int, weight1: int):
		if new_id == -1:
			new_id = None
		else:
			success, locked_record, error = lock_record("reservation", new_id, "SELECT", None, None, weigher_name)
			if success is False:
				message = just_locked_message("SELECT", "reservation", locked_record.user.username if locked_record.user else None, locked_record.weigher_name)
				raise HTTPException(status_code=400, detail=message)
		lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["id_selected"] = {
			"id": new_id,
			"weight1": weight1
		}
		lb_config.saveconfig()
		self.Callback_DataInExecution(instance_name=instance_name, weigher_name=weigher_name)
	
	def deleteIdSelected(self, instance_name: str, weigher_name: str):
		current_id = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["id_selected"]["id"]
		if current_id is not None:
			unlock_record_by_attributes("reservation", current_id, None, weigher_name)
		lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["id_selected"] = {
			"id": None,
			"weight1": None
		}
		lb_config.saveconfig()
		self.Callback_DataInExecution(instance_name=instance_name, weigher_name=weigher_name)

	def addInstanceSocket(self, instance_name: str):
		weighers_data[instance_name] = {}

	def deleteInstanceSocket(self, instance_name: str):
		for node in weighers_data[instance_name]:
			weighers_data[instance_name][node]["sockets"].manager_realtime.disconnect_all()
			weighers_data[instance_name][node]["sockets"].manager_realtime = None
			weighers_data[instance_name][node]["sockets"].manager_diagnostic.disconnect_all()
			weighers_data[instance_name][node]["sockets"].manager_diagnostic = None
		weighers_data.pop(instance_name)

	def addInstanceWeigherSocket(self, instance_name: str, weigher_name: str, data: Data):
		node_sockets = {
			"sockets": NodeConnectionManager(),
			"data": data
		}
		weighers_data[instance_name][weigher_name] = node_sockets

	def deleteInstanceWeigherSocket(self, instance_name: str, weigher_name: str):
		weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.disconnect_all()
		weighers_data[instance_name][weigher_name]["sockets"].manager_realtime = None
		weighers_data[instance_name][weigher_name]["sockets"].manager_diagnostic.disconnect_all()
		weighers_data[instance_name][weigher_name]["sockets"].manager_diagnostic = None
		weighers_data[instance_name].pop(weigher_name)