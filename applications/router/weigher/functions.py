from applications.router.weigher.dto import DataInExecutionDTO, DataDTO
from applications.router.weigher.types import Data
from modules.md_weigher import md_weigher
import libs.lb_config as lb_config
from applications.utils.utils_weigher import NodeConnectionManager
from libs.lb_database import get_data_by_id, update_data

class Functions:
	def __init__(self):
		self.weighers_data = {}

		md_weigher.module_weigher.initializeModuleConfig(config=lb_config.g_config["app_api"]["weighers"])

		for instance_name, instance in md_weigher.module_weigher.instances.items():
			nodes_sockets = {}
			for weigher_name, weigher in instance.nodes.items():
				nodes_sockets[weigher_name] = {
					"sockets": NodeConnectionManager(),
					"data": Data(**lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"])
				}
			self.weighers_data[instance_name] = nodes_sockets

		md_weigher.module_weigher.setApplicationCallback(
			cb_realtime=self.Callback_Realtime, 
			cb_diagnostic=self.Callback_Diagnostic, 
			cb_weighing=self.Callback_Weighing, 
			cb_tare_ptare_zero=self.Callback_TarePTareZero,
			cb_action_in_execution=self.Callback_ActionInExecution
		)
	
	def getData(self, instance_name: str, weigher_name: str):
		return lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]

	def setDataInExecution(self, instance_name: str, weigher_name: str, source: DataInExecutionDTO):
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
				if is_passed_some_values and current_data_contains_id:
					is_allow_none = True
				for sub_key, sub_value in vars(value).items():
					if sub_value is not None or is_allow_none:
						# Se il valore è un tipo primitivo, aggiorna il nuovo valore
						if sub_value in ["", "undefined", -1]:
							sub_value = None
						lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["data_in_execution"][key][sub_key] = sub_value
						lb_config.saveconfig()
		self.Callback_DataInExecution(instance_name=instance_name, weigher_name=weigher_name)

	def deleteDataInExecution(self, instance_name: str, weigher_name: str):
		# Per ogni chiave dei dati correnti
		for key, attr in lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["data_in_execution"].items():
			if isinstance(attr, str) or isinstance(attr, int):
				lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["data_in_execution"][key] = None
				lb_config.saveconfig()
			elif isinstance(attr, dict):
				# Resetta tutti gli attributi dell'oggetto corrente a None
				for sub_key in attr:
					lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["data_in_execution"][key][sub_key] = None
				lb_config.saveconfig()
		self.Callback_DataInExecution(instance_name=instance_name, weigher_name=weigher_name)
	
	def setIdSelected(self, instance_name: str, weigher_name: str, new_id: int):
		if new_id == -1:
			new_id = None
		current_id = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["id_selected"]["id"]
		if current_id is not None:
			update_data('reservation', current_id, {"selected": False})
		lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["id_selected"]["id"] = new_id
		lb_config.saveconfig()
		self.Callback_DataInExecution(instance_name=instance_name, weigher_name=weigher_name)
	
	def deleteIdSelected(self, instance_name: str, weigher_name: str):
		current_id = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["id_selected"]["id"]
		if current_id is not None:
			update_data('reservation', current_id, {"selected": False})
		lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["id_selected"]["id"] = None
		lb_config.saveconfig()
		self.Callback_DataInExecution(instance_name=instance_name, weigher_name=weigher_name)

	def addInstanceSocket(self, instance_name: str):
		self.weighers_data[instance_name] = {}

	def deleteInstanceSocket(self, instance_name: str):
		for node in self.weighers_data[instance_name]:
			self.weighers_data[instance_name][node]["sockets"].manager_realtime.disconnect_all()
			self.weighers_data[instance_name][node]["sockets"].manager_realtime = None
			self.weighers_data[instance_name][node]["sockets"].manager_diagnostic.disconnect_all()
			self.weighers_data[instance_name][node]["sockets"].manager_diagnostic = None
			self.weighers_data[instance_name][node]["data"].data_in_execution.deleteAttribute()
			self.weighers_data[instance_name][node]["data"].id_selected.deleteAttribute()
		self.weighers_data.pop(instance_name)

	def addInstanceWeigherSocket(self, instance_name: str, weigher_name: str, data: Data):
		node_sockets = {
			"sockets": NodeConnectionManager(),
			"data": data
		}
		self.weighers_data[instance_name][weigher_name] = node_sockets

	def deleteInstanceWeigherSocket(self, instance_name: str, weigher_name: str):
		self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.disconnect_all()
		self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime = None
		self.weighers_data[instance_name][weigher_name]["sockets"].manager_diagnostic.disconnect_all()
		self.weighers_data[instance_name][weigher_name]["sockets"].manager_diagnostic = None
		self.weighers_data[instance_name].pop(weigher_name)