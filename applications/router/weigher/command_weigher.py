from fastapi import APIRouter, Depends, WebSocket, HTTPException, Request
from applications.utils.utils_weigher import InstanceNameWeigherDTO, get_query_params_name_node
import modules.md_weigher.md_weigher as md_weigher
from typing import Optional
import asyncio
from applications.router.weigher.data import DataRouter
import libs.lb_config as lb_config
from applications.router.weigher.manager_weighers_data import weighers_data
from applications.router.anagrafic.access import AccessRouter
from modules.md_database.md_database import TypeAccess, AccessStatus
from modules.md_database.functions.get_access_by_id import get_access_by_id
from modules.md_database.interfaces.access import AddAccessDTO, SetAccessDTO
from applications.router.weigher.dto import IdentifyDTO, DataDTO, DataToStoreDTO
from modules.md_database.functions.get_access_by_identify_if_uncomplete import get_access_by_identify_if_uncomplete
from modules.md_database.functions.add_data import add_data
from modules.md_database.functions.get_in_out_by_id import get_in_out_by_id
from applications.middleware.auth import get_user
import threading
from applications.router.weigher.manager_weighers_data import weighers_data
from applications.router.weigher.types import DataAssignedDTO
import datetime as dt
import applications.utils.utils as utils
from applications.utils.utils_report import get_data_variables, generate_html_report, save_file_dir
from libs.lb_printer import printer
from applications.router.weigher.types import Data

class CommandWeigherRouter(DataRouter, AccessRouter):
	def __init__(self):
		super().__init__()

		self.router_action_weigher = APIRouter()
		self.url_weighing_auto = '/weighing/auto'
		self.automatic_weighing_process = []

		self.router_action_weigher.add_api_route('/realtime', self.StartRealtime, methods=['GET'])
		self.router_action_weigher.add_api_route('/diagnostic', self.StartDiagnostic, methods=['GET'])
		self.router_action_weigher.add_api_route('/stop-all-command', self.StopAllCommand, methods=['GET'])
		self.router_action_weigher.add_api_route('/weighing-without-pid', self.WeighingWithoutPid, methods=['POST'])
		self.router_action_weigher.add_api_route('/print', self.Generic, methods=['GET'])
		self.router_action_weigher.add_api_route('/in', self.Weight1, methods=['POST'])
		self.router_action_weigher.add_api_route('/out', self.Weight2, methods=['POST'])
		self.router_action_weigher.add_api_route(self.url_weighing_auto, self.WeighingByIdentify, methods=['POST'])
		self.router_action_weigher.add_api_route('/tare', self.Tare, methods=['GET'])
		self.router_action_weigher.add_api_route('/tare/preset', self.PresetTare, methods=['GET'])
		self.router_action_weigher.add_api_route('/zero', self.Zero, methods=['GET'])
		self.router_action_weigher.add_api_route('/rele', self.Rele, methods=['GET'])

		self.router_action_weigher.add_api_websocket_route('/realtime', self.websocket_endpoint_realtime)
		self.router_action_weigher.add_api_websocket_route('/diagnostic', self.websocket_endpoint_diagnostic)

	async def StartRealtime(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		status_modope, command_executed, error_message = md_weigher.module_weigher.setModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name, modope="REALTIME")

		return {
			"instance": instance,
			"command_details": {
				"status_modope": status_modope,
				"command_executed": command_executed,
				"error_message": error_message
			}
		}

	async def StartDiagnostic(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		status_modope, command_executed, error_message = md_weigher.module_weigher.setModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name, modope="DIAGNOSTIC")
		return {
			"instance": instance,
			"command_details": {
				"status_modope": status_modope,
				"command_executed": command_executed,
				"error_message": error_message
			}
		}

	async def StopAllCommand(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		status_modope, command_executed, error_message = md_weigher.module_weigher.setModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name, modope="OK")
		return {
			"instance": instance,
			"command_details": {
				"status_modope": status_modope,
				"command_executed": command_executed,
				"error_message": error_message
			}
		}

	async def WeighingWithoutPid(self, request: Request, body: DataToStoreDTO, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node), tare: Optional[int] = None):
		status_modope, command_executed, error_message = 500, False, ""
		realtime = md_weigher.module_weigher.getRealtime(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
		status = realtime.status
		current_tare = None
		if realtime.tare:
			current_tare = float(realtime.tare.replace("PT", "").replace(" ",  "")) if "." in realtime.tare or "," in realtime.tare else int(realtime.tare.replace("PT", "").replace(" ",  ""))
		gross_weight = None
		if realtime.gross_weight:
			gross_weight = float(realtime.gross_weight) if "." in realtime.gross_weight or "," in realtime.gross_weight else int(realtime.gross_weight)
		net_weight = None
		if realtime.net_weight:
			net_weight = float(realtime.net_weight) if "." in realtime.net_weight or "," in realtime.net_weight else int(realtime.net_weight)
		instance_weigher = md_weigher.module_weigher.getInstanceWeigher(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
		firmware = instance_weigher[instance.instance_name]["terminal_data"]["firmware"]
		model_name = instance_weigher[instance.instance_name]["terminal_data"]["model_name"]
		serial_number = instance_weigher[instance.instance_name]["terminal_data"]["serial_number"]
		max_weight = instance_weigher[instance.instance_name]["max_weight"]
		min_weight = instance_weigher[instance.instance_name]["min_weight"]
		division = instance_weigher[instance.instance_name]["division"]
		take_of_weight_on_startup = instance_weigher[instance.instance_name]["take_of_weight_on_startup"]
		take_of_weight_before_weighing = instance_weigher[instance.instance_name]["take_of_weight_before_weighing"]
		if status != "ST":
			error_message = "Il peso non è stabile"
		elif int(realtime.gross_weight) < min_weight:
			error_message = f"Il peso è inferiore a {min_weight} kg"
		elif int(realtime.gross_weight) > max_weight:
			error_message = f"Il peso è maggiore di {max_weight} kg"
		elif tare and str(current_tare).isdigit() and current_tare > 0:
			error_message = "Non puoi passare la tara perchè è già impostata sulla pesa"
		elif tare > int(realtime.gross_weight):
			error_message = "Non puoi assegnare un tara più grande del peso lordo"
		if error_message:
			raise HTTPException(status_code=400, detail=error_message)
		access = await self.addAccess(request=None, body=AddAccessDTO(**{
			**body.dict(), 
			"number_in_out": 1,
			"type": TypeAccess.MANUALLY.name,
		}), status=AccessStatus.CLOSED.name)
		weighing_stored_db = add_data("weighing", {
			"date": dt.datetime.now(),
			"weigher": instance.weigher_name,
			"weigher_serial_number": serial_number,
			"pid": None,
			"tare": tare or current_tare,
			"is_preset_tare": True,
			"weight": gross_weight,
			"log": None,
			"idUser": request.state.user.id,
			"idOperator": None,
		})
		in_out = add_data("in_out", {
			"idAccess": access.id,
			"idMaterial": None,
			"idWeight1": None,
			"idWeight2": weighing_stored_db["id"],
			"net_weight": net_weight - tare if tare else net_weight
		})
		await self.setAccess(request=None, id=access.id, body=SetAccessDTO(**{"material": body.material.dict(), "operator2": body.operator.dict()}), idInOut=in_out["id"])
		last_in_out = get_in_out_by_id(in_out["id"])
		# RECUPERA TUTTI I DATI UTILI ALLA STAMPA DEL REPORT
		printer_name = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["printer_name"]
		number_of_prints = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["number_of_prints"]
		reports_dir = utils.base_path_applications / lb_config.g_config["app_api"]["path_content"]  / "report"
		print_in = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"]["weighing"]["report"]["in"]
		print_out = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["events"]["weighing"]["report"]["out"]
		print = print_out if tare > 0 or last_in_out.idWeight2 else print_in
		path_pdf = lb_config.g_config["app_api"]["path_pdf"]
		name_file, variables, report = get_data_variables(last_in_out)
		# MANDA IN STAMPA I DATI RELATIVI ALLA PESATA
		if report:
			html = generate_html_report(reports_dir, report, v=variables.dict())
			pdf = printer.generate_pdf_from_html(html_content=html)
			if print:
				job_id, message1, message2 = printer.print_pdf(pdf_bytes=pdf, printer_name=printer_name, number_of_prints=number_of_prints)
			# SALVA COPIA PDF
			if path_pdf and pdf:
				save_file_dir(path_pdf, name_file, pdf)
		return {
			"instance": instance,
			"in_out": in_out
		}

	async def Generic(self, request: Request, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		status_modope, command_executed, error_message = 500, False, ""
		access_id = None
		if weighers_data[instance.instance_name][instance.weigher_name]["data"]["id_selected"]["id"]:
			error_message = "Deselezionare l'id per effettuare la pesata di prova."
		else:
			access = await self.addAccess(request=None, body=AddAccessDTO(**{
				**weighers_data[instance.instance_name][instance.weigher_name]["data"]["data_in_execution"], 
				"number_in_out": 1,
				"type": "TEST",
				"hidden": True
			}))
			data_assigned = DataAssignedDTO(**{"accessId": access.id, "userId": request.state.user.id})
			status_modope, command_executed, error_message = md_weigher.module_weigher.setModope(
				instance_name=instance.instance_name, 
				weigher_name=instance.weigher_name, 
				modope="WEIGHING", 
			  	data_assigned=data_assigned
			)
			access_id = access.id
			if error_message:
				await self.deleteAccess(request=None, id=access.id)
		return {
			"instance": instance,
			"command_details": {
				"status_modope": status_modope,
				"command_executed": command_executed,
				"error_message": error_message
			},
			"access_id": access_id
		}

	async def Weight1(self, request: Request, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		status_modope, command_executed, error_message = 500, False, ""
		tare = md_weigher.module_weigher.getRealtime(instance_name=instance.instance_name, weigher_name=instance.weigher_name).tare
		weigher = md_weigher.module_weigher.getInstanceWeigher(instance_name=instance.instance_name, weigher_name=instance.weigher_name)[instance.instance_name]
		take_of_weight_on_startup = weigher["take_of_weight_on_startup"]
		take_of_weight_before_weighing = weigher["take_of_weight_before_weighing"]
		current_id = weighers_data[instance.instance_name][instance.weigher_name]["data"]["id_selected"]["id"]
		access = None
		status_modope = None
		command_executed = None
		error_message = None
		if take_of_weight_on_startup is True:
			error_message = "Scaricare la pesa dopo l'avvio del programma"
		if take_of_weight_before_weighing is True:
			error_message = "Scaricare la pesa prima di eseguire nuova pesata"
		if current_id:
			access = get_access_by_id(current_id)
		if access and len(access.in_out) > 0 and weighers_data[instance.instance_name][instance.weigher_name]["data"]["id_selected"]["weight1"] is not None:
			error_message = "Il mezzo ha già effettuato l'entrata."
		elif tare != "0":
			error_message = "Eliminare la tara per effettuare l'entrata del mezzo."
		elif not access:
			access = await self.addAccess(request=None, body=AddAccessDTO(**{
					**weighers_data[instance.instance_name][instance.weigher_name]["data"]["data_in_execution"], 
				 	"number_in_out": 1,
				  	"type": "MANUALLY",
				   	"hidden": True
				}))
			current_id = access.id
		if not error_message:
			data_assigned = DataAssignedDTO(**{"accessId": current_id, "userId": request.state.user.id})
			status_modope, command_executed, error_message = md_weigher.module_weigher.setModope(
				instance_name=instance.instance_name, 
				weigher_name=instance.weigher_name, 
				modope="WEIGHING", 
				data_assigned=data_assigned
			)
			if error_message and access.hidden is True:
				await self.deleteAccess(request=None, id=current_id)
		return {
			"instance": instance,
			"command_details": {
				"status_modope": status_modope,
				"command_executed": command_executed,
				"error_message": error_message
			},
			"access_id": current_id
		}

	async def Weight2(self, request: Request, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		status_modope, command_executed, error_message = 500, False, ""
		tare = md_weigher.module_weigher.getRealtime(instance_name=instance.instance_name, weigher_name=instance.weigher_name).tare
		weigher = md_weigher.module_weigher.getInstanceWeigher(instance_name=instance.instance_name, weigher_name=instance.weigher_name)[instance.instance_name]
		take_of_weight_on_startup = weigher["take_of_weight_on_startup"]
		take_of_weight_before_weighing = weigher["take_of_weight_before_weighing"]
		idAccess = weighers_data[instance.instance_name][instance.weigher_name]["data"]["id_selected"]["id"]
		access = None
		if take_of_weight_on_startup is True:
			error_message = "Scaricare la pesa dopo l'avvio del programma"
		elif take_of_weight_before_weighing is True:
			error_message = "Scaricare la pesa prima di eseguire nuova pesata"
		else:
			if idAccess:
				access = get_access_by_id(idAccess)
			just_created = False
			if access:
				if len(access.in_out) == 0 and access.number_in_out is not None and tare != "0":
					error_message = "Non è possibile effettuare pesate con tara negli accessi multipli."
				if len(access.in_out) > 0 and access.number_in_out is not None and access.in_out[-1].idWeight1 and access.in_out[-1].idWeight2 and tare != "0":
					error_message = "Rimuovere la tara per effettuare l'uscita del mezzo tramite id."
				elif len(access.in_out) == 0 and tare == "0":
					error_message = "Inserire una tara o effettuare una entrata prima di effettuare l'uscita del mezzo tramite id."
				if len(access.in_out) > 0 and weighers_data[instance.instance_name][instance.weigher_name]["data"]["id_selected"]["weight1"] is None and tare == "0":
					error_message = "E' necessario effettuare l'entrata del mezzo"
			if not access:
				if tare == "0":
					error_message = "Nessun id impostato per effettuare l'uscita."
				else:
					access = await self.addAccess(request=None, body=AddAccessDTO(**{
						**weighers_data[instance.instance_name][instance.weigher_name]["data"]["data_in_execution"], 
						"number_in_out": 1,
					  	"type": "MANUALLY",
						"hidden": True
					}))
					idAccess = access.id
					just_created = True
			if idAccess and not error_message:
				data_assigned = DataAssignedDTO(**{"accessId": idAccess, "userId": request.state.user.id})
				status_modope, command_executed, error_message = md_weigher.module_weigher.setModope(
					instance_name=instance.instance_name, 
					weigher_name=instance.weigher_name, 
					modope="WEIGHING", 
					data_assigned=data_assigned)
			if error_message and just_created:
				await self.deleteAccess(request=None, id=idAccess)
		return {
			"instance": instance,
			"command_details": {
				"status_modope": status_modope,
				"command_executed": command_executed,
				"error_message": error_message
			},
			"access_id": idAccess
		}

	async def WeighingByIdentify(self, request: Request, identify_dto: IdentifyDTO, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node), token: str = None):
		if request is not None:
			response = get_user(token=token)
			if hasattr(response, "status_code"):
				return response
			request.state.user = response
		mode = lb_config.g_config["app_api"]["mode"]
		error_message = None
		success_message = None
		access = None
		proc = {
			"instance_name": instance.instance_name,
			"weigher_name": instance.weigher_name,
			"identify": identify_dto.identify
		}
		cam_message = f'"{identify_dto.identify}"'
		if request is not None:
			cam_message = cam_message + f" ricevuto da {request.client.host}"
		else:
			cam_message = cam_message + f" ricevuto da terminale"
		if len(identify_dto.identify) < 5:
			error_message = "L'identificativo deve essere di almeno 5 caratteri"
		else:
			await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"cam_message": cam_message})
			existing_proc = next(
				(p for p in self.automatic_weighing_process if p["instance_name"] == instance.instance_name and p["weigher_name"] == instance.weigher_name),
				None
			)
			# current_data = await self.GetData(instance=instance)
			if mode == "MANUALLY":
				error_message = f"Modalità automatica disattiva. Tentativo di pesatura {cam_message} bloccato"
			elif existing_proc:
				error_message = f"Pesatura automatica già in esecuzione sulla pesa '{instance.weigher_name}' con identify '{existing_proc['identify']}'."
			# elif Data(**{}) != Data(**current_data):
			# 	error_message = f"Sulla pesa '{instance.weigher_name}' sono già presenti dati in esecuzione. Attendi che gli operatori completino le operazioni manuali prima di avviare una nuova pesatura automatica."
			else:
				weigher = md_weigher.module_weigher.getInstanceWeigher(instance_name=instance.instance_name, weigher_name=instance.weigher_name)[instance.instance_name]
				division = weigher["division"]
				take_of_weight_on_startup = weigher["take_of_weight_on_startup"]
				take_of_weight_before_weighing = weigher["take_of_weight_before_weighing"]
				if take_of_weight_on_startup is True:
					error_message = "Scaricare la pesa dopo l'avvio del programma"
				elif take_of_weight_before_weighing is True:
					error_message = "Scaricare la pesa prima di eseguire nuova pesata"
				else:
					access = get_access_by_identify_if_uncomplete(identify=identify_dto.identify)
					realtime = md_weigher.module_weigher.getRealtime(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
					min_weight = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["min_weight"]
					if realtime.gross_weight == "" or realtime.gross_weight != "" and float(realtime.gross_weight) < min_weight:
						error_message = f"Il peso deve essere maggiore di {min_weight} kg"
					elif access:
						current_weigher_data = self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
						if current_weigher_data["id_selected"]["id"] != access["id"]:
							await self.DeleteData(instance=instance)
							try:
								if access["type"].name == TypeAccess.RESERVATION.name and access["number_in_out"] is not None and realtime.tare != "0":
									error_message = "Non è possibile effettuare pesate con tara negli accessi multipli."
								else:
									data_dto = DataDTO(**{"id_selected": {"id": access["id"]}})
									need_to_confirm = True if mode == "SEMIAUTOMATIC" else False
									await self.SetData(request=None, data_dto=data_dto, instance=instance, need_to_confirm=need_to_confirm)
							except Exception as e:
								error_message = e.detail
						if not error_message:
							self.automatic_weighing_process.append(proc)
							if mode == "AUTOMATIC":
								async def handleAutomatic():
									data = weighers_data[instance.instance_name][instance.weigher_name]["data"]
									tare = data["data_in_execution"]["vehicle"]["tare"]
									weight1 = data["id_selected"]["weight1"]
									timeout = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["connection"]["timeout"]
									time_between_actions = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["time_between_actions"]
									stable = 0
									while True:
										await asyncio.sleep(time_between_actions)
										timeout = timeout - time_between_actions
										current_weigher_data = self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
										modope = md_weigher.module_weigher.getModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
										current_modope = md_weigher.module_weigher.getCurrentModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
										realtime = md_weigher.module_weigher.getRealtime(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
										current_tare = realtime.tare.replace("PT", "").replace(" ",  "")
										m = modope if request is not None else current_modope
										if modope != "PRESETTARE" and current_modope != "PRESETTARE":
											if current_weigher_data["id_selected"]["id"] != access["id"]:
												error_message = f"Pesatura automatica interrotta. Accesso con '{identify_dto.identify}' deselezionato."
												await self.DeleteData(instance=instance)
												await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"error_message": error_message})
												break
											if weight1 is None and current_tare != "" and tare is not None and abs(float(current_tare) - float(tare)) > division:
												if current_tare == "0":
													if timeout >= 0:
														message = f"Impostando la tara per la pesatura automatica."
														await self.DeleteData(instance=instance)
														await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"message": message})
												elif timeout >= 0:
													error_message = f"Pesatura automatica interrotta. La tara di {tare} kg non è stata impostata correttamente."
													await self.DeleteData(instance=instance)
													await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"error_message": error_message})
													break
											elif realtime.gross_weight == "" or float(realtime.gross_weight) != "" and float(realtime.gross_weight) < min_weight:
												error_message = f"Pesatura automatica interrotta. Il peso deve essere maggiore di {min_weight} kg."
												await self.DeleteData(instance=instance)
												await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"error_message": error_message})
												break
											elif realtime.gross_weight != "" and float(realtime.gross_weight) >= min_weight:
												if realtime.status == "ST":
													if stable == 3:
														data_assigned = DataAssignedDTO(**{"accessId": access["id"], "userId": request.state.user.id if request else None})
														status_modope, command_executed, error_message = md_weigher.module_weigher.setModope(
															instance_name=instance.instance_name, 
															weigher_name=instance.weigher_name, 
															modope="WEIGHING", 
															data_assigned=data_assigned)
														if error_message:
															error_message = f"Errore nella pesatura automatica: {error_message}. Ritento."
															await self.DeleteData(instance=instance)
															await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"error_message": error_message})
														if command_executed:
															await self.DeleteData(instance=instance)
															break
													else:
														stable = stable + 1
												else:
													stable = 0
									# Rimuovi il processo dalla lista in modo sicuro
									self.automatic_weighing_process = [
										p for p in self.automatic_weighing_process
										if not (
											p["instance_name"] == instance.instance_name and
											p["weigher_name"] == instance.weigher_name and
											p["identify"] == identify_dto.identify
										)
									]
								threading.Thread(target=lambda: asyncio.run(handleAutomatic())).start()
								success_message = "Pesatura automatica presa in carico."
							elif mode == "SEMIAUTOMATIC":
								async def handleSemiautomatic():
									data = weighers_data[instance.instance_name][instance.weigher_name]["data"]
									tare = data["data_in_execution"]["vehicle"]["tare"]
									weight1 = data["id_selected"]["weight1"]
									timeout = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["connection"]["timeout"]
									time_between_actions = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["time_between_actions"]
									stable = 0
									while True:
										await asyncio.sleep(time_between_actions)
										timeout = timeout - time_between_actions
										current_weigher_data = self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
										modope = md_weigher.module_weigher.getModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
										current_modope = md_weigher.module_weigher.getCurrentModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
										realtime = md_weigher.module_weigher.getRealtime(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
										current_tare = realtime.tare.replace("PT", "").replace(" ",  "")
										m = modope if request is not None else current_modope

										if modope != "PRESETTARE" and current_modope != "PRESETTARE":
											if current_weigher_data["id_selected"]["id"] != access["id"]:
												break
											if weight1 is None and current_tare != "" and tare is not None and abs(float(current_tare) - float(tare)) > division:
												if current_tare == "0":
													if timeout >= 0:
														message = f"Impostando la tara per la pesatura semiautomatica."
														await self.DeleteData(instance=instance)
														await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"message": message})
												elif timeout >= 0:
													error_message = f"Pesatura semiautomatica interrotta. La tara di {tare} kg non è stata impostata correttamente."
													await self.DeleteData(instance=instance)
													await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"error_message": error_message})
													break
											elif realtime.gross_weight == "" or float(realtime.gross_weight) != "" and float(realtime.gross_weight) < min_weight:
												error_message = f"Pesatura semiautomatica interrotta. Il peso deve essere maggiore di {min_weight} kg."
												await self.DeleteData(instance=instance)
												await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"error_message": error_message})
												break
											elif realtime.gross_weight != "" and float(realtime.gross_weight) >= min_weight:
												if realtime.status == "ST":
													stable += 1
												else:
													stable = 0
									# Rimuovi il processo dalla lista in modo sicuro
									self.automatic_weighing_process = [
										p for p in self.automatic_weighing_process
										if not (
											p["instance_name"] == instance.instance_name and
											p["weigher_name"] == instance.weigher_name and
											p["identify"] == identify_dto.identify
										)
									]
								threading.Thread(target=lambda: asyncio.run(handleSemiautomatic())).start()
								error_message = "Pesatura semiautomatica in attesa di conferma dall'operatore."
					else:
						error_message = f"Accesso con '{identify_dto.identify}' non esistente."
		if error_message:
			error_message = cam_message + f" - Errore: {error_message}"
			await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"cam_message": error_message})
		elif success_message:
			success_message = cam_message + f" - {success_message}"
			await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"cam_message": success_message})
		return {
			"message": error_message or success_message,
			"access_id": access["id"] if access else None,
			"identify_dto": identify_dto
		}

	def Callback_WeighingByIdentify(self, instance_name: str, weigher_name: str, identify: str):
		instance = InstanceNameWeigherDTO(instance_name=instance_name, weigher_name=weigher_name)
		identify_dto = IdentifyDTO(identify=identify)

		def run_in_thread():
			asyncio.run(self.WeighingByIdentify(request=None, instance=instance, identify_dto=identify_dto))

		thread = threading.Thread(target=run_in_thread)
		thread.start()

	async def Tare(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		status_modope, command_executed, error_message = 500, False, ""
		data_id_selected = weighers_data[instance.instance_name][instance.weigher_name]["data"]["id_selected"]
		execution = True
		if data_id_selected["id"] and data_id_selected["weight1"]:
			error_message = "Non puoi effettuare la preset tara perchè il mezzo ha già effettuato una entrata."
			execution = False
		if execution:
			status_modope, command_executed, error_message = md_weigher.module_weigher.setModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name, modope="TARE")
		return {
			"instance": instance,
			"command_details": {
				"status_modope": status_modope,
				"command_executed": command_executed,
				"error_message": error_message
			}
		}

	async def PresetTare(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node), tare: Optional[int] = 0):
		status_modope, command_executed, error_message = 500, False, ""
		data_id_selected = weighers_data[instance.instance_name][instance.weigher_name]["data"]["id_selected"]
		execution = True
		if data_id_selected["id"] and data_id_selected["weight1"]:
			error_message = "Non puoi effettuare la preset tara perchè il mezzo ha già effettuato una entrata."
			execution = False
		if execution:
			status_modope, command_executed, error_message = md_weigher.module_weigher.setModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name, modope="PRESETTARE", presettare=tare)
		return {
			"instance": instance,
			"command_details": {
				"status_modope": status_modope,
				"command_executed": command_executed,
				"error_message": error_message
			}
		}

	async def Zero(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		status_modope, command_executed, error_message = md_weigher.module_weigher.setModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name, modope="ZERO")
		return {
			"instance": instance,
			"command_details": {
				"status_modope": status_modope,
				"command_executed": command_executed,
				"error_message": error_message
			}
		}

	async def Rele(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node), rele: Optional[str] = None):
		if not rele:
			raise HTTPException(status_code=400, detail="Need to insert a rele")
		reles = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["rele"].copy()
		if rele not in reles:
			raise HTTPException(status_code=400, detail="Rele doesn't exist in configuration")
		rele = (rele, lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["rele"][rele])
		modope = "OPENRELE" if rele[1] == 0 else "CLOSERELE"
		status_modope, command_executed, error_message = md_weigher.module_weigher.setModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name, modope=modope, port_rele=rele)
		return {
			"instance": instance,
			"command_details": {
				"status_modope": status_modope,
				"command_executed": command_executed,
				"error_message": error_message
			}
		}
  
	async def websocket_endpoint_realtime(self, websocket: WebSocket, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.connect(websocket)

		# Invia immediatamente uno stato iniziale al client per evitare N/A
		try:
			weigher = md_weigher.module_weigher.getInstanceWeigher(instance_name=instance.instance_name, weigher_name=instance.weigher_name)[instance.instance_name]
			status = weigher["status"]

			if status == 200:
				# Bilancia collegata - invia stato di caricamento
				await websocket.send_json({
					"status": "Caricamento...",
					"type": "--",
					"net_weight": "0",
					"gross_weight": "0",
					"tare": "0",
					"unite_measure": "kg",
					"potential_net_weight": None
				})
				# Imposta immediatamente il modope a REALTIME per ricevere dati subito
				modope_in_execution = md_weigher.module_weigher.getModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
				if modope_in_execution in ["OK", "DIAGNOSTIC"]:
					md_weigher.module_weigher.setModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name, modope="REALTIME")
			else:
				# Bilancia non collegata - invia errore
				connecting = md_weigher.module_weigher.getInstanceConnecting(instance_name=instance.instance_name)
				message = "Errore di connessione"
				if connecting:
					message = "Tentativo di connessione in corso..."
				if status in [305, 201]:
					message = "Errore di ricezione"
				await websocket.send_json({
					"status": message,
					"type": "--",
					"net_weight": "--",
					"gross_weight": "--",
					"tare": "--",
					"unite_measure": "--",
					"potential_net_weight": None
				})
		except Exception as e:
			# In caso di errore, invia uno stato di default
			await websocket.send_json({
				"status": "Inizializzazione...",
				"type": "--",
				"net_weight": "0",
				"gross_weight": "0",
				"tare": "0",
				"unite_measure": "kg",
				"potential_net_weight": None
			})

		while instance.instance_name in weighers_data and instance.weigher_name in weighers_data[instance.instance_name]:
			weigher = md_weigher.module_weigher.getInstanceWeigher(instance_name=instance.instance_name, weigher_name=instance.weigher_name)[instance.instance_name]
			status = weigher["status"]
			always_execute_realtime_in_undeground = weigher["always_execute_realtime_in_undeground"]
			modope_on_close = "REALTIME" if always_execute_realtime_in_undeground else "OK"
			if websocket not in weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.active_connections:
				if len(weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.active_connections) == 0:
					data = await self.GetData(instance=instance)
					if data["id_selected"]["need_to_confirm"] is False:
						await self.DeleteData(instance=instance)
					await self.StopAllCommand(instance=instance)
					md_weigher.module_weigher.setModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name, modope=modope_on_close)
				break
			if len(weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.active_connections) > 0:
				if status == 200:
					modope_in_execution = md_weigher.module_weigher.getModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
					if modope_in_execution in ["OK", "DIAGNOSTIC"]:
						if modope_in_execution == "DIAGNOSTIC":
							await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({
								"status":"Diagnostica in corso",
								"type":"--",
								"net_weight": "--",
								"gross_weight":"--",
								"tare":"--",
								"unite_measure": "--",
								"potential_net_weight": None
							})
						md_weigher.module_weigher.setModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name, modope="REALTIME")
				else:
					connecting = md_weigher.module_weigher.getInstanceConnecting(instance_name=instance.instance_name)
					message = "Errore di connessione"
					if connecting:
						message = "Tentativo di connessione in corso..."
					if status in [305, 201]:
						message = "Errore di ricezione"
					await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({
						"status": message,
						"type":"--",
						"net_weight": "--",
						"gross_weight":"--",
						"tare":"--",
						"unite_measure": "--",
						"potential_net_weight": None
					})
			else:
				data = await self.GetData(instance=instance)
				if data["id_selected"]["need_to_confirm"] is False:
					await self.DeleteData(instance=instance)
				await self.StopAllCommand(instance=instance)
				md_weigher.module_weigher.setModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name, modope=modope_on_close)
				break
			await asyncio.sleep(0.1)

	async def websocket_endpoint_diagnostic(self, websocket: WebSocket, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_diagnostic.connect(websocket)
		while instance.instance_name in weighers_data and instance.weigher_name in weighers_data[instance.instance_name]:
			weigher = md_weigher.module_weigher.getInstanceWeigher(instance_name=instance.instance_name, weigher_name=instance.weigher_name)[instance.instance_name]
			status = weigher["status"]
			diagnostic_has_priority_than_realtime = weigher["diagnostic_has_priority_than_realtime"]
			always_execute_realtime_in_undeground = weigher["always_execute_realtime_in_undeground"]
			modope_on_close = "REALTIME" if always_execute_realtime_in_undeground else "OK"
			if websocket not in weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_diagnostic.active_connections:
				if len(weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_diagnostic.active_connections) == 0:
					await self.StopAllCommand(instance=instance)
					md_weigher.module_weigher.setModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name, modope=modope_on_close)
				break
			if len(weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_diagnostic.active_connections) > 0:
				if status == 200:
					modope_in_execution = md_weigher.module_weigher.getModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
					if modope_in_execution in ["OK", "REALTIME"]:
						if modope_in_execution == "REALTIME" and not diagnostic_has_priority_than_realtime:
							await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_diagnostic.broadcast({
								"status": "Realtime in esecuzione"
							})
						md_weigher.module_weigher.setModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name, modope="DIAGNOSTIC")
				else:
					message = "Pesa scollegata"
					if status == 301:
						message = "Connessione non settata"
					elif status == 201:
						message = "Protocollo pesa non valido"
					await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_diagnostic.broadcast({
						"status": message
					})
			else:
				await self.StopAllCommand(instance=instance)
				md_weigher.module_weigher.setModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name, modope=modope_on_close)
				break
			await asyncio.sleep(1)