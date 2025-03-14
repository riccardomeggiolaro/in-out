from fastapi import APIRouter, Depends, WebSocket
from applications.utils.utils_weigher import InstanceNameWeigherDTO, get_query_params_name_node
from applications.utils.utils import validate_time
import modules.md_weigher.md_weigher as md_weigher
from applications.router.weigher.dto import DataInExecution
from applications.router.weigher.dto import IdSelectedDTO, WeighingDataDTO
from typing import Optional, Union
import asyncio
import libs.lb_log as lb_log
from applications.router.weigher.cams import DataInExecutionRouter

class CommandWeigherRouter(DataInExecutionRouter):
	def __init__(self):
		super().__init__()

		self.router_action_weigher = APIRouter()

		self.router_action_weigher.add_api_route('/realtime', self.StartRealtime, methods=['GET'])
		self.router_action_weigher.add_api_route('/diagnostic', self.StartDiagnostics, methods=['GET'])
		self.router_action_weigher.add_api_route('/stop_all_command', self.StopAllCommand, methods=['GET'])
		self.router_action_weigher.add_api_route('/print', self.Print, methods=['GET'])
		self.router_action_weigher.add_api_route('/weighing', self.Weighing, methods=['POST'])
		self.router_action_weigher.add_api_route('/tare', self.Tare, methods=['GET'])
		self.router_action_weigher.add_api_route('/preset_tare', self.PresetTare, methods=['GET'])
		self.router_action_weigher.add_api_route('/zero', self.Zero, methods=['GET'])
		self.router_action_weigher.add_api_route('/open_rele', self.OpenRele, methods=['GET'])
		self.router_action_weigher.add_api_route('/close_rele', self.CloseRele,methods=['GET'])

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
		data = DataInExecution(**{})
		status_modope, command_executed, error_message = md_weigher.module_weigher.setModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name, modope="WEIGHING", data_assigned=data)
		return {
			"instance": instance,
			"command_details": {
				"status_modope": status_modope,
				"command_executed": command_executed,
				"error_message": error_message
			}
		}

	async def Weighing(self, body: WeighingDataDTO, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		data = None
		if body.id_selected is not None:
			data = body.id_selected
		elif body.plate is not None:
			data = body.plate
		elif body.data_in_execution is not None:
			data = body.data_in_execution
		status_modope, command_executed, error_message = md_weigher.module_weigher.setModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name, modope="WEIGHING", data_assigned=data)
		return {
			"instance": instance,
			"command_details": {
				"status_modope": status_modope,
				"command_executed": command_executed,
				"error_message": error_message
			}
		}

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
  
	async def OpenRele(self, port_rele: str, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		status_modope, command_executed, error_message = md_weigher.module_weigher.setModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name, modope="OPENRELE", port_rele=port_rele)
		lb_log.warning(port_rele)
		return {
			"instance": instance,
			"command_details": {
				"status_modope": status_modope,
				"command_executed": command_executed,
				"error_message": error_message
			}
		}
  
	async def CloseRele(self, port_rele: str, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		status_modope, command_executed, error_message = md_weigher.module_weigher.setModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name, modope="CLOSERELE", port_rele=port_rele)
		return {
			"instance": instance,
			"command_details": {
				"status_modope": status_modope,
				"command_executed": command_executed,
				"error_message": error_message
			}
		}

	async def websocket_endpoint(self, websocket: WebSocket, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		await self.weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.connect(websocket)
		while instance.instance_name in self.weighers_data and instance.weigher_name in self.weighers_data[instance.instance_name]:
			if websocket not in self.weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.active_connections:
				break
			if len(self.weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.active_connections) > 0:
				status = md_weigher.module_weigher.getInstanceWeigher(instance_name=instance.instance_name, weigher_name=instance.weigher_name)[instance.instance_name]["status"]
				if status == 200:
					modope_in_execution = md_weigher.module_weigher.getModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
					if modope_in_execution in ["OK", "DIAGNOSTICS"]:
						if modope_in_execution == "DIAGNOSTICS":
							await self.weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({
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
					await self.weighers_data[instance.instance_name][instance.weigher_name]["sockets"].manager_realtime.broadcast({
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