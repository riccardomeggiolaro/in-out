import modules.md_weigher.md_weigher as md_weigher
import asyncio
from typing import Union
from modules.md_weigher.types import Realtime, Diagnostic, Weight
import libs.lb_config as lb_config
from libs.lb_database import add_data, get_data_by_id, get_data_by_attributes, update_data
import datetime as dt
from applications.router.weigher.types import DataInExecution
from libs.lb_capture_camera import capture_camera_image
from applications.router.weigher.functions import Functions
from libs.lb_utils import has_values_besides_id

class CallbackWeigher(Functions):
	def __init__(self):
		super().__init__()
  
		self.switch_to_call = None

	# ==== FUNZIONI RICHIAMABILI DENTRO LA APPLICAZIONE =================
	# Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di peso in tempo reale
	def Callback_Realtime(self, instance_name: str, weigher_name: str, pesa_real_time: Realtime):
		gross_weight = pesa_real_time.gross_weight
		float_gross_weight = None
		try:
			float_gross_weight = float(gross_weight)
		except:
			pass
		if type(float_gross_weight) is float:
			if float_gross_weight <= lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["min_weight"] and self.switch_to_call in [0, None]:
				for rele in lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["events"]["realtime"]["under_min"]["set_rele"]:
					key, value = next(iter(rele.items()))
					modope = "CLOSERELE" if value == 0 else "OPENRELE"
					md_weigher.module_weigher.setModope(instance_name=instance_name, weigher_name=weigher_name, modope=modope, port_rele=key)
				self.switch_to_call = 1
			elif float_gross_weight >= lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["min_weight"] and self.switch_to_call in [1, None]:
				for rele in lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["events"]["realtime"]["over_min"]["set_rele"]:
					key, value = next(iter(rele.items()))
					modope = "CLOSERELE" if value == 0 else "OPENRELE"
					md_weigher.module_weigher.setModope(instance_name=instance_name, weigher_name=weigher_name, modope=modope, port_rele=key)
				self.switch_to_call = 0
		asyncio.run(self.weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(pesa_real_time.dict()))

	# Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di diagnostica
	def Callback_Diagnostic(self, instance_name: str, weigher_name: str, diagnostic: Diagnostic):
		asyncio.run(self.weighers_data[instance_name][weigher_name]["sockets"].manager_diagnostic.broadcast(diagnostic.dict()))

	# Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di pesata
	def Callback_Weighing(self, instance_name: str, weigher_name: str, last_pesata: Weight):
		if last_pesata.weight_executed.executed:
			if last_pesata.data_assigned.id_selected.id is None and last_pesata.type_weighing in ["PRINT", "IN"]:
				node = md_weigher.module_weigher.getInstanceWeigher(instance_name=instance_name,weigher_name=weigher_name)
				tare = float(last_pesata.weight_executed.tare)
				weighing = {
					"typeSocialReason": last_pesata.data_assigned.data_in_execution.typeSocialReason,
					"idSocialReason": last_pesata.data_assigned.data_in_execution.social_reason.id,
					"idVector": last_pesata.data_assigned.data_in_execution.vector.id,
					"idVehicle": last_pesata.data_assigned.data_in_execution.vehicle.id,
					"idMaterial": last_pesata.data_assigned.data_in_execution.material.id,
					"note": last_pesata.data_assigned.data_in_execution.note,
					"weight1": last_pesata.weight_executed.gross_weight if last_pesata.type_weighing == "IN" else tare,
					"weight2": last_pesata.weight_executed.gross_weight if last_pesata.type_weighing != "IN" else None,
					"net_weight": last_pesata.weight_executed.net_weight,
					"date1": dt.datetime.now() if last_pesata.type_weighing == "IN" else None,
					"date2": dt.datetime.now() if last_pesata.type_weighing != "IN" else None,
					"pid1": last_pesata.weight_executed.pid if last_pesata.type_weighing == "IN" else None,
					"pid2": last_pesata.weight_executed.pid if last_pesata.type_weighing != "IN" else None,
					"weigher": weigher_name
				}
				if not last_pesata.data_assigned.data_in_execution.social_reason.id and has_values_besides_id(last_pesata.data_assigned.data_in_execution.social_reason.dict()):
					social_reason_without_id = last_pesata.data_assigned.data_in_execution.social_reason.dict()
					del social_reason_without_id["id"]
					exist_social_reason = get_data_by_attributes("social_reason", social_reason_without_id)
					if exist_social_reason:
						weighing["idSocialReason"] = exist_social_reason["id"]
					else:
						social_reason = add_data("social_reason", last_pesata.data_assigned.data_in_execution.social_reason.dict())
						weighing["idSocialReason"] = social_reason.id
				if not last_pesata.data_assigned.data_in_execution.vector.id and has_values_besides_id(last_pesata.data_assigned.data_in_execution.vector.dict()):
					vector_without_id = last_pesata.data_assigned.data_in_execution.vector.dict()
					del vector_without_id["id"]
					exist_vector = get_data_by_attributes("vector", vector_without_id)
					if exist_vector:
						weighing["idVector"] = exist_vector["id"]
					else:
						vector = add_data("vector", last_pesata.data_assigned.data_in_execution.vector.dict())
						weighing["idVector"] = vector.id
				if not last_pesata.data_assigned.data_in_execution.vehicle.id and has_values_besides_id(last_pesata.data_assigned.data_in_execution.vehicle.dict()):
					vehicle_without_id = last_pesata.data_assigned.data_in_execution.vehicle.dict()
					del vehicle_without_id["id"]
					exist_vehicle = get_data_by_attributes("vehicle", vehicle_without_id)
					if exist_vehicle:
						weighing["idVehicle"] = exist_vehicle["id"]
					else:
						vehicle = add_data("vehicle", last_pesata.data_assigned.data_in_execution.vehicle.dict())
						weighing["idVehicle"] = vehicle.id
				if not last_pesata.data_assigned.data_in_execution.material.id and has_values_besides_id(last_pesata.data_assigned.data_in_execution.material.dict()):
					material_without_id = last_pesata.data_assigned.data_in_execution.material.dict()
					del material_without_id["id"]
					exist_material = get_data_by_attributes("material", material_without_id)
					if exist_material:
						weighing["idMaterial"] = exist_material["id"]
					else:
						material = add_data("material", last_pesata.data_assigned.data_in_execution.material.dict())
						weighing["idMaterial"] = material.id
				# if last_pesata.data_assigned.data_in_execution.social_reason.id:
				# 	obj["idSocialReason"] = last_pesata.data_assigned.data_in_execution.social_reason.id
				# if last_pesata.data_assigned.data_in_execution.vehicle.id:
				# 	obj["idVehicle"] = last_pesata.data_assigned.data_in_execution.vehicle.id
				# if last_pesata.data_assigned.data_in_execution.material.id:
				# 	obj["idMaterial"] = last_pesata.data_assigned.data_in_execution.material.id
				# for cam in lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["cams"]:
				#	 image_capture = capture_camera_image(cam["camera_url"], cam["username"], cam["password"])
				#	 image_saved = add_data("image_captured", image_capture)
				add_data("weighing", weighing)
				self.deleteDataInExecution(instance_name=instance_name, weigher_name=weigher_name)
			elif last_pesata.data_assigned.id_selected.id is not None and last_pesata.type_weighing == "OUT":
				data = get_data_by_id("weighing", last_pesata.data_assigned.id_selected.id)
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
				update_data("weighing", last_pesata.data_assigned.id_selected.id, obj)
				self.deleteIdSelected(instance_name=instance_name, weigher_name=weigher_name)
			if last_pesata.weight_executed.tare == '0':
				for rele in lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["events"]["weighing"]["weight1"]["set_rele"]:
					key, value = next(iter(rele.items()))
					modope = "CLOSERELE" if value == 0 else "OPENRELE"
					md_weigher.module_weigher.setModope(instance_name=instance_name, weigher_name=weigher_name, modope=modope, port_rele=key)
					import libs.lb_log as lb_log
					lb_log.warning(value)
			else:
				for rele in lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["events"]["weighing"]["weight2"]["set_rele"]:
					key, value = next(iter(rele.items()))
					modope = "CLOSERELE" if value == 0 else "OPENRELE"
					md_weigher.module_weigher.setModope(instance_name=instance_name, weigher_name=weigher_name, modope=modope, port_rele=key)
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