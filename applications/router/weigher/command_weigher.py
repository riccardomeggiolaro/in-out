from fastapi import APIRouter, Depends, WebSocket
from applications.utils.utils_weigher import InstanceNameNodeDTO, get_query_params_name_node
from applications.utils.utils import validate_time
import modules.md_weigher.md_weigher as md_weigher
from modules.md_weigher.types import DataInExecution
from modules.md_weigher.dto import IdSelectedDTO, WeighingDataDTO
from typing import Optional, Union
import asyncio
import libs.lb_log as lb_log
from applications.router.weigher.config_weigher import ConfigWeigher

class CommandWeigher(ConfigWeigher):
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

		self.router_action_weigher.add_api_websocket_route('/realtime', self.websocket_endpoint)

	async def StartRealtime(self, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
		status, status_modope, status_command, error_message = md_weigher.module_weigher.setModope(name=instance.name, node=instance.node, modope="REALTIME")

		return {
			"instance": instance,
			"command_executed": {
				"status": status,
				"status_modope": status_modope,
				"status_command": status_command,
				"error_message": error_message
			}
		}

	async def StartDiagnostics(self, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
		status, status_modope, status_command, error_message = md_weigher.module_weigher.setModope(name=instance.name, node=instance.node, modope="DIAGNOSTICS")
		return {
			"instance": instance,
			"command_executed": {
				"status": status,
				"status_modope": status_modope,
				"status_command": status_command,
				"error_message": error_message
			}
		}

	async def StopAllCommand(self, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
		status, status_modope, status_command, error_message = md_weigher.module_weigher.setModope(name=instance.name, node=instance.node, modope="OK")
		return {
			"instance": instance,
			"command_executed": {
				"status": status,
				"status_modope": status_modope,
				"status_command": status_command,
				"error_message": error_message
			}
		}

	async def Print(self, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
		data = DataInExecution(**{})
		status, status_modope, status_command, error_message = md_weigher.module_weigher.setModope(name=instance.name, node=instance.node, modope="WEIGHING", data_assigned=data)
		return {
			"instance": instance,
			"command_executed": {
				"status": status,
				"status_modope": status_modope,
				"status_command": status_command,
				"error_message": error_message
			}
		}

	async def Weighing(self, body: WeighingDataDTO, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
		data = None
		if body.id_selected is not None:
			data = body.id_selected
		elif body.plate is not None:
			data = body.plate
		elif body.data_in_execution is not None:
			data = body.data_in_execution
		status, status_modope, status_command, error_message = md_weigher.module_weigher.setModope(name=instance.name, node=instance.node, modope="WEIGHING", data_assigned=data)
		return {
			"instance": instance,
			"command_executed": {
				"status": status,
				"status_modope": status_modope,
				"status_command": status_command,
				"error_message": error_message
			}
		}

	async def Tare(self, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
		status, status_modope, status_command, error_message = md_weigher.module_weigher.setModope(name=instance.name, node=instance.node, modope="TARE")
		return {
			"instance": instance,
			"command_executed": {
				"status": status,
				"status_modope": status_modope,
				"status_command": status_command,
				"error_message": error_message
			}
		}

	async def PresetTare(self, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node), tare: Optional[int] = 0):
		status, status_modope, status_command, error_message = md_weigher.module_weigher.setModope(name=instance.name, node=instance.node, modope="PRESETTARE", presettare=tare)
		return {
			"instance": instance,
			"command_executed": {
				"status": status,
				"status_modope": status_modope,
				"status_command": status_command,
				"error_message": error_message
			}
		}

	async def Zero(self, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
		status, status_modope, status_command, error_message = md_weigher.module_weigher.setModope(name=instance.name, node=instance.node, modope="ZERO")
		return {
			"instance": instance,
			"command_executed": {
				"status": status,
				"status_modope": status_modope,
				"status_command": status_command,
				"error_message": error_message
			}
		}

	async def websocket_endpoint(self, websocket: WebSocket, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
		await self.weighers_sockets[instance.name][instance.node].manager_realtime.connect(websocket)
		while instance.name in self.weighers_sockets and instance.node in self.weighers_sockets[instance.name]:
			if websocket not in self.weighers_sockets[instance.name][instance.node].manager_realtime.active_connections:
				break
			if len(self.weighers_sockets[instance.name][instance.node].manager_realtime.active_connections) > 0:
				status = md_weigher.module_weigher.getInstanceNode(name=instance.name, node=instance.node)[instance.name]["status"]
				if status == 200:
					modope_in_execution = md_weigher.module_weigher.getModope(name=instance.name, node=instance.node)
					if modope_in_execution in ["OK", "DIAGNOSTICS"]:
						if modope_in_execution == "DIAGNOSTICS":
							await self.weighers_sockets[instance.name][instance.node].manager_realtime.broadcast({
								"status":"--",
								"type":"--",
								"net_weight": "Diagnostica in corso",
								"gross_weight":"--",
								"tare":"--",
								"unite_measure": "--"
							})
						md_weigher.module_weigher.setModope(name=instance.name, node=instance.node, modope="REALTIME")
				else:
					message = "Pesa scollegata"
					if status == 301:
						message = "Connessione non settata"
					elif status == 201:
						message = "Protocollo pesa non valido"
					await self.weighers_sockets[instance.name][instance.node].manager_realtime.broadcast({
						"status":"--",
						"type":"--",
						"net_weight": message,
						"gross_weight":"--",
						"tare":"--",
						"unite_measure": str(status)
					})
			else:
				md_weigher.module_weigher.setModope(name=instance.name, node=instance.node, modope="OK")
				break
			await asyncio.sleep(1)