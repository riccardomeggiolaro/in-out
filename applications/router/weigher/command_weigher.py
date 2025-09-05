from fastapi import APIRouter, Depends, WebSocket, HTTPException, Request
from applications.utils.utils_weigher import InstanceNameWeigherDTO, get_query_params_name_node
import modules.md_weigher.md_weigher as md_weigher
from typing import Optional
import asyncio
from applications.router.weigher.data import DataRouter
import libs.lb_config as lb_config
from applications.router.weigher.manager_weighers_data import weighers_data
from applications.router.anagrafic.reservation import ReservationRouter
from modules.md_database.md_database import TypeReservation
from modules.md_database.functions.get_reservation_by_id import get_reservation_by_id
from modules.md_database.interfaces.reservation import AddReservationDTO, VehicleDataDTO
from applications.router.weigher.dto import IdentifyDTO, DataDTO
from modules.md_database.functions.get_reservation_by_plate_if_uncomplete import get_reservation_by_plate_if_uncomplete
from modules.md_database.functions.get_reservation_by_identify_if_uncomplete import get_reservation_by_identify_if_uncomplete
from modules.md_database.functions.get_data_by_attributes import get_data_by_attributes
from applications.middleware.auth import get_user
import libs.lb_log as lb_log
import threading

class CommandWeigherRouter(DataRouter, ReservationRouter):
	def __init__(self):
		super().__init__()

		self.router_action_weigher = APIRouter()
		self.url_weighing_auto = '/weighing/auto'
		self.automatic_weighing_process = []

		self.router_action_weigher.add_api_route('/realtime', self.StartRealtime, methods=['GET'])
		self.router_action_weigher.add_api_route('/diagnostic', self.StartDiagnostic, methods=['GET'])
		self.router_action_weigher.add_api_route('/stop-all-command', self.StopAllCommand, methods=['GET'])
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

	async def Generic(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		status_modope, command_executed, error_message = 500, False, ""
		reservation_id = None
		if lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"]["id_selected"]["id"]:
			error_message = "Deselezionare l'id per effettuare la pesata di prova."
		else:
			reservation = await self.addReservation(request=None, body=AddReservationDTO(**{
				**lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"]["data_in_execution"], 
				"number_in_out": 1,
				"type": "TEST",
				"hidden": True
			}))
			status_modope, command_executed, error_message = md_weigher.module_weigher.setModope(
				instance_name=instance.instance_name, 
				weigher_name=instance.weigher_name, 
				modope="WEIGHING", 
	          	data_assigned=reservation.id
			)
			reservation_id = reservation.id
			if error_message:
				await self.deleteReservation(request=None, id=reservation.id)
		return {
			"instance": instance,
			"command_details": {
				"status_modope": status_modope,
				"command_executed": command_executed,
				"error_message": error_message
			},
			"reservation_id": reservation_id
		}

	async def Weight1(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		status_modope, command_executed, error_message = 500, False, ""
		tare = md_weigher.module_weigher.getRealtime(instance_name=instance.instance_name, weigher_name=instance.weigher_name).tare
		weigher = md_weigher.module_weigher.getInstanceWeigher(instance_name=instance.instance_name, weigher_name=instance.weigher_name)[instance.instance_name]
		take_of_weight_on_startup = weigher["take_of_weight_on_startup"]
		take_of_weight_before_weighing = weigher["take_of_weight_before_weighing"]
		current_id = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"]["id_selected"]["id"]
		reservation = None
		status_modope = None
		command_executed = None
		error_message = None
		if take_of_weight_on_startup is True:
			error_message = "Scaricare la pesa dopo l'avvio del programma"
		if take_of_weight_before_weighing is True:
			error_message = "Scaricare la pesa prima di eseguire nuova pesata"
		if current_id:
			reservation = get_reservation_by_id(current_id)
		if reservation and len(reservation.in_out) > 0 and lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"]["id_selected"]["weight1"] is not None:
			error_message = "Il mezzo ha già effettuato l'entrata."
		elif tare != "0":
			error_message = "Eliminare la tara per effettuare l'entrata del mezzo."
		elif not reservation:
			reservation = await self.addReservation(request=None, body=AddReservationDTO(**{
                	**lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"]["data_in_execution"], 
                 	"number_in_out": 1,
                  	"type": "MANUALLY",
                   	"hidden": True
                }))
			current_id = reservation.id
		if not error_message:
			status_modope, command_executed, error_message = md_weigher.module_weigher.setModope(
				instance_name=instance.instance_name, 
				weigher_name=instance.weigher_name, 
				modope="WEIGHING", 
				data_assigned=reservation.id
			)
			if error_message and reservation.hidden is True:
				await self.deleteReservation(request=None, id=current_id)
		return {
			"instance": instance,
			"command_details": {
				"status_modope": status_modope,
				"command_executed": command_executed,
				"error_message": error_message
			},
			"reservation_id": current_id
		}

	async def Weight2(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		status_modope, command_executed, error_message = 500, False, ""
		tare = md_weigher.module_weigher.getRealtime(instance_name=instance.instance_name, weigher_name=instance.weigher_name).tare
		weigher = md_weigher.module_weigher.getInstanceWeigher(instance_name=instance.instance_name, weigher_name=instance.weigher_name)[instance.instance_name]
		take_of_weight_on_startup = weigher["take_of_weight_on_startup"]
		take_of_weight_before_weighing = weigher["take_of_weight_before_weighing"]
		idReservation = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"]["id_selected"]["id"]
		reservation = None
		if take_of_weight_on_startup is True:
			error_message = "Scaricare la pesa dopo l'avvio del programma"
		elif take_of_weight_before_weighing is True:
			error_message = "Scaricare la pesa prima di eseguire nuova pesata"
		else:
			if idReservation:
				reservation = get_reservation_by_id(idReservation)
			just_created = False
			if reservation:
				if len(reservation.in_out) == 0 and reservation.number_in_out is not None and tare != "0":
					error_message = "Non è possibile effettuare pesate con tara negli accessi multipli."
				if len(reservation.in_out) > 0 and reservation.number_in_out is not None and reservation.in_out[-1].idWeight1 and reservation.in_out[-1].idWeight2 and tare != "0":
					error_message = "Rimuovere la tara per effettuare l'uscita del mezzo tramite id."
				elif len(reservation.in_out) == 0 and tare == "0":
					error_message = "Inserire una tara o effettuare una entrata prima di effettuare l'uscita del mezzo tramite id."
				if len(reservation.in_out) > 0 and lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"]["id_selected"]["weight1"] is None and tare == "0":
					error_message = "E' necessario effettuare l'entrata del mezzo"
				# elif len(reservation.in_out) > 0 and not reservation.in_out[-1].idWeight1 and tare == "0":
				# 	error_message = "Inserire una tara o effettuare una entrata prima di effettuare l'uscita del mezzo tramite id."
			if not reservation:
				if tare == "0":
					error_message = "Nessun id impostato per effettuare l'uscita."
				else:
					reservation = await self.addReservation(request=None, body=AddReservationDTO(**{
						**lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"]["data_in_execution"], 
						"number_in_out": 1,
	                  	"type": "MANUALLY",
						"hidden": True
					}))
					idReservation = reservation.id
					just_created = True
			if idReservation and not error_message:
				status_modope, command_executed, error_message = md_weigher.module_weigher.setModope(
					instance_name=instance.instance_name, 
					weigher_name=instance.weigher_name, 
					modope="WEIGHING", 
					data_assigned=idReservation)
			if error_message and just_created:
				await self.deleteReservation(request=None, id=idReservation)
		return {
			"instance": instance,
			"command_details": {
				"status_modope": status_modope,
				"command_executed": command_executed,
				"error_message": error_message
			},
			"reservation_id": idReservation
		}

	async def WeighingByIdentify(self, request: Request, identify_dto: IdentifyDTO, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node), token: str = None):
		if request is not None:
			response = get_user(token=token)
			if hasattr(response, "status_code"):
				return response
		status_modope, command_executed, error_message = 500, False, ""
		reservation = None
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
		await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"cam_message": cam_message})
		if proc in self.automatic_weighing_process:
			error_message = f"Pesatura automatica con '{identify_dto.identify}' già in esecuzione sulla pesa '{instance.weigher_name}'"
		else:
			self.automatic_weighing_process.append(proc)
			weigher = md_weigher.module_weigher.getInstanceWeigher(instance_name=instance.instance_name, weigher_name=instance.weigher_name)[instance.instance_name]
			division = weigher["division"]
			take_of_weight_on_startup = weigher["take_of_weight_on_startup"]
			take_of_weight_before_weighing = weigher["take_of_weight_before_weighing"]
			if take_of_weight_on_startup is True:
				error_message = "Scaricare la pesa dopo l'avvio del programma"
			elif take_of_weight_before_weighing is True:
				error_message = "Scaricare la pesa prima di eseguire nuova pesata"
			else:
				reservation = get_reservation_by_identify_if_uncomplete(identify=identify_dto.identify)
				realtime = md_weigher.module_weigher.getRealtime(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
				min_weight = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["min_weight"]
				if realtime.gross_weight == "" or realtime.gross_weight != "" and float(realtime.gross_weight) < min_weight:
					error_message = f"Il peso deve essere maggiore di {min_weight} kg"
				elif reservation:
					current_weigher_data = self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
					if current_weigher_data["id_selected"]["id"] != reservation["id"]:
						await self.DeleteData(instance=instance)
						try:
							if reservation["type"].name == TypeReservation.RESERVATION.name and reservation["number_in_out"] is not None and realtime.tare != "0":
								error_message = "Non è possibile effettuare pesate con tara negli accessi multipli."
							else:
								await self.SetData(request=None, data_dto=DataDTO(**{"id_selected": {"id": reservation["id"]}}), instance=instance)
						except Exception as e:
							error_message = e.detail
					if not error_message:
						data = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"]
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
							lb_log.warning(realtime)
							current_tare = realtime.tare.replace("PT", "").replace(" ",  "")
							m = modope if request is not None else current_modope
							if modope != "PRESETTARE" and current_modope != "PRESETTARE":
								if current_weigher_data["id_selected"]["id"] != reservation["id"]:
									error_message = f"Pesatura automatica interrotta. Accesso con '{identify_dto.identify}' deselezionato."
									await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"error_message": error_message})
									break
								if weight1 is None and current_tare != "" and tare is not None and abs(float(current_tare) - float(tare)) > division:
									if current_tare == "0":
										if timeout >= 0:
											message = f"Impostando la tara per la pesatura automatica."
											await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"message": message})
									elif timeout >= 0:
										error_message = f"Pesatura automatica interrotta. La tara di {tare} kg non è stata impostata correttamente."
										await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"error_message": error_message})
										break
								elif realtime.gross_weight == "" or float(realtime.gross_weight) != "" and float(realtime.gross_weight) < min_weight:
									error_message = f"Pesatura automatica interrotta. Il peso deve essere maggiore di {min_weight} kg."
									await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"error_message": error_message})
									break
								elif realtime.gross_weight != "" and float(realtime.gross_weight) >= min_weight:
									if realtime.status == "ST":
										if stable == 3:
											status_modope, command_executed, error_message = md_weigher.module_weigher.setModope(
												instance_name=instance.instance_name, 
												weigher_name=instance.weigher_name, 
												modope="WEIGHING", 
												data_assigned=reservation["id"])
											if error_message:
												error_message = f"Errore nella pesatura automatica: {error_message}. Ritento."
												await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"error_message": error_message})
											if command_executed:
												break
										else:
											stable = stable + 1
									else:
										stable = 0
				else:
					error_message = f"Accesso con '{identify_dto.identify}' non esistente."
			current_weigher_data = self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
			if error_message and reservation and current_weigher_data["id_selected"]["id"] == reservation["id"]:
				await self.DeleteData(instance=instance)
			self.automatic_weighing_process.remove(proc)
		return {
			"instance": instance,
			"command_details": {
				"status_modope": status_modope,
				"command_executed": command_executed,
				"error_message": error_message
			},
			"reservation_id": reservation["id"] if reservation else None,
			"identify_dto": identify_dto
		}

	# async def WeighingByIdentify(self, request: Request, identify_dto: IdentifyDTO, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node), token: str = None):
	# 	if request is not None:
	# 		response = get_user(token=token)
	# 		if hasattr(response, "status_code"):
	# 			return response
	# 	status_modope, command_executed, error_message = 500, False, ""
	# 	weigher = md_weigher.module_weigher.getInstanceWeigher(instance_name=instance.instance_name, weigher_name=instance.weigher_name)[instance.instance_name]
	# 	take_of_weight_on_startup = weigher["take_of_weight_on_startup"]
	# 	take_of_weight_before_weighing = weigher["take_of_weight_before_weighing"]
	# 	if take_of_weight_on_startup is True:
	# 		error_message = "Scaricare la pesa dopo l'avvio del programma"
	# 	elif take_of_weight_before_weighing is True:
	# 		error_message = "Scaricare la pesa prima di eseguire nuova pesata"
	# 	else:
	# 		reservation = get_reservation_by_identify_if_uncomplete(identify=identify_dto.identify)
	# 		realtime = md_weigher.module_weigher.getRealtime(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
	# 		min_weight = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["min_weight"]
	# 		if realtime.gross_weight == "" or realtime.gross_weight != "" and float(realtime.gross_weight) < min_weight:
	# 			error_message = f"Il peso deve essere maggiore di {min_weight} kg"
	# 		elif reservation:
	# 			current_weigher_data = self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
	# 			set_data = None
	# 			if current_weigher_data["id_selected"]["id"] != reservation["id"]:
	# 				set_data = await self.SetData(request=None, data_dto=DataDTO(**{"id_selected": {"id": reservation["id"]}}), instance=instance)
	# 			data = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"]
	# 			tare = data["data_in_execution"]["vehicle"]["tare"]
	# 			weight1 = data["id_selected"]["weight1"]
	# 			weighing = True
	# 			if weight1 is None and tare is not None:
	# 				weighing = False
	# 				timeout = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["connection"]["timeout"]
	# 				time_between_actions = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["time_between_actions"]
	# 				while timeout > 0:
	# 					await asyncio.sleep(time_between_actions)
	# 					modope = md_weigher.module_weigher.getModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
	# 					current_modope = md_weigher.module_weigher.getCurrentModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
	# 					realtime = md_weigher.module_weigher.getRealtime(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
	# 					current_tare = realtime.tare.replace("PT", "").replace(" ",  "")
	# 					m = modope if request is not None else current_modope
	# 					if modope != "PRESETTARE" and current_modope != "PRESETTARE" and current_tare == str(tare):
	# 						weighing = True
	# 						break
	# 					timeout -= time_between_actions
	# 				if weighing is False:
	# 					error_message = "Errore durante la pesatura automatica. La tara non è stata impostata correttamente."
	# 					await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"message": error_message})
	# 			if weighing:
	# 				realtime = md_weigher.module_weigher.getRealtime(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
	# 				if realtime.status != "ST":
	# 					error_message = "Errore durante la pesatura automatica. La pesa non è stabile."
	# 					await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({"message": error_message})
	# 				else:
	# 					status_modope, command_executed, error_message = md_weigher.module_weigher.setModope(
	# 						instance_name=instance.instance_name, 
	# 						weigher_name=instance.weigher_name, 
	# 						modope="WEIGHING", 
	# 						data_assigned=reservation["id"])
	# 	if error_message:
	# 		await self.DeleteData(instance=instance)
	# 	return {
	# 		"instance": instance,
	# 		"command_details": {
	# 			"status_modope": status_modope,
	# 			"command_executed": command_executed,
	# 			"error_message": error_message
	# 		},
	# 		"reservation_id": reservation["id"] if reservation else None
	# 	}

	def Callback_WeighingByIdentify(self, instance_name: str, weigher_name: str, identify: str):
		instance = InstanceNameWeigherDTO(instance_name=instance_name, weigher_name=weigher_name)
		identify_dto = IdentifyDTO(identify=identify)

		# Lancia un thread separato siccome viene lanciata come callback all'interno del ciclo di lettura della pesa
		# e non può essere bloccante altrimenti rimarrebbe bloccato tutto il ciclo di lettura della pesa
		# su PRESETTARE in attesa della pesata automatica e non eseguirebbe WEIGHING
		def run_in_thread():
			asyncio.run(self.WeighingByIdentify(request=None, instance=instance, identify_dto=identify_dto))

		thread = threading.Thread(target=run_in_thread)
		thread.start()

	async def Tare(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		status_modope, command_executed, error_message = 500, False, ""
		data_id_selected = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"]["id_selected"]
		execution = True
		if data_id_selected["id"] and data_id_selected["weight1"]:
			# last_in_out = get_reservation_by_id(data_id_selected["id"])
			# if len(last_in_out.in_out) > 0 and not last_in_out.in_out[-1].idWeight2:
			error_message = "Non puoi effettuare la preset tara perchè il mezzo ha già effettuato una entrata."
			execution = False
			# else:
			# 	execution = True
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
		data_id_selected = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"]["id_selected"]
		execution = True
		if data_id_selected["id"] and data_id_selected["weight1"]:
			# last_in_out = get_reservation_by_id(data_id_selected["id"])
			# if len(last_in_out.in_out) > 0 and not last_in_out.in_out[-1].idWeight2:
			error_message = "Non puoi effettuare la preset tara perchè il mezzo ha già effettuato una entrata."
			execution = False
			# else:
			# 	execution = True
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
		while instance.instance_name in weighers_data and instance.weigher_name in weighers_data[instance.instance_name]:
			weigher = md_weigher.module_weigher.getInstanceWeigher(instance_name=instance.instance_name, weigher_name=instance.weigher_name)[instance.instance_name]
			status = weigher["status"]
			always_execute_realtime_in_undeground = weigher["always_execute_realtime_in_undeground"]
			modope_on_close = "REALTIME" if always_execute_realtime_in_undeground else "OK"
			if websocket not in weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.active_connections:
				if len(weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.active_connections) == 0:
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
					message = "Errore di connessione"
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
				await self.DeleteData(instance=instance)
				await self.StopAllCommand(instance=instance)
				md_weigher.module_weigher.setModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name, modope=modope_on_close)
				break
			await asyncio.sleep(1)

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