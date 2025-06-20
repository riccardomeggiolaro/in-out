from fastapi import APIRouter, Depends, WebSocket, HTTPException, Request
from applications.utils.utils_weigher import InstanceNameWeigherDTO, get_query_params_name_node
import modules.md_weigher.md_weigher as md_weigher
from applications.router.weigher.dto import PlateDTO, DataDTO
from typing import Optional
import asyncio
import libs.lb_log as lb_log
from applications.router.weigher.data import DataRouter
import libs.lb_config as lb_config
from applications.router.weigher.manager_weighers_data import weighers_data
from applications.router.anagrafic.reservation import ReservationRouter
from modules.md_database.functions.get_reservation_by_plate_if_uncomplete import get_reservation_by_plate_if_uncomplete
from modules.md_database.interfaces.reservation import AddReservationDTO, SetReservationDTO

class CommandWeigherRouter(DataRouter, ReservationRouter):
	def __init__(self):
		super().__init__()

		self.router_action_weigher = APIRouter()

		self.router_action_weigher.add_api_route('/realtime', self.StartRealtime, methods=['GET'])
		self.router_action_weigher.add_api_route('/diagnostic', self.StartDiagnostics, methods=['GET'])
		self.router_action_weigher.add_api_route('/stop-all-command', self.StopAllCommand, methods=['GET'])
		self.router_action_weigher.add_api_route('/print', self.Print, methods=['GET'])
		self.router_action_weigher.add_api_route('/in', self.In, methods=['POST'])
		self.router_action_weigher.add_api_route('/out', self.Out, methods=['POST'])
		self.router_action_weigher.add_api_route('/out/plate', self.OutByPlate, methods=['POST'])
		self.router_action_weigher.add_api_route('/tare', self.Tare, methods=['GET'])
		self.router_action_weigher.add_api_route('/tare/preset', self.PresetTare, methods=['GET'])
		self.router_action_weigher.add_api_route('/zero', self.Zero, methods=['GET'])

		self.router_action_weigher.add_api_websocket_route('/realtime', self.websocket_endpoint)

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

	async def StartDiagnostics(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		status_modope, command_executed, error_message = md_weigher.module_weigher.setModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name, modope="DIAGNOSTICS")
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

	async def Print(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		status_modope, command_executed, error_message = 500, False, ""
		if lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"]["id_selected"]["id"]:
			error_message = "Deselezionare l'id per effettuare l'entrata del mezzo."
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
		return {
			"instance": instance,
			"command_details": {
				"status_modope": status_modope,
				"command_executed": command_executed,
				"error_message": error_message
			}
		}

	async def In(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		status_modope, command_executed, error_message = 500, False, ""
		tare = md_weigher.module_weigher.getRealtime(instance_name=instance.instance_name, weigher_name=instance.weigher_name).tare
		if lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"]["id_selected"]["id"]:
			error_message = "Deselezionare l'id per effettuare l'entrata del mezzo."
		elif tare != "0":
			error_message = "Eliminare la tara per effettuare l'entrata del mezzo."
		else:
			reservation = await self.addReservation(request=None, body=AddReservationDTO(**{
                	**lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"]["data_in_execution"], 
                 	"number_in_out": 1,
                  	"type": "MANUALLY",
                   	"hidden": True
                }))
			status_modope, command_executed, error_message = md_weigher.module_weigher.setModope(
				instance_name=instance.instance_name, 
				weigher_name=instance.weigher_name, 
				modope="WEIGHING", 
	          	data_assigned=reservation.id
			)
		return {
			"instance": instance,
			"command_details": {
				"status_modope": status_modope,
				"command_executed": command_executed,
				"error_message": error_message
			}
		}

	async def Out(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		status_modope, command_executed, error_message = 500, False, ""
		tare = md_weigher.module_weigher.getRealtime(instance_name=instance.instance_name, weigher_name=instance.weigher_name).tare
		idReservation = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"]["id_selected"]["id"]
		if idReservation and tare != "0":
			error_message = "Rimuovere la tara per effettuare l'uscite del mezzo tramite id."
		elif not idReservation and tare == "0":
			error_message = "Nessun id impostato per effettuare l'uscita."
		else:
			if not idReservation:
				reservation = await self.addReservation(request=None, body=AddReservationDTO(**{
					**lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"]["data_in_execution"], 
					"number_in_out": 1
				}))
				idReservation = reservation.id
			status_modope, command_executed, error_message = md_weigher.module_weigher.setModope(
				instance_name=instance.instance_name, 
				weigher_name=instance.weigher_name, 
				modope="WEIGHING", 
				data_assigned=idReservation)
		return {
			"instance": instance,
			"command_details": {
				"status_modope": status_modope,
				"command_executed": command_executed,
				"error_message": error_message
			}
		}

	async def OutByPlate(self, request: Request, plate_dto: PlateDTO, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		try:
			reservation = get_reservation_by_plate_if_uncomplete(plate=plate_dto.plate)
			if reservation:
				current_weigher_data = self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
				specific = "telecamera " if request.state.user.level == 0 else ""
				if current_weigher_data["id_selected"]["id"] != reservation.id:
					self.Callback_Message(instance_name=instance.instance_name, weigher_name=instance.weigher_name, message=f"Targa '{plate_dto.plate}' selezionata da {specific}'{request.client.host}'")
					await self.SetData(data_dto=DataDTO(**{"id_selected": {"id": reservation.id}}), instance=instance)
				result = await self.Out(instance=instance)
				if result["command_details"]["error_message"]:
					error = result["command_details"]["error_message"]
					error_message = f"Errore effettuando pesata da {specific}'{request.client.host}': {error}"
					self.Callback_Message(instance_name=instance.instance_name, weigher_name=instance.weigher_name, message=error_message)
				# if result["command_details"]["command_executed"] is False:
				# 	await self.DeleteData(instance=instance)
				return result
		except Exception as e:
			lb_log.error(e)
			return HTTPException(status_code=500, detail=str(e))

	async def Tare(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
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
  
	async def websocket_endpoint(self, websocket: WebSocket, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.connect(websocket)
		while instance.instance_name in weighers_data and instance.weigher_name in weighers_data[instance.instance_name]:
			if websocket not in weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.active_connections:
				break
			if len(weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.active_connections) > 0:
				status = md_weigher.module_weigher.getInstanceWeigher(instance_name=instance.instance_name, weigher_name=instance.weigher_name)[instance.instance_name]["status"]
				if status == 200:
					modope_in_execution = md_weigher.module_weigher.getModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
					if modope_in_execution in ["OK", "DIAGNOSTICS"]:
						if modope_in_execution == "DIAGNOSTICS":
							await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({
								"status":"--",
								"type":"--",
								"net_weight": "Diagnostica in corso",
								"gross_weight":"--",
								"tare":"--",
								"unite_measure": "--"
							})
						md_weigher.module_weigher.setModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name, modope="REALTIME")
				else:
					message = "Pesa scollegata"
					if status == 301:
						message = "Connessione non settata"
					elif status == 201:
						message = "Protocollo pesa non valido"
					await weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({
						"status":"--",
						"type":"--",
						"net_weight": message,
						"gross_weight":"--",
						"tare":"--",
						"unite_measure": str(status)
					})
			else:
				md_weigher.module_weigher.setModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name, modope="OK")
				break
			await asyncio.sleep(1)