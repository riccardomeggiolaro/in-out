import modules.md_weigher.md_weigher as md_weigher
import asyncio
from modules.md_weigher.types import Realtime, Diagnostic, Weight
import libs.lb_config as lb_config
from modules.md_database.md_database import ReservationStatus, TypeReservation
from modules.md_database.functions.get_reservation_by_id import get_reservation_by_id
from modules.md_database.functions.add_data import add_data
from modules.md_database.functions.update_data import update_data
from modules.md_database.functions.add_material_if_not_exist import add_material_if_not_exists
from modules.md_database.functions.get_data_by_id import get_data_by_id
from modules.md_database.interfaces.subject import SubjectDataDTO
from modules.md_database.interfaces.vector import VectorDataDTO
from modules.md_database.interfaces.driver import DriverDataDTO
from modules.md_database.interfaces.vehicle import VehicleDataDTO
from modules.md_database.interfaces.reservation import Reservation
import datetime as dt
from applications.router.weigher.types import ReportVariables
from libs.lb_capture_camera import capture_camera_image
from applications.router.weigher.functions import Functions
from libs.lb_folders import structure_folder_rule, save_bytes_to_file
from applications.router.anagrafic.web_sockets import WebSocket
from applications.router.weigher.manager_weighers_data import weighers_data
from applications.utils.utils_report import generate_report
from libs.lb_printer import printer

class CallbackWeigher(Functions, WebSocket):
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
		asyncio.run(weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(pesa_real_time.dict()))

	# Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di diagnostica
	def Callback_Diagnostic(self, instance_name: str, weigher_name: str, diagnostic: Diagnostic):
		asyncio.run(weighers_data[instance_name][weigher_name]["sockets"].manager_diagnostic.broadcast(diagnostic.dict()))

	# Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di pesata
	def Callback_Weighing(self, instance_name: str, weigher_name: str, last_pesata: Weight):
		reservation = get_reservation_by_id(last_pesata.data_assigned)
		if last_pesata.weight_executed.executed:
			############################
			# SALVATAGGIO DELLA PESATA
			date = dt.datetime.now()
			str_tare = last_pesata.weight_executed.tare.value
			str_net_weight = last_pesata.weight_executed.net_weight
			str_gross_weight = last_pesata.weight_executed.gross_weight
			tare = float(str_tare) if "," in str_tare or "." in str_tare else int(str_tare)
			net_weight = float(str_net_weight) if "," in str_net_weight or "." in str_net_weight else int(str_net_weight)
			gross_weight = float(str_gross_weight) if "," in str_gross_weight or "." in str_gross_weight else int(str_gross_weight)
			is_preset_tare = last_pesata.weight_executed.tare.is_preset_tare
			weighing = {
				"date": date,
				"weigher": weigher_name,
				"pid": last_pesata.weight_executed.pid,
				"tare": tare,
				"is_preset_tare": is_preset_tare,
				"weight": gross_weight,
			}
			weighing_stored_db = add_data("weighing", weighing)
			############################
			# SALVATAGGIO DEL MATERIALE
			id_material = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["data_in_execution"]["material"]["id"]
			description_material = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["data"]["data_in_execution"]["material"]["description"]
			if not id_material and description_material is not None:
				material = add_material_if_not_exists(description_material)
				import libs.lb_log as lb_log
				lb_log.warning(material)
				lb_log.warning(description_material)
				id_material = material["id"]
			############################
			# ASSOCIAZIONE DELLA PESATA SALVATA ALL COMBINAZIONE IN-OUT CORRETTA DELL'ACCESSO
			last_in_out = reservation.in_out[-1] if len(reservation.in_out) > 0 else None
			if last_in_out and not last_in_out.idWeight2:
				weight1 = last_in_out.weight1.weight
				net_weight = weight1 - gross_weight if weight1 > gross_weight else gross_weight - weight1
				update_data("in_out", last_in_out.id, {
					"idMaterial": id_material,
        			"idWeight2": weighing_stored_db["id"],
					"net_weight": net_weight
	           })
			elif last_in_out and last_in_out.idWeight2:
				weight1 = last_in_out.weight2.weight
				net_weight = weight1 - gross_weight if weight1 > gross_weight else gross_weight - weight1
				add_data("in_out", {
					"idReservation": last_pesata.data_assigned,
					"idMaterial": id_material,
					"idWeight1": last_in_out.idWeight2,
					"idWeight2": weighing_stored_db["id"],
					"net_weight": net_weight,
				})
			else:
				add_data("in_out", {
					"idReservation": last_pesata.data_assigned,
					"idMaterial": id_material,
					"idWeight1": weighing_stored_db["id"] if tare == 0 else None,
					"idWeight2": weighing_stored_db["id"] if tare > 0 else None,
					"net_weight": net_weight if tare > 0 else None
				})
			############################
			# AGGIORNAMENTO DELL'ACCESSO
			reservation = get_reservation_by_id(last_pesata.data_assigned)
			last_in_out = reservation.in_out[-1] if len(reservation.in_out) > 0 else None
			len_in_out = len(reservation.in_out)
			is_test = reservation.type == TypeReservation.TEST
			updated_reservation = update_data("reservation", last_pesata.data_assigned, {
				"status": ReservationStatus.CLOSED if len_in_out == reservation.number_in_out and last_in_out.idWeight2 or is_test else ReservationStatus.ENTERED,
				"hidden": False
			})
			reservation_data_json = Reservation(**updated_reservation).json()
			asyncio.run(self.broadcastUpdateAnagrafic("reservation", {"weighing": reservation_data_json}))
			############################
			# RIMUOVE TUTTI I DATA IN EXECUTION
			self.deleteDataInExecution(instance_name=instance_name, weigher_name=weigher_name)
			self.deleteIdSelected(instance_name=instance_name, weigher_name=weigher_name)
			############################
			# DATI UTILI ALLA STAMPA DEL REPORT
			printer_name = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["printer_name"]
			template_in = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["events"]["weighing"]["reports"]["in"]
			template_out = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["events"]["weighing"]["reports"]["out"]
			template = template_in if tare > 0 else template_out
			variables = ReportVariables(**{})
			variables.typeSubject = reservation.typeSubject.value
			variables.subject = reservation.subject.__dict__ if reservation.subject else SubjectDataDTO(**{})
			variables.vector = reservation.vector.__dict__ if reservation.vector else VectorDataDTO(**{})
			variables.driver = reservation.driver.__dict__ if reservation.driver else DriverDataDTO(**{})
			variables.vehicle = reservation.vehicle.__dict__ if reservation.vehicle else VehicleDataDTO(**{})
			variables.note = reservation.note
			variables.document_reference = reservation.document_reference
			# if len(reservation["weighings"]) > 1:
			# 	last_weighing = reservation["weighings"][-2]
			# 	variables.weight1.date = last_weighing["date"].strftime("%d/%m/%Y %H:%M")
			# 	variables.weight1.pid = last_weighing["pid"]
			# 	variables.weight1.weight = last_weighing["weight"]
			# 	variables.weight1.type = None
			# 	variables.weight2.date = dt.datetime.now().strftime("%d/%m/%Y %H:%M")
			# 	variables.weight2.pid = last_pesata.weight_executed.pid
			# 	variables.weight2.weight = float(last_pesata.weight_executed.gross_weight) if "." in last_pesata.weight_executed.gross_weight or "," in last_pesata.weight_executed.gross_weight else int(last_pesata.weight_executed.gross_weight)
			# 	variables.weight2.type = None
			# 	if variables.weight1.weight > variables.weight2.weight:
			# 		variables.net_weight = variables.weight1.weight - variables.weight2.weight
			# 	else:
			# 		variables.net_weight = variables.weight2.weight - variables.weight1.weight
			# else:
			# 	variables.weight1.date = dt.datetime.now().strftime("%d/%m/%Y %H:%M")
			# 	variables.weight1.pid = last_pesata.weight_executed.pid
			# 	variables.weight1.weight = last_pesata.weight_executed.gross_weight
			# 	variables.weight1.type = None
			# reservation_update = None
			# if reservation["number_in_out"] == len(reservation["weighings"]):
			# 	reservation_update = update_data("reservation", last_pesata.data_assigned.id_selected.id, {"status": ReservationStatus.CLOSED})
			# else:
			# 	reservation_update = update_data("reservation", last_pesata.data_assigned.id_selected.id, {"status": ReservationStatus.ENTERED})
			# self.deleteIdSelected(instance_name=instance_name, weigher_name=weigher_name)
			# self.deleteDataInExecution(instance_name=instance_name, weigher_name=weigher_name)
			# asyncio.run(self.broadcastAddAnagrafic("reservation", {"weighing": Reservation(**reservation_update).json()}))
			# if len(reservation["weighings"]) > 1:
			# 	template = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["events"]["weighing"]["reports"]["out"]
			# else:
			# 	template = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["events"]["weighing"]["reports"]["in"]
			if printer_name and template:
				report = generate_report(template, v=variables.dict())
				printer.print_html(html_content=report, printer_name=printer_name)
			if weighing_stored_db:
				for rele in lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["events"]["weighing"]["set_rele"]:
					key, value = next(iter(rele.items()))
					modope = "CLOSERELE" if value == 0 else "OPENRELE"
					md_weigher.module_weigher.setModope(instance_name=instance_name, weigher_name=weigher_name, modope=modope, port_rele=key)
				for cam in lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["events"]["weighing"]["cams"]:
					if cam["active"]:
						image_captured_details = capture_camera_image(camera_url=cam["picture"], timeout=5)
						if image_captured_details["image"]:
							base_folder_path = lb_config.g_config["app_api"]["path_weighing_pictures"]
							sub_folder_path = structure_folder_rule()
							file_name = f"{last_pesata.weight_executed.pid}.png"
							save_bytes_to_file(image_captured_details["image"], file_name, f"{base_folder_path}{sub_folder_path}")
							add_data("weighing_picture", {"path_name": f"{sub_folder_path}/{file_name}", "idWeighing": weighing_stored_db["id"]})
		for instance in weighers_data:
			for weigher in weighers_data[instance]:
				weight = last_pesata.dict()
				weight["instance_name"] = instance_name
				weight["weigher_name"] = weigher_name
				asyncio.run(weighers_data[instance][weigher]["sockets"].manager_realtime.broadcast(weight))

	def Callback_TarePTareZero(self, instance_name: str, weigher_name: str, ok_value: str):
		asyncio.run(weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast({"command_executed": ok_value}))

	def Callback_DataInExecution(self, instance_name, weigher_name):
		try:
			if asyncio.get_event_loop().is_running():
				asyncio.create_task(weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(self.getData(instance_name=instance_name, weigher_name=weigher_name)))
			else:
				loop = asyncio.get_event_loop()
				loop.run_until_complete(weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(self.getData(instance_name=instance_name, weigher_name=weigher_name)))
		except RuntimeError:
			asyncio.run(weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(self.getData(instance_name=instance_name, weigher_name=weigher_name)))

	def Callback_ActionInExecution(self, instance_name: str, weigher_name: str, action_in_execution: str):
		result = {"command_in_executing": action_in_execution}
		try:
			if asyncio.get_event_loop().is_running():
				asyncio.create_task(weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(result))
			else:
				loop = asyncio.get_event_loop()
				loop.run_until_complete(weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(result))
		except Exception as e:
			asyncio.run(weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(result))
		
	def Callback_Rele(self, instance_name: str, weigher_name: str, port_rele: tuple):
		key, value = port_rele
		result = {"rele": key, "status": value}
		try:
			if asyncio.get_event_loop().is_running():
				asyncio.create_task(weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(result))
			else:
				loop = asyncio.get_event_loop()
				loop.run_until_complete(weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(result))
		except RuntimeError:
			asyncio.run(weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(result))
   
	def Callback_Message(self, instance_name: str, weigher_name: str, message: str):
		result = {"message": message}
		try:
			if asyncio.get_event_loop().is_running():
				asyncio.create_task(weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(result))
			else:
				loop = asyncio.get_event_loop()
				loop.run_until_complete(weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(result))
		except RuntimeError:
			asyncio.run(weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(result))