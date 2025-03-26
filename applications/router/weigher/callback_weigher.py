import modules.md_weigher.md_weigher as md_weigher
import asyncio
from typing import Union
from modules.md_weigher.types import Realtime, Diagnostic, Weight
import libs.lb_config as lb_config
from modules.md_database.functions.add_data import add_data
from modules.md_database.functions.get_data_by_id import get_data_by_id
from modules.md_database.functions.get_data_by_attributes import get_data_by_attributes
from modules.md_database.functions.update_data import update_data
import datetime as dt
from applications.router.weigher.types import DataInExecution
from libs.lb_capture_camera import capture_camera_image
from applications.router.weigher.functions import Functions
from libs.lb_utils import has_values_besides_id, current_month
from libs.lb_folders import save_bytes_to_file, search_file

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
			if last_pesata.data_assigned.id_selected.id is None:
				node = md_weigher.module_weigher.getInstanceWeigher(instance_name=instance_name,weigher_name=weigher_name)
				tare = float(last_pesata.weight_executed.tare)
				reservation = {
					"typeSocialReason": last_pesata.data_assigned.data_in_execution.typeSocialReason,
					"idSocialReason": last_pesata.data_assigned.data_in_execution.social_reason.id,
					"idVector": last_pesata.data_assigned.data_in_execution.vector.id,
					"idVehicle": last_pesata.data_assigned.data_in_execution.vehicle.id,
					"idMaterial": last_pesata.data_assigned.data_in_execution.material.id,
					"note": last_pesata.data_assigned.data_in_execution.note,
					"number_weighings": last_pesata.data_assigned.number_weighings if tare == 0 else 2
				}
				if not last_pesata.data_assigned.data_in_execution.social_reason.id and has_values_besides_id(last_pesata.data_assigned.data_in_execution.social_reason.dict()):
					social_reason_without_id = last_pesata.data_assigned.data_in_execution.social_reason.dict()
					del social_reason_without_id["id"]
					exist_social_reason = get_data_by_attributes("social_reason", social_reason_without_id)
					if exist_social_reason:
						reservation["idSocialReason"] = exist_social_reason["id"]
					else:
						social_reason = add_data("social_reason", last_pesata.data_assigned.data_in_execution.social_reason.dict())
						reservation["idSocialReason"] = social_reason.id
				if not last_pesata.data_assigned.data_in_execution.vector.id and has_values_besides_id(last_pesata.data_assigned.data_in_execution.vector.dict()):
					vector_without_id = last_pesata.data_assigned.data_in_execution.vector.dict()
					del vector_without_id["id"]
					exist_vector = get_data_by_attributes("vector", vector_without_id)
					if exist_vector:
						reservation["idVector"] = exist_vector["id"]
					else:
						vector = add_data("vector", last_pesata.data_assigned.data_in_execution.vector.dict())
						reservation["idVector"] = vector.id
				if not last_pesata.data_assigned.data_in_execution.vehicle.id and has_values_besides_id(last_pesata.data_assigned.data_in_execution.vehicle.dict()):
					vehicle_without_id = last_pesata.data_assigned.data_in_execution.vehicle.dict()
					del vehicle_without_id["id"]
					exist_vehicle = get_data_by_attributes("vehicle", vehicle_without_id)
					if exist_vehicle:
						reservation["idVehicle"] = exist_vehicle["id"]
					else:
						vehicle = add_data("vehicle", last_pesata.data_assigned.data_in_execution.vehicle.dict())
						reservation["idVehicle"] = vehicle.id
				if not last_pesata.data_assigned.data_in_execution.material.id and has_values_besides_id(last_pesata.data_assigned.data_in_execution.material.dict()):
					material_without_id = last_pesata.data_assigned.data_in_execution.material.dict()
					del material_without_id["id"]
					exist_material = get_data_by_attributes("material", material_without_id)
					if exist_material:
						reservation["idMaterial"] = exist_material["id"]
					else:
						material = add_data("material", last_pesata.data_assigned.data_in_execution.material.dict())
						reservation["idMaterial"] = material.id
				reservation_add = add_data("reservation", reservation)
				if tare != 0:
					weighing_tare = {
						"weight": tare,
						"date": dt.datetime.now(),
						"pid": None,
						"weigher": weigher_name,
						"idReservation": reservation_add.id
					}
					add_data("weighing", weighing_tare)
				weighing = {
					"weight": last_pesata.weight_executed.gross_weight,
					"date": dt.datetime.now(),
					"pid": last_pesata.weight_executed.pid,
					"weigher": weigher_name,
					"idReservation": reservation_add.id
				}
				add_data("weighing", weighing)
				self.deleteDataInExecution(instance_name=instance_name, weigher_name=weigher_name)
			elif last_pesata.data_assigned.id_selected.id:
				reservation = get_data_by_id("reservation", last_pesata.data_assigned.id_selected.id)
				weighing = {
					"weight": last_pesata.weight_executed.gross_weight,
					"date": dt.datetime.now(),
					"pid": last_pesata.weight_executed.pid,
					"weigher": weigher_name,
					"idReservation": last_pesata.data_assigned.id_selected.id
     			}
				add_data("weighing", weighing)
				self.deleteIdSelected(instance_name=instance_name, weigher_name=weigher_name)
				self.deleteDataInExecution(instance_name=instance_name, weigher_name=weigher_name)
			for rele in lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["events"]["weighing"]["set_rele"]:
				key, value = next(iter(rele.items()))
				modope = "CLOSERELE" if value == 0 else "OPENRELE"
				md_weigher.module_weigher.setModope(instance_name=instance_name, weigher_name=weigher_name, modope=modope, port_rele=key)
			for cam in lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["events"]["weighing"]["cams"]:
				if cam["active"]:
					image_captured_details = capture_camera_image(camera_url=cam["url"])
					save_bytes_to_file(image_captured_details["image"], f"{last_pesata.weight_executed.pid}_{weigher_name}.png", lb_config.g_config["app_api"]["path_weighing_pictures"] + current_month())
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