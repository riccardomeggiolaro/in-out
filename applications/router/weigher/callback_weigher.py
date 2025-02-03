import modules.md_weigher.md_weigher as md_weigher
import asyncio
from typing import Union
from modules.md_weigher.types import Realtime, Diagnostic, Weight
import libs.lb_config as lb_config
from libs.lb_database import add_data, get_data_by_id, update_data
import datetime as dt
from applications.router.weigher.types import DataInExecution
from libs.lb_capture_camera import capture_camera_image
from applications.router.weigher.functions import Functions

class CallbackWeigher(Functions):
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