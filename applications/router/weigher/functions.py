from applications.router.weigher.dto import DataInExecutionDTO
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
			if isinstance(value, str):
				if value in ["", "undefined", -1]:
					value = None
				lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["data_in_execution"][key] = value
			elif isinstance(value, object) and value is not None:
				current_attr = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["data_in_execution"][key]
				current_id = current_attr["id"]
				source_value_id = getattr(value, 'id')
				# Verifica se `source` ha qualsiasi altro attributo diverso da `id`
				other_source_values = any(sub_key != 'id' for sub_key in vars(source).keys())
				# Preparazione dei dati correnti prima di aggiungere le modifiche
				# Serve per gestire il cambio di selected sul database nel caso fosse in uso una anagrafica del database
				# Se l'id corrente è un numero
				if isinstance(current_id, int):
					# Controlla se é stato passato un nuovo id e se oltre a quello sono stati passati altri valori
					if source_value_id is None and other_source_values:
						# Se ci sono altri attributi, resetta tutti gli attributi correnti a None
						for sub_key, sub_value in vars(current_attr).items():
							lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["data_in_execution"][key][sub_key] = None
							lb_config.saveconfig()
					# Setta l'id corrente nel database a selected False siccome è stato cambiato passando l'id, o altri attributi o entrambi
					update_data(key, current_id, {"selected": False})
				# Modifica dei valori
				for sub_key, sub_value in vars(value).items():
					if sub_value is not None or current_id is not None:
						# Se il valore è un tipo primitivo, aggiorna il nuovo valore
						if sub_value in ["", "undefined", -1]:
							sub_value = None
						lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["data_in_execution"][key][sub_key] = sub_value
						lb_config.saveconfig()
		self.Callback_DataInExecution(instance_name=instance_name, weigher_name=weigher_name)

	def deleteDataInExecution(self, instance_name: str, weigher_name: str):
		# Per ogni chiave dei dati correnti
		for key, attr in lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["data_in_execution"].items():
			if isinstance(attr, str):
				lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["data_in_execution"][key] = None
				lb_config.saveconfig()
			elif isinstance(attr, dict):
				if hasattr(attr, "id"):
					# Ottiene l'id corrente dell'oggetto inerente alla chiave
					current_attr_id = lb_config.g_config["app_api"][instance_name]["nodes"][weigher_name]["data"]["data_in_execution"][key]["id"]
					# Se l'id corrente non é None allora setta selected False dell'id sul database
					if current_attr_id is not None:
						update_data(key, current_attr_id, {"selected": False})
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
			update_data('weighing', current_id, {"selected": False})
		lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["id_selected"]["id"] = new_id
		lb_config.saveconfig()
		self.Callback_DataInExecution(instance_name=instance_name, weigher_name=weigher_name)
	
	def deleteIdSelected(self, instance_name: str, weigher_name: str):
		current_id = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["id_selected"]["id"]
		if current_id is not None:
			update_data('weighing', current_id, {"selected": False})
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