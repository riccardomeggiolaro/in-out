import modules.md_weigher.md_weigher as md_weigher
import asyncio
from modules.md_weigher.types import Realtime, Diagnostic, Weight, WeightTerminal
import libs.lb_config as lb_config
import libs.lb_log as lb_log
from modules.md_database.md_database import AccessStatus, TypeAccess, TypeSubjectEnum
from modules.md_database.functions.get_access_by_id import get_access_by_id
from modules.md_database.functions.add_data import add_data
from modules.md_database.functions.update_data import update_data
from modules.md_database.functions.delete_data import delete_data
from modules.md_database.functions.add_material_if_not_exist import add_material_if_not_exists
from modules.md_database.functions.get_data_by_id import get_data_by_id
from modules.md_database.functions.get_data_by_attributes import get_data_by_attributes
from modules.md_database.interfaces.access import Access
from modules.md_database.interfaces.user import User
import datetime as dt
from libs.lb_capture_camera import capture_camera_image
from applications.router.weigher.functions import Functions
from libs.lb_folders import structure_folder_rule, save_bytes_to_file
from applications.router.anagrafic.web_sockets import WebSocket
from applications.router.weigher.manager_weighers_data import weighers_data
from applications.utils.utils_report import get_data_variables, generate_html_report, generate_csv_report, save_file_dir
from libs.lb_printer import printer
import applications.utils.utils as utils
import threading
from libs.lb_utils import base_path
from datetime import datetime
import json

class CallbackWeigher(Functions, WebSocket):
	def __init__(self):
		super().__init__()
  
	# ==== FUNZIONI RICHIAMABILI DENTRO LA APPLICAZIONE =================
	# Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di peso in tempo reale
	def Callback_Realtime(self, instance_name: str, weigher_name: str, pesa_real_time: Realtime):
		try:
			gross_weight = pesa_real_time.gross_weight
			if gross_weight == "":
				self.switch_to_call_instance_weigher[instance_name][weigher_name] = None
			numeric_gross_weight = None
			try:
				if "," in gross_weight or "." in gross_weight:
					numeric_gross_weight = float(gross_weight)
				else:
					numeric_gross_weight = int(gross_weight)
			except:
				pass
			if type(numeric_gross_weight) in [float, int]:
				if numeric_gross_weight < lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["min_weight"] and self.switch_to_call_instance_weigher[instance_name][weigher_name] in [0, None]:
					data = self.getData(instance_name=instance_name, weigher_name=weigher_name)
					if data["id_selected"]["need_to_confirm"] is True:
						self.deleteData(instance_name=instance_name, weigher_name=weigher_name)
						thread = threading.Thread()
					for rele in lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["events"]["realtime"]["under_min"]["set_rele"]:
						modope = "CLOSERELE" if rele["set"] == 0 else "OPENRELE"
						rele_status = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["rele"][rele["rele"]]
						md_weigher.module_weigher.setModope(instance_name=instance_name, weigher_name=weigher_name, modope=modope, port_rele=(rele["rele"], rele_status))
					self.switch_to_call_instance_weigher[instance_name][weigher_name] = 1
				elif numeric_gross_weight >= lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["min_weight"] and self.switch_to_call_instance_weigher[instance_name][weigher_name] in [1, None]:
					for rele in lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["events"]["realtime"]["over_min"]["set_rele"]:
						modope = "CLOSERELE" if rele["set"] == 0 else "OPENRELE"
						rele_status = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["rele"][rele["rele"]]
						md_weigher.module_weigher.setModope(instance_name=instance_name, weigher_name=weigher_name, modope=modope, port_rele=(rele["rele"], rele_status))
					self.switch_to_call_instance_weigher[instance_name][weigher_name] = 0
				weight1 = weighers_data[instance_name][weigher_name]["data"]["id_selected"]["weight1"]
				if pesa_real_time.status == "ST" and weight1:
					pesa_real_time.potential_net_weight = numeric_gross_weight - weight1 if numeric_gross_weight > weight1 else weight1 - numeric_gross_weight
				else:
					pesa_real_time.potential_net_weight = None
				max_theshold = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["max_theshold"]
				if max_theshold is not None and numeric_gross_weight > max_theshold:
					pesa_real_time.over_max_theshold = True
				else:
					pesa_real_time.over_max_theshold = False
			asyncio.run(weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(pesa_real_time.dict()))
		except Exception as e:
			lb_log.error(e)
			pass

	# Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di diagnostica
	def Callback_Diagnostic(self, instance_name: str, weigher_name: str, diagnostic: Diagnostic):
		asyncio.run(weighers_data[instance_name][weigher_name]["sockets"].manager_diagnostic.broadcast(diagnostic.dict()))

	# Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di pesata
	def Callback_Weighing(self, instance_name: str, weigher_name: str, last_pesata: Weight):
		access = get_access_by_id(last_pesata.data_assigned.accessId)
		user = get_data_by_id("user", last_pesata.data_assigned.userId)
		# lb_log.warning(last_pesata.data_assigned.userId)
		if last_pesata.weight_executed.executed and not "NO" in last_pesata.weight_executed.pid:
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
				"weigher_serial_number": last_pesata.weight_executed.serial_number,
				"pid": last_pesata.weight_executed.pid,
				"tare": tare,
				"is_preset_tare": is_preset_tare,
				"weight": gross_weight,
				"log": last_pesata.weight_executed.log,
				"idUser": last_pesata.data_assigned.userId
			}
			weighing_stored_db = add_data("weighing", weighing)
			############################
			# SALVATAGGIO DEL MATERIALE
			id_material = weighers_data[instance_name][weigher_name]["data"]["data_in_execution"]["material"]["id"]
			description_material = weighers_data[instance_name][weigher_name]["data"]["data_in_execution"]["material"]["description"]
			if not id_material and description_material is not None:
				material = add_material_if_not_exists(description_material)
				id_material = material["id"]
			############################
			# ASSOCIAZIONE DELLA PESATA SALVATA ALLA COMBINAZIONE IN-OUT CORRETTA DELL'ACCESSO
			last_in_out = access.in_out[-1] if len(access.in_out) > 0 else None
			if last_in_out and not last_in_out.idWeight2:
				weight1 = last_in_out.weight1.weight
				net_weight = weight1 - gross_weight if weight1 > gross_weight else gross_weight - weight1
				update_data("in_out", last_in_out.id, {
					"idMaterial": id_material,
        			"idWeight2": weighing_stored_db["id"],
					"net_weight": net_weight
	           })
			elif last_in_out and last_in_out.idWeight2 and tare == 0 and access.number_in_out is not None:
				weight1 = last_in_out.weight2.weight
				net_weight = weight1 - gross_weight if weight1 > gross_weight else gross_weight - weight1
				add_data("in_out", {
					"idAccess": last_pesata.data_assigned.accessId,
					"idMaterial": id_material,
					"idWeight1": last_in_out.idWeight2,
					"idWeight2": weighing_stored_db["id"],
					"net_weight": net_weight,
				})
			else:
				add_data("in_out", {
					"idAccess": last_pesata.data_assigned.accessId,
					"idMaterial": id_material,
					"idWeight1": weighing_stored_db["id"] if tare == 0 else None,
					"idWeight2": weighing_stored_db["id"] if tare > 0 else None,
					"net_weight": net_weight if tare > 0 else None
				})
			############################
			# RECUPERO L'ACCESSO CON IL NUOVO IN-OUT CREATO
			access = get_access_by_id(last_pesata.data_assigned.accessId)
			last_in_out = access.in_out[-1]
			len_in_out = len(access.in_out)
			is_test = access.type == TypeAccess.TEST
			is_to_close = len_in_out == access.number_in_out and last_in_out.idWeight2 or is_test
			last_in_out.access = access
   			############################
			# CREO L'IN-OUT SUCCESSIVO PER L'ASSEGNAZIONE DEL MATERIALE SE L'ACCESSO NON E' STATO CHIUSO E HA PIU' DI UNA OPERAZIONE
			# if tare == 0 and not is_to_close and last_in_out.idWeight2 and not is_test:
			# 	add_data("in_out", {
			# 		"idAccess": access.id,
			# 		"idWeight1": last_in_out.idWeight2
			# 	})
			############################
			# AGGIORNAMENTO FINALE DELLO STATO DELL'ACCESSO
			changed = {
				"status": AccessStatus.CLOSED if is_to_close else AccessStatus.ENTERED,
				"hidden": False
			}
			if is_to_close:
				changed["badge"] = ""
			updated_access = update_data("access", last_pesata.data_assigned.accessId, changed)
			access_data_json = Access(**updated_access).json()
			user_data_json = User(**user).json()
			asyncio.run(self.broadcastUpdateAnagrafic("access", {"weighing": access_data_json}))
			last_pesata.data_assigned.accessId = access_data_json
			last_pesata.data_assigned.userId = user_data_json
			############################
			# RIMUOVE TUTTI I DATA IN ESECUZIONE E L'ID SELEZIONATO SULLA DASHBAORD
			self.deleteData(instance_name=instance_name, weigher_name=weigher_name)
			threading.Thread(target=self.Callback_DataInExecution, args=(instance_name, weigher_name)).start()
			############################
			# RECUPERA TUTTI I DATI UTILI ALLA STAMPA DEL REPORT
			printer_name = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["printer_name"]
			number_of_prints = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["number_of_prints"]
			reports_dir = utils.base_path_applications / lb_config.g_config["app_api"]["path_content"]  / "report"
			report_in = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["events"]["weighing"]["report"]["in"]
			report_out = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["events"]["weighing"]["report"]["out"]
			generate_report = report_out if tare > 0 or last_in_out.idWeight2 else report_in
			path_pdf = f"{base_path}/{lb_config.g_config['app_api']['path_pdf']}"
			name_file, variables, report = get_data_variables(last_in_out)
			# MANDA IN STAMPA I DATI RELATIVI ALLA PESATA
			if generate_report and report:
				html = generate_html_report(reports_dir, report, v=variables.dict())
				pdf = printer.generate_pdf_from_html(html_content=html)
				if pdf:
					job_id, message1, message2 = printer.print_pdf(pdf_bytes=pdf, printer_name=printer_name, number_of_prints=number_of_prints)
					# SALVA COPIA PDF
					if path_pdf:
						save_file_dir(path_pdf, name_file, pdf)
			csv_in = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["events"]["weighing"]["csv"]["in"]
			csv_out = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["events"]["weighing"]["csv"]["out"]
			generate_csv = csv_out if tare > 0 or last_in_out.idWeight2 else csv_in
			path_csv = f"{base_path}/{lb_config.g_config['app_api']['path_csv']}"
			if generate_csv and path_csv:
				# SALVA I DATI DELLA PESATA IN UN FILE CSV
				csv = generate_csv_report(variables)
				if csv:
					save_file_dir(path_csv, name_file.replace(".pdf", ".csv"), csv)
			# APRE E CHIUDE I RELE'
			if weighing_stored_db:
				i = 1
				for cam in lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["events"]["weighing"]["cams"]:
					if cam["active"]:
						image_captured_details = capture_camera_image(camera_url=cam["picture"], timeout=5)
						if image_captured_details["image"]:
							base_folder_path = f"{base_path}/{lb_config.g_config['app_api']['path_img']}"
							sub_folder_path = structure_folder_rule()
							file_name = f"{i}_{last_pesata.weight_executed.pid}.png"
							save_bytes_to_file(image_captured_details["image"], file_name, f"{base_folder_path}{sub_folder_path}")
							add_data("weighing_picture", {"path_name": f"{sub_folder_path}/{file_name}", "idWeighing": weighing_stored_db["id"]})
							i = i + 1
				for rele in lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["events"]["weighing"]["set_rele"]:
					modope = "CLOSERELE" if rele["set"] == 0 else "OPENRELE"
					rele_status = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["rele"][rele["rele"]]
					r = md_weigher.module_weigher.setModope(instance_name=instance_name, weigher_name=weigher_name, modope=modope, port_rele=(rele["rele"], rele_status))
					lb_log.warning(r)
		elif not last_pesata.weight_executed.executed and last_pesata.data_assigned.accessId and access.hidden is True:
			# SE LA PESATA NON E' STATA ESEGUITA CORRETTAMENTE ELIMINA L'ACCESSO
			delete_data("access", last_pesata.data_assigned.accessId)
		# FUNZIONE UTILE PER ELIMINARE I DATI IN ESECUZIONE E L'ID SELEZIONATO DOPO UN PESATA AUTOMATICA NON RIUSCITA
		if not last_pesata.weight_executed.executed and len(access.in_out) == 0 and access.hidden is False:
			# SE LA PESATA NON E' STATA ESEGUITA CORRETTAMENTE E NON C'E' NESSUN IN-OUT ELIMINA I DATI IN ESECUZIONE
			self.deleteData(instance_name=instance_name, weigher_name=weigher_name)
		# AVVISA GLI UTENTI COLLEGATI ALLA DASHBOARD CHE HA FINITO DI EFFETTUARE IL PROCESSO DI PESATURA CON IL RELATIVO MESSAGIO
		weight = last_pesata.dict()
		asyncio.run(weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(weight))
		for instance in weighers_data:
			for weigher in weighers_data[instance]:
				weight = {"access": {}}
				asyncio.run(weighers_data[instance][weigher]["sockets"].manager_realtime.broadcast(weight))

	def Callback_WeighingTerminal(self, instance_name: str, weigher_name: str, weight_terminal: WeightTerminal):
		if lb_config.g_config["app_api"]["use_recordings"]:
			id = None
			weighing_terminal = None
			if weight_terminal.type == "2":
				weighing_terminal = get_data_by_attributes("weighing-terminal", {
					"id_terminal": weight_terminal.id,
					"pid1": weight_terminal.pid1
				})
				id = weighing_terminal["id"] if weighing_terminal else None
			if not id:
				data = add_data("weighing-terminal", {
					"id_terminal": weight_terminal.id or None,
					"bil": weight_terminal.bil or None,
					"badge": weight_terminal.badge or None,
					"plate": weight_terminal.plate or None,
					"customer": weight_terminal.customer or None,
					"supplier": weight_terminal.supplier or None,
					"material": weight_terminal.material or None,
					"notes1": weight_terminal.notes1 or None,
					"notes2": weight_terminal.notes2 or None,
					"datetime1": datetime.strptime(f"{weight_terminal.date1} {weight_terminal.time1}", "%d/%m/%Y %H:%M") if weight_terminal.date1 and weight_terminal.time1 else None,
					"date1": datetime.strptime(weight_terminal.date1, "%d/%m/%Y").date() if weight_terminal.date1 else None,
					"time1": datetime.strptime(weight_terminal.time1, "%H:%M").time().strftime("%H:%M") if weight_terminal.time1 else None,
					"datetime2": datetime.strptime(f"{weight_terminal.date2} {weight_terminal.time2}", "%d/%m/%Y %H:%M") if weight_terminal.date2 and weight_terminal.time2 else None,
					"date2": datetime.strptime(weight_terminal.date2, "%d/%m/%Y").date() if weight_terminal.date2 else None,
					"time2": datetime.strptime(weight_terminal.time2, "%H:%M").time().strftime("%H:%M") if weight_terminal.time2 else None,
					"prog1": weight_terminal.prog1 or None,
					"prog2": weight_terminal.prog2 or None,
					"pid1": weight_terminal.pid1 or None,
					"pid2": weight_terminal.pid2 or None,
					"weight1": float(weight_terminal.weight1) if weight_terminal.weight1 and ("," in weight_terminal.weight1 or "." in weight_terminal.weight1) else int(weight_terminal.weight1) if weight_terminal.weight1 else None,
					"weight2": float(weight_terminal.weight2) if weight_terminal.weight2 and ("," in weight_terminal.weight2 or "." in weight_terminal.weight2) else int(weight_terminal.weight2) if weight_terminal.weight2 else None,
					"net_weight": float(weight_terminal.net_weight) if weight_terminal.net_weight and ("," in weight_terminal.net_weight or "." in weight_terminal.net_weight) else int(weight_terminal.net_weight) if weight_terminal.net_weight else None,
				})
				del data["datetime1"]
				del data["datetime2"]
				del data["date_created"]
				asyncio.run(self.broadcastAddAnagrafic("weighing-terminal", data))
			else:
				update_weighing_data = {
					"type": weight_terminal.type,
					"notes2": weight_terminal.notes2 or None,
					"datetime2": datetime.strptime(f"{weight_terminal.date2} {weight_terminal.time2}", "%d/%m/%Y %H:%M") if weight_terminal.date2 and weight_terminal.time2 else None,
					"date2": datetime.strptime(weight_terminal.date2, "%d/%m/%Y").date() if weight_terminal.date2 else None,
					"time2": datetime.strptime(weight_terminal.time2, "%H:%M").time().strftime("%H:%M") if weight_terminal.time2 else None,
					"prog2": weight_terminal.prog2 or None,
					"pid2": weight_terminal.pid2 or None,
					"weight2": float(weight_terminal.weight2) if weight_terminal.weight2 and ("," in weight_terminal.weight2 or "." in weight_terminal.weight2) else int(weight_terminal.weight2) if weight_terminal.weight2 else None,
					"net_weight": float(weight_terminal.net_weight) if weight_terminal.net_weight and ("," in weight_terminal.net_weight or "." in weight_terminal.net_weight) else int(weight_terminal.net_weight) if weight_terminal.net_weight else None,
				}
				if weight_terminal.badge and weight_terminal.badge != weighing_terminal["badge"]:
					update_weighing_data["badge"] = weight_terminal.badge
				if weight_terminal.plate and weight_terminal.plate != weighing_terminal["plate"]:
					update_weighing_data["plate"] = weight_terminal.plate
				if weight_terminal.customer and weight_terminal.customer != weighing_terminal["customer"]:
					update_weighing_data["customer"] = weight_terminal.customer
				if weight_terminal.supplier and weight_terminal.supplier != weighing_terminal["supplier"]:
					update_weighing_data["supplier"] = weight_terminal.supplier
				if weight_terminal.material and weight_terminal.material != weighing_terminal["material"]:
					update_weighing_data["material"] = weight_terminal.material
				if weight_terminal.notes1 and weight_terminal.notes1 != weighing_terminal["notes1"]:
					update_weighing_data["notes1"] = weight_terminal.notes1
				if weight_terminal.notes2 and weight_terminal.notes2 != weighing_terminal["notes2"]:
					update_weighing_data["notes2"] = weight_terminal.notes2
				data = update_data("weighing-terminal", id, update_weighing_data)
				del data["datetime1"]
				del data["datetime2"]
				del data["date_created"]
				asyncio.run(self.broadcastUpdateAnagrafic("weighing-terminal", data))
			message = {
				"message": f"Pesata eseguita da terminale! Pid: {weight_terminal.pid2 or weight_terminal.pid1}"
			}
			asyncio.run(weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(message))

	def Callback_TarePTareZero(self, instance_name: str, weigher_name: str, ok_value: str):
		asyncio.run(weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast({"command_executed": ok_value}))

	def Callback_DataInExecution(self, instance_name, weigher_name):
		try:
			if asyncio.get_event_loop().is_running():
				asyncio.create_task(weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(self.getData(instance_name=instance_name, weigher_name=weigher_name)))
			else:
				loop = asyncio.get_event_loop()
				loop.run_until_complete(weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(self.getData(instance_name=instance_name, weigher_name=weigher_name)))
		except Exception:
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
		result = {key: value}
		lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][weigher_name]["rele"][key] = value
		lb_config.saveconfig()
		try:
			if asyncio.get_event_loop().is_running():
				asyncio.create_task(weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(result))
				asyncio.create_task(weighers_data[instance_name][weigher_name]["sockets"].manager_diagnostic.broadcast(result))
			else:
				loop = asyncio.get_event_loop()
				loop.run_until_complete(weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(result))
				loop.run_until_complete(weighers_data[instance_name][weigher_name]["sockets"].manager_diagnostic.broadcast(result))
		except RuntimeError:
			asyncio.run(weighers_data[instance_name][weigher_name]["sockets"].manager_realtime.broadcast(result))
			asyncio.run(weighers_data[instance_name][weigher_name]["sockets"].manager_diagnostic.broadcast(result))
   
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