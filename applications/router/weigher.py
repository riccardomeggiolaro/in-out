from fastapi import APIRouter, HTTPException, Depends, WebSocket
from libs.lb_printer import HTMLPrinter
import libs.lb_database as lb_database
import libs.lb_config as lb_config
import libs.lb_log as lb_log
from applications.utils.instance_weigher import InstanceNameDTO, InstanceNameNodeDTO, NodeConnectionManager
from applications.utils.utils import get_query_params_name, get_query_params_name_node
from typing import Optional
from modules.md_weigher.types import DataInExecution
import modules.md_weigher.md_weigher as md_weigher
import asyncio
from typing import Union
from modules.md_weigher.types import Realtime, Diagnostic, Weight, Data
import libs.lb_log as lb_log
import modules.md_weigher.md_weigher as md_weigher
import datetime as dt
from libs.lb_database import add_data, get_data_by_id, update_data

router = APIRouter()

# ==== FUNZIONI RICHIAMABILI DENTRO LA APPLICAZIONE =================
# Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di peso in tempo reale
def Callback_Realtime(instance_name: str, instance_node: Union[str, None], pesa_real_time: Realtime):
	global weighers_sockets
	pesa_real_time.net_weight = pesa_real_time.net_weight.zfill(6)
	pesa_real_time.tare = pesa_real_time.tare.zfill(6)
	asyncio.run(weighers_sockets[instance_name][instance_node].manager_realtime.broadcast(pesa_real_time.dict()))

# Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di diagnostica
def Callback_Diagnostic(instance_name: str, instance_node: Union[str, None], diagnostic: dict):
	global weighers_sockets
	asyncio.run(weighers_sockets[instance_name][instance_node].manager_diagnostic.broadcast(diagnostic))

# Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di pesata
def Callback_Weighing(instance_name: str, instance_node: Union[str, None], last_pesata: Weight):
	global weighers_sockets
	# global printer
	if last_pesata.data_assigned is not None and not isinstance(last_pesata.data_assigned, int) and last_pesata.weight_executed.executed:
		node = md_weigher.module_weigher.instances[instance_name].getNode(instance_node)
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
			"weigher": node["name"]
		}
		add_data("weighing", obj)
		status, data = md_weigher.module_weigher.instances[instance_name].deleteDataInExecution(node=instance_node, call_callback=False)
		node_found = [n for n in lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"] if n["node"] == instance_node]
		index_node_found = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"].index(node_found[0])
		lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][index_node_found]["data"]["data_in_execution"] = data["data_in_execution"]
		lb_config.saveconfig()
		asyncio.run(weighers_sockets[instance_name][instance_node].manager_realtime.broadcast(data))
	elif isinstance(last_pesata.data_assigned, int) and last_pesata.weight_executed.executed:
		data = get_data_by_id("weighing", last_pesata.data_assigned)
		net_weight = data["weight1"] - int(last_pesata.weight_executed.gross_weight)
		obj = {
			"weight2": last_pesata.weight_executed.gross_weight,
			"net_weight": net_weight,
			"date2": dt.datetime.now(),
			"pid2": last_pesata.weight_executed.pid
		}
		update_data("weighing", last_pesata.data_assigned, obj)
		status, data = md_weigher.module_weigher.instances[instance_name].setIdSelected(node=instance_node, new_id=-1, call_callback=False)
		node_found = [n for n in lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"] if n["node"] == instance_node]
		index_node_found = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"].index(node_found[0])
		lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][index_node_found]["data"]["id_selected"] = {
			"id": None
		}
		lb_config.saveconfig()
		asyncio.run(weighers_sockets[instance_name][instance_node].manager_realtime.broadcast(data))
	elif last_pesata.data_assigned is None and last_pesata.weight_executed.executed:
		node = md_weigher.module_weigher.instances[instance_name].getNode(instance_node)
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
			"weigher": node["name"]
		}
		add_data("weighing", obj)
	# if last_pesata.weight_executed.executed:
	# 	html = f"""
	# 		<h1>PESATA ESEGUITA</h1>
	# 		<p>PID: {last_pesata.weight_executed.pid}</p>
	# 		<p>PESO: {last_pesata.weight_executed.gross_weight}</p>
	# 	"""
	# 	printer.print_html(html)

	asyncio.run(weighers_sockets[instance_name][instance_node].manager_realtime.broadcast(last_pesata.dict()))

def Callback_TarePTareZero(instance_name: str, instance_node: Union[str, None], ok_value: str):
	global weighers_sockets
	result = {"command_executend": ok_value}
	asyncio.run(weighers_sockets[instance_name][instance_node].manager_realtime.broadcast(result))

def Callback_Data(instance_name: str, instance_node: Union[str, None], data: Data):
	global weighers_sockets
	if asyncio.get_event_loop().is_running():
		asyncio.create_task(weighers_sockets[instance_name][instance_node].manager_realtime.broadcast(data.dict()))
	else:
		loop = asyncio.get_event_loop()
		loop.run_until_complete(weighers_sockets[instance_name][instance_node].manager_realtime.broadcast(data.dict()))

def Callback_ActionInExecution(instance_name: str, instance_node: Union[str, None], action_in_execution: str):
	global weighers_sockets
	result = {"command_in_executing": action_in_execution}
	if asyncio.get_event_loop().is_running():
		asyncio.create_task(weighers_sockets[instance_name][instance_node].manager_realtime.broadcast(result))
	else:
		loop = asyncio.get_event_loop()
		loop.run_until_complete(weighers_sockets[instance_name][instance_node].manager_realtime.broadcast(result))

@router.get("/start/realtime")
async def StartRealtime(instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
	status, status_modope, status_command, error_message = md_weigher.module_weigher.instances[instance.name].setModope(node=instance.node, modope="REALTIME")

	return {
		"instance": instance,
		"command_executed": {
			"status": status,
			"status_modope": status_modope,
			"status_command": status_command,
			"error_message": error_message
		}
	}

@router.get("/start/diagnostics")
async def StartDiagnostics(instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
	status, status_modope, status_command, error_message = md_weigher.module_weigher.instances[instance.name].setModope(node=instance.node, modope="DIAGNOSTICS")
	return {
		"instance": instance,
		"command_executed": {
			"status": status,
			"status_modope": status_modope,
			"status_command": status_command,
			"error_message": error_message
		}
	}

@router.get("/stop/all_command")
async def StopAllCommand(instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
	status, status_modope, status_command, error_message = md_weigher.module_weigher.instances[instance.name].setModope(node=instance.node, modope="OK")
	return {
		"instance": instance,
		"command_executed": {
			"status": status,
			"status_modope": status_modope,
			"status_command": status_command,
			"error_message": error_message
		}
	}

@router.get("/print")
async def Print(instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
	data = DataInExecution(**{})
	status, status_modope, status_command, error_message = md_weigher.module_weigher.instances[instance.name].setModope(node=instance.node, modope="WEIGHING", data_assigned=data)
	return {
		"instance": instance,
		"command_executed": {
			"status": status,
			"status_modope": status_modope,
			"status_command": status_command,
			"error_message": error_message
		}
	}

@router.get("/weighing")
async def Weighing(instance: InstanceNameNodeDTO = Depends(get_query_params_name_node), id: Optional[int] = None):
	data = None
	if id is not None:
		data = id
	else:
		status, data = md_weigher.module_weigher.instances[instance.name].getData(node=instance.node)
	status, status_modope, status_command, error_message = md_weigher.module_weigher.instances[instance.name].setModope(node=instance.node, modope="WEIGHING", data_assigned=data)
	return {
		"instance": instance,
		"command_executed": {
			"status": status,
			"status_modope": status_modope,
			"status_command": status_command,
			"error_message": error_message
		}
	}

@router.get("/tare")
async def Tare(instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
	status, status_modope, status_command, error_message = md_weigher.module_weigher.instances[instance.name].setModope(node=instance.node, modope="TARE")
	return {
		"instance": instance,
		"command_executed": {
			"status": status,
			"status_modope": status_modope,
			"status_command": status_command,
			"error_message": error_message
		}
	}

@router.get("/presettare")
async def PresetTare(instance: InstanceNameNodeDTO = Depends(get_query_params_name_node), tare: Optional[int] = 0):
	status, status_modope, status_command, error_message = md_weigher.module_weigher.instances[instance.name].setModope(node=instance.node, modope="PRESETTARE", presettare=tare)
	return {
		"instance": instance,
		"command_executed": {
			"status": status,
			"status_modope": status_modope,
			"status_command": status_command,
			"error_message": error_message
		}
	}

@router.get("/zero")
async def Zero(instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
	status, status_modope, status_command, error_message = md_weigher.module_weigher.instances[instance.name].setModope(node=instance.node, modope="ZERO")
	return {
		"instance": instance,
		"command_executed": {
			"status": status,
			"status_modope": status_modope,
			"status_command": status_command,
			"error_message": error_message
		}
	}

@router.websocket("/realtime")
async def websocket_endpoint(websocket: WebSocket, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
	global weighers_sockets
	await weighers_sockets[instance.name][instance.node].manager_realtime.connect(websocket)
	while True:
		try:
			if len(weighers_sockets[instance.name][instance.node].manager_realtime.active_connections) > 0:
				status = md_weigher.module_weigher.instances[instance.name].getNode(instance.node)["status"]
				if status == 200:
					modope_in_execution = md_weigher.module_weigher.instances[instance.name].getModope(instance.node)
					if modope_in_execution in ["OK", "DIAGNOSTICS"]:
						if modope_in_execution == "DIAGNOSTICS":
							await WEIGHERS[instance.name]["node_sockets"][instance.node].manager_realtime.broadcast({
								"status":"--",
								"type":"--",
								"net_weight": "Diagnostica in corso",
								"gross_weight":"--",
								"tare":"--",
								"unite_measure": "--"
							})
						md_weigher.module_weigher.instances[instance.name].setModope(instance.node, "REALTIME")
				else:
					message = "Pesa scollegata"
					if status == 301:
						message = "Connessione non settata"
					elif status == 201:
						message = "Protocollo pesa non valido"
					await weighers_sockets[instance.name][instance.node].manager_realtime.broadcast({
						"status":"--",
						"type":"--",
						"net_weight": message,
						"gross_weight":"--",
						"tare":"--",
						"unite_measure": str(status)
					})
			else:
				md_weigher.module_weigher.instances[instance.name].setModope(instance.node, "OK")
				break
			await asyncio.sleep(1)
		except Exception as e:
			lb_log.error(e)

def initWeigherRouter():
	global weighers_sockets

	weighers_sockets = {}

	for name, instance in md_weigher.module_weigher.instances.items():
		nodes_sockets = {}
		for node in instance.nodes:
			nodes_sockets[node.node] = NodeConnectionManager()
		weighers_sockets[name] = nodes_sockets

	md_weigher.module_weigher.setApplicationCallback(
		cb_realtime=Callback_Realtime, 
		cb_diagnostic=Callback_Diagnostic, 
		cb_weighing=Callback_Weighing, 
		cb_tare_ptare_zero=Callback_TarePTareZero,
		cb_data=Callback_Data,
		cb_action_in_execution=Callback_ActionInExecution
	)