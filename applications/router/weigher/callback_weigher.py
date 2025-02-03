import modules.md_weigher.md_weigher as md_weigher
import asyncio
from applications.utils.utils_weigher import NodeConnectionManager
from typing import Union
from modules.md_weigher.types import Realtime, Diagnostic, Weight
import libs.lb_config as lb_config
from libs.lb_database import add_data, get_data_by_id, update_data
import datetime as dt
import libs.lb_log as lb_log
from applications.router.weigher.types import Data, DataInExecution, IdSelected
from libs.lb_capture_camera import capture_camera_image
from applications.router.weigher.dto import DataInExecutionDTO

class CallbackWeigher:
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

	# ==== FUNZIONI RICHIAMABILI DENTRO LA APPLICAZIONE =================
	# Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di peso in tempo reale
	def Callback_Realtime(self, instance_name: str, weigher_name: str, pesa_real_time: Realtime):
		asyncio.run(self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(pesa_real_time.dict()))

	# Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di diagnostica
	def Callback_Diagnostic(self, instance_name: str, weigher_name: str, diagnostic: Diagnostic):
		asyncio.run(self.weighers_data[instance_name][weigher_name]["sockets"].manager_diagnostic.broadcast(diagnostic.dict()))

	# Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di pesata
	def Callback_Weighing(self, instance_name: str, weigher_name: str, last_pesata: Weight):
		if last_pesata.weight_executed.executed:
			if isinstance(last_pesata.data_assigned, DataInExecution):
				node = md_weigher.module_weigher.getInstanceWeigher(instance_name=instance_name,weigher_name=weigher_name)
				obj = {
					"plate": last_pesata.data_assigned.vehicle.plate,
					"vehicle": last_pesata.data_assigned.vehicle.name,
					"customer": last_pesata.data_assigned.customer.name, 
					"customer_cell": last_pesata.data_assigned.customer.cell,
					"customer_cfpiva": last_pesata.data_assigned.customer.cfpiva,
					"supplier": last_pesata.data_assigned.supplier.name,
					"supplier_cell": last_pesata.data_assigned.supplier.cell,
					"supplier_cfpiva": last_pesata.data_assigned.supplier.cfpiva,
					"material": last_pesata.data_assigned.material.name,
					"note": last_pesata.data_assigned.note,
					"weight1": last_pesata.weight_executed.gross_weight,
					"weight2": None if last_pesata.weight_executed.tare == '0' else last_pesata.weight_executed.tare,
					"net_weight": last_pesata.weight_executed.net_weight,
					"date1": None if last_pesata.weight_executed.tare != '0' else dt.datetime.now(),
					"date2": None if last_pesata.weight_executed.tare == '0' else dt.datetime.now(),
					"card_code": None,
					"card_number": None,
					"pid1": None if last_pesata.weight_executed.tare != '0' else last_pesata.weight_executed.pid,
					"pid2": None if last_pesata.weight_executed.tare == '0' else last_pesata.weight_executed.pid,
					"weigher": weigher_name
				}
				# for cam in lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["cams"]:
				#	 image_capture = capture_camera_image(cam["camera_url"], cam["username"], cam["password"])
				#	 image_saved = add_data("image_captured", image_capture)
				add_data("weighing", obj)
				self.deleteDataInExecution(instance_name=instance_name, weigher_name=weigher_name)
			elif isinstance(last_pesata.data_assigned, int) and last_pesata.weight_executed.executed:
				lb_log.warning("2")
				data = get_data_by_id("weighing", last_pesata.data_assigned)
				net_weight = data["weight1"] - int(last_pesata.weight_executed.gross_weight)
				obj = {
					"weight2": last_pesata.weight_executed.gross_weight,
					"net_weight": net_weight,
					"date2": dt.datetime.now(),
					"pid2": last_pesata.weight_executed.pid
				}
				# for cam in lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["cams"]:
				#	 image_capture = capture_camera_image(cam["camera_url"], cam["username"], cam["password"])
				#	 image_saved = add_data("image_captured", image_capture)
				update_data("weighing", last_pesata.data_assigned, obj)
				self.deleteIdSelected(instance_name=instance_name, weigher_name=weigher_name)
			elif last_pesata.data_assigned is None and last_pesata.weight_executed.executed:
				node = md_weigher.module_weigher.instances[instance_name].getNode(weigher_name)
				obj = {
					"plate": None,
					"vehicle": None,
					"customer": None, 
					"customer_cell": None,
					"customer_cfpiva": None,
					"supplier": None,
					"supplier_cell": None,
					"supplier_cfpiva": None,
					"material": None,
					"note": None,
					"weight1": last_pesata.weight_executed.gross_weight,
					"weight2": None if last_pesata.weight_executed.tare == '0' else last_pesata.weight_executed.tare,
					"net_weight": last_pesata.weight_executed.net_weight,
					"date1": None,
					"date2": dt.datetime.now(),
					"card_code": None,
					"card_number": None,
					"pid1": None,
					"pid2": last_pesata.weight_executed.pid,
					"weigher": weigher_name
				}
				# for cam in lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["cams"]:
				# 	image_capture = capture_camera_image(cam["camera_url"], cam["username"], cam["password"])
				# 	image_saved = add_data("image_captured", image_capture)
				add_data("weighing", obj)
		asyncio.run(self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(last_pesata.dict()))

	def Callback_TarePTareZero(self, instance_name: str, weigher_name: str, ok_value: str):
		asyncio.run(self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast({"command_executed": ok_value}))

	def Callback_DataInExecution(self, instance_name, weigher_name):
		try:
			if asyncio.get_event_loop().is_running():
				asyncio.create_task(self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(self.getData(instance_name=instance_name, weigher_name=weigher_name)))
			else:
				loop = asyncio.get_event_loop()
				loop.run_until_complete(self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(self.getData(instance_name=instance_name, weigher_name=weigher_name)))
		except RuntimeError:
			asyncio.run(self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(self.getData(instance_name=instance_name, weigher_name=weigher_name)))

	def Callback_ActionInExecution(self, instance_name: str, weigher_name: str, action_in_execution: str):
		result = {"command_in_executing": action_in_execution}
		try:
			if asyncio.get_event_loop().is_running():
				asyncio.create_task(self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(result))
			else:
				loop = asyncio.get_event_loop()
				loop.run_until_complete(self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(result))
		except Exception as e:
			asyncio.run(self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(result))
		
	def Callback_Rele(self, instance_name: str, weigher_name: str, port_rele: tuple):
		key, value = port_rele
		result = {"rele": key, "status": value}
		try:
			if asyncio.get_event_loop().is_running():
				asyncio.create_task(self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(result))
			else:
				loop = asyncio.get_event_loop()
				loop.run_until_complete(self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(result))
		except RuntimeError:
			asyncio.run(self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(result))