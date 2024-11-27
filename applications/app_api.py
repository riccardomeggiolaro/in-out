# ==============================================================
# = App......: main					   =
# = Description.: Applicazione			   =
# = Author......: Riccardo Meggiolaro				   =
# = Last rev....: 0.0002					   =
# -------------------------------------------------------------=
# 0.0002 : Implementato....
# 0.0001 : Creazione della applicazione
# ==============================================================

# ==== LIBRERIE DA IMPORTARE ===================================
import libs.lb_log as lb_log  # noqa: E402
import libs.lb_system as lb_system  # noqa: E402
import libs.lb_config as lb_config  # noqa: E402
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Path, Depends, Query, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
import uvicorn  # noqa: E402
import asyncio  # noqa: E402
import psutil  # noqa: E402
# import modules.md_rfid as rfid
from modules.md_weigher.types import DataInExecution, Weight, Data  # noqa: E402
from modules.md_weigher.dto import SetupWeigherDTO, ConfigurationDTO, ChangeSetupWeigherDTO, DataInExecutionDTO, DataDTO  # noqa: E402
from modules.md_weigher.types import Configuration
from libs.lb_system import SerialPort, Tcp, Connection  # noqa: E402
from typing import Optional, Union, Dict  # noqa: E402
from libs.lb_utils import GracefulKiller, createThread, startThread, closeThread
from pydantic import BaseModel, validator
import threading
from os.path import exists
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import os
import json
from modules.md_weigher.types import Realtime
from libs.lb_ssh import ssh_tunnel, SshClientConnection
import time
import libs.lb_database as lb_database  # noqa: E402
from libs.lb_database import filter_data, add_data, update_data, get_data_by_id
import datetime as dt
from applications.utils.instance_weigher import InstanceNameDTO, InstanceNameNodeDTO, NodeConnectionManager
import modules.md_weigher.md_weigher as md_weigher
# ==============================================================

name_app = "app_api"

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
		node = md_weigher.module_weigher.instances[instance.name].getNode(instance_node)
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
		asyncio.run(WEIGHERS[instance_name]["node_sockets"][instance_node].manager_realtime.broadcast(data))
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
		status, data = md_weigher.module_weigher.instances[instance.name].setIdSelected(node=instance_node, new_id=-1, call_callback=False)
		node_found = [n for n in lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"] if n["node"] == instance_node]
		index_node_found = lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"].index(node_found[0])
		lb_config.g_config["app_api"]["weighers"][instance_name]["nodes"][index_node_found]["data"]["id_selected"] = {
			"id": None
		}
		lb_config.saveconfig()
		asyncio.run(WEIGHERS[instance_name]["node_sockets"][instance_node].manager_realtime.broadcast(data))
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

def Callback_Cardcode(cardcode: str):
	pass

async def deleteInstanceWeigher(name):
	global weighers_sockets

	deleted = False
 
	if name in WEIGHERS:
		for node in weighers_sockets[name]:
			await weighers_sockets[name][node].manager_realtime.broadcast("Weigher instance deleted")
			weighers_sockets[name][node].manager_realtime.disconnect_all()
			await weighers_sockets[name][node].manager_diagnostic.broadcast("Weigher instance deleted")
			weighers_sockets[name][node].manager_diagnostic.disconnect_all()
			await weighers_sockets[name][node].manager_execution.broadcast("Weigher instance deleted")
			weighers_sockets[name][node].manager_execution.disconnect_all()
		weighers_sockets[name].stop()
		deleted = True
	return deleted

def get_query_params_name(params: InstanceNameDTO = Depends()):
	if params.name not in md_weigher.module_weigher.instances:
		raise HTTPException(status_code=404, detail='Name instance does not exist')
	return params
 
def get_query_params_name_node(params: InstanceNameNodeDTO = Depends()):
	if params.name not in md_weigher.module_weigher.instances:
		raise HTTPException(status_code=404, detail='Name instance does not exist')
	if md_weigher.module_weigher.instances[params.name].getNode(params.node) is None:
		raise HTTPException(status_code=404, detail='Node not exist')
	return params
# ==============================================================

# ==== MAINPRGLOOP =============================================
# funzione che si connette a redis, setta i moduli e imposta le callback da richiamare dentro i moduli
def mainprg():
	global data_in_execution
	global app
	global base_dir_templates
	global templates
	global thread_ssh_tunnel
	global printer
	global weighers_sockets

	@app.get("/weighings/in")
	async def getWeighings():
		try:
			data = filter_data("weighing", { "pid2": None })
			return data
		except Exception as e:
			return HTTPException(status_code=400, detail=f"{e}")

	@app.get("/list_serial_ports")
	async def ListSerialPorts():
		status, data = lb_system.list_serial_port()
		if status is True:
			return {
				"list_serial_ports": data
			}
		return data

	@app.get("/start/realtime")
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

	@app.get("/start/diagnostics")
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

	@app.get("/stop/all_command")
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

	@app.get("/print")
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

	@app.get("/weighing")
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

	@app.get("/tare")
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

	@app.get("/presettare")
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

	@app.get("/zero")
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

	@app.get("/data")
	async def GetDataInExecution(instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
		status, data = md_weigher.module_weigher.instances[instance.name].getData(node=instance.node)
		return {
			"instance": instance,
			"data": data,
			"status": status
		}

	@app.patch("/set/data")
	async def SetDataInExecution(data_dto: DataDTO, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
		data_in_execution = DataInExecution(**data_dto.data_in_execution.dict())
		status, data = md_weigher.module_weigher.instances[instance.name].setDataInExecution(node=instance.node, data_in_execution=data_in_execution, call_callback=True)
		if data_dto.id_selected is not None:
			status, data = md_weigher.module_weigher.instances[instance.name].setIdSelected(node=instance.node, new_id=data_dto.id_selected.id, call_callback=True)
		node_found = [n for n in lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"] if n["node"] == instance.node]
		index_node_found = lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"].index(node_found[0])
		lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"][index_node_found]["data"] = data
		lb_config.saveconfig()
		return {
			"instance": instance,
			"data": data,
			"status": status
		}

	@app.delete("/delete/data_in_execution")
	async def DeleteDataInExecution(instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
		status, data = md_weigher.module_weigher.instances[instance.name].deleteDataInExecution(node=instance.node, call_callback=True)
		node_found = [n for n in lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"] if n["node"] == instance.node]
		index_node_found = lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"].index(node_found[0])
		lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"][index_node_found]["data"]["data_in_execution"] = data
		lb_config.saveconfig()
		return {
			"instance": instance,
			"data": data,
			"status": status
		}

	@app.get("/all/config_weigher")
	async def GetConfigWeighers():
		return lb_config.g_config["app_api"]["weighers"]

	@app.get("/config_weigher")
	async def GetConfigWeigher(instance: InstanceNameDTO = Depends(get_query_params_name)):
		response = md_weigher.module_weigher.instances[instance.name].getConfig()
		return {
			"instance_name": instance.name,
			"config_weigher": response
		}

	@app.post("/config_weigher")
	async def CreateConfigWeighers(configuration: ConfigurationDTO):
		conn_to_check = configuration.connection.dict()
		del conn_to_check["conn"]
		for instance_name, instance_data in lb_config.g_config["app_api"]["weighers"].items():
			conn_to_check_without_timeout = {key: value for key, value in conn_to_check.items() if key != "timeout"}
			conn_without_timeout = {key: value for key, value in instance_data["connection"].items() if key != "timeout"}
			if configuration.name == instance_name:
					return HTTPException(status_code=400, detail='Name just exist')
			if conn_to_check_without_timeout == conn_without_timeout:
				return HTTPException(status_code=400, detail='Connection just exist')
		instance = {
			"connection": conn_to_check,
			"nodes": [],
			"time_between_actions": configuration.time_between_actions,
		}
		createIstanceWeigher(configuration.name, instance)
		lb_config.g_config["app_api"]["weighers"][configuration.name] = instance
		lb_config.saveconfig()
		return instance

	@app.delete("/config_weigher")
	async def DeleteConfigWeigher(instance: InstanceNameDTO = Depends(get_query_params_name)):
		md_weigher.module_weigher.instances[instance.name].deleteConfig()
		result = await deleteInstanceWeigher(instance.name)
		if result:
			WEIGHERS.pop(instance.name)
			lb_config.g_config["app_api"]["weighers"].pop(instance.name)
			lb_config.saveconfig()
		return {
			"instance_name": instance.name,
			"status_command": result
		}

	@app.get("/config_weigher/nodes")
	async def GetConfigWeigherNodes(instance: InstanceNameDTO = Depends(get_query_params_name)):
		responses = md_weigher.module_weigher.instances[instance.name].getNodes()
		response = {
	  		"instance_name": instance.name,
			"nodes": responses
		}
		return response

	@app.get("/config_weigher/node")
	async def GetConfigWeigherNode(instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
		response = md_weigher.module_weigher.instances[instance.name].getNode(instance.node)
		if not response:
			raise HTTPException(status_code=404, detail='Not found')
		response["instance_name"] = instance.name
		return response

	@app.post("/config_weigher/node")
	async def AddConfigWeigherNode(node: SetupWeigherDTO, instance: InstanceNameDTO = Depends(get_query_params_name)):
		if node.node in lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"]:
			raise HTTPException(status_code=400, detail='Node just exist')
		response = md_weigher.module_weigher.instances[instance.name].addNode(node)
		if response:
			md_weigher.module_weigher.instances[instance.name].setActionNode(
					node=node,
					cb_realtime=Callback_Realtime, 
					cb_diagnostic=Callback_Diagnostic, 
					cb_weighing=Callback_Weighing, 
					cb_tare_ptare_zero=Callback_TarePTareZero)
			lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"].append(response)
			lb_config.saveconfig()
		response["instance_name"] = instance.name
		return response

	@app.patch("/config_weigher/node")
	async def SetConfigWeigherSetup(setup: ChangeSetupWeigherDTO = {}, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
		if node.node in lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"]:
			raise HTTPException(status_code=400, detail='Node just exist')
		response = md_weigher.module_weigher.instances[instance.name].setNode(instance.node, setup)
		if response:
			node_found = [n for n in lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"] if n["node"] == instance.node]
			index_node_found = lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"].index(node_found[0])
			lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"][index_node_found] = response
			lb_config.saveconfig()
			response["instance"] = instance
			return response
		else:
			raise HTTPException(status_code=404, detail='Not found')

	@app.delete("/config_weigher/node")
	async def DeleteConfigWeigherSetup(instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
		node_removed = md_weigher.module_weigher.instances[instance.name].deleteNode(instance.node)
		if node_removed:
			node_found = [n for n in lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"] if n["node"] == instance.node]
			lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"].remove(node_found[0])
			lb_config.saveconfig()
			return {
				"instance_name": instance.name,
				"node": instance.node,
				"status_command": node_removed
			}
		else:
			raise HTTPException(status_code=404, detail='Not found')

	@app.delete("/config_weigher/nodes")
	async def DeleteConfigWeigherSetup(instance: InstanceNameDTO = Depends(get_query_params_name)):
		nodes_removed = md_weigher.module_weigher.instances[instance.name].deleteNodes()
		if nodes_removed:
			lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"] = []
			lb_config.saveconfig()
			return {
				"instance_name": instance.name,
				"status_command": nodes_removed
			}
		else:
			raise HTTPException(status_code=404, detail='Not found')

	@app.get("/config_weigher/connection")
	async def GetConfigWeigherConnection(instance: InstanceNameDTO = Depends(get_query_params_name)):
		conn = md_weigher.module_weigher.instances[instance.name].getConnection()
		time_between_actions = md_weigher.module_weigher.instances[instance.name].getTimeBetweenActions()
		if conn:
			return {
				"instance": instance,
	   			"connection": conn,
				"time_between_actions": time_between_actions
			}
		raise HTTPException(status_code=404, detail='Not found')

	@app.patch("/config_weigher/connection")
	async def SetConfigWeigherConnection(connection: Union[SerialPort, Tcp], instance: InstanceNameDTO = Depends(get_query_params_name)):
		conn = md_weigher.module_weigher.instances[instance.name].setConnection(connection)
		time_between_actions = md_weigher.module_weigher.instances[instance.name].getTimeBetweenActions()
		lb_config.g_config["app_api"]["weighers"][instance.name]["connection"] = conn
		lb_config.saveconfig()
		return {
			"instance": instance,
			"connection": conn,
			"time_between_actions": time_between_actions,
		}

	@app.delete("/config_weigher/connection")
	async def DeleteConfigWeigherConnection(instance: InstanceNameDTO = Depends(get_query_params_name)):
		if lb_config.g_config["app_api"]["weighers"][instance.name]["connection"] != {}:
			conn = md_weigher.module_weigher.instances[instance.name].deleteConnection()
			lb_config.g_config["app_api"]["weighers"][instance.name]["connection"] = {}
			lb_config.saveconfig()
			return {
				"instance": instance,
				"connection": conn,
				"status_command": True
			}
		raise HTTPException(status_code=404, detail='Not found')

	@app.patch("/config_weigher/time_between_actions/{time}")
	async def SetTimeBetweenActions(time: Union[int, float], instance: InstanceNameDTO = Depends(get_query_params_name)):
		if time < 0:
			return {
				"message": "Time must be greater or same than 0"
			}
		result = md_weigher.module_weigher.instances[instance.name].setTimeBetweenActions(time=time)
		connection = md_weigher.module_weigher.instances[instance.name].getConnection()
		lb_config.g_config["app_api"]["weighers"][instance.name]["time_between_actions"] = result
		lb_config.saveconfig()
		return {
			"instance": instance,
			"connection": connection,
			"time_between_actions": result
		}

	@app.websocket("/realtime")
	async def websocket_endpoint(websocket: WebSocket, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
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

	@app.websocket("/diagnostic")
	async def websocket_diagnostic(websocket: WebSocket, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
		await weighers_sockets[instance.name][instance.node].manager_diagnostic.connect(websocket)
		try:
			if len(weighers_sockets[instance.name][instance.node].manager_diagnostic.active_connections) == 1:
				if md_weigher.module_weigher.instances[instance.name] is not None:
					md_weigher.module_weigher.instances[instance.name].diagnostic()
			while True:
				await asyncio.sleep(0.2)
		except WebSocketDisconnect:
			await weighers_sockets[instance.name][instance.node].manager_diagnostic.disconnect(websocket)
			if len(weighers_sockets[instance.name][instance.node].manager_diagnostic.active_connections) == 0 and len(weighers_sockets[instance.name][instance.node].manager_realtime.active_connections) >= 1:
				if md_weigher.module_weigher.instances[instance.name] is not None:
					md_weigher.module_weigher.instances[instance.name].realTime()

	@app.get("/{filename:path}", response_class=HTMLResponse)
	async def Static(request: Request, filename: Optional[str] = None):
		if filename is None or filename == "":
			return templates.TemplateResponse("index.html", {"request": request})
		elif filename in ["index", "index.html"]:
			return RedirectResponse(url="/")
		file_exist = os.path.isfile(f"{base_dir_templates}/{filename}")
		if file_exist:
			return templates.TemplateResponse(filename, {"request": request})
		else:
			filename_html = f'{filename}.html'
			file_exist = os.path.isfile(f"{base_dir_templates}/{filename_html}")
			if file_exist:
				return templates.TemplateResponse(filename_html, {"request": request})
		return RedirectResponse(url="/")

	uvicorn.run(app, host="0.0.0.0", port=lb_config.g_config["app_api"]["port"], log_level="info", reload=False)
# ==============================================================


# ==== START ===================================================
# funzione che fa partire la applicazione
def start():
	lb_log.info("start")
	mainprg()  # 	a il loop a mainprg
	lb_log.info("end")
# ==============================================================

def stop():
	global ssh_client
	
	try:
		port = lb_config.g_config["app_api"]["port"]
		connection = [conn for conn in psutil.net_connections() if conn.laddr.port == port] 
		lb_log.info(f"Chiudendo il processo che utilizza la porta {port}...")
		p = psutil.Process(connection[-1].pid)
		p.kill()
		p.wait(timeout=5)  # Attendere al massimo 5 secondi per la chiusura
		lb_log.info(f"Processo sulla porta {port} chiuso con successo.")
	except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired) as e:	
		lb_log.info(f"Impossibile chiudere il processo sulla porta {port}. {e}")

	closeThread(ssh_client)

# ==== INIT ====================================================
# funzione che dichiara tutte le globali
def init():	
	lb_log.info("init")
	global app
	global rfid
	global modules
	global base_dir_templates
	global templates
	global ssh_client
	global weighers_sockets

	weighers_sockets = {}

	md_weigher.module_weigher.setApplicationCallback(
		cb_realtime=Callback_Realtime, 
		cb_diagnostic=Callback_Diagnostic, 
		cb_weighing=Callback_Weighing, 
		cb_tare_ptare_zero=Callback_TarePTareZero,
		cb_data=Callback_Data,
		cb_action_in_execution=Callback_ActionInExecution
	)

	for name, instance in md_weigher.module_weigher.instances.items():
		nodes_sockets = {}
		for node in instance.nodes:
			nodes_sockets[node.node] = NodeConnectionManager()
		weighers_sockets[name] = nodes_sockets

	app = FastAPI()

	base_dir_templates = os.getcwd() + "/client"
	templates = Jinja2Templates(directory=f"{base_dir_templates}")
	# app.mount("/_app", StaticFiles(directory=f"{base_dir_templates}/_app"), name="_app")
	# app.mount("/assets", StaticFiles(directory=f"{base_dir_templates}/assets"), name="assets")

	app.add_middleware(
		CORSMiddleware, 
		allow_origins=["*"],
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)

	from applications.router.printer import router as printerRouter
	from applications.router.anagrafic import router as anagraficRouter

	# Usa la sottoroute "printer"
	app.include_router(printerRouter, prefix="/printer", tags=["printer"])

	app.include_router(anagraficRouter, prefix="/anagrafic", tags=["anagrafic"])

	ssh_client = None
	if lb_config.g_config["app_api"]["ssh_client"]:
		ssh_client = lb_config.g_config["app_api"]["ssh_client"]
		ssh_client["local_port"] = lb_config.g_config["app_api"]["port"]
		ssh_client = createThread(ssh_tunnel, (SshClientConnection(**ssh_client),))
		startThread(ssh_client)

	# rfid.setAction(cb_cardcode=Callback_Cardcode)

	# if lb_config.g_config["app_api"]["rfid"]["connection"] != None:
	# 	config = (**lb_config.g_config["app_api"]["rfid"])
	# 	setup = i# ==============================================================
# = App......: main					   =
# = Description.: Applicazione			   =
# = Author......: Riccardo Meggiolaro				   =
# = Last rev....: 0.0002					   =
# -------------------------------------------------------------=
# 0.0002 : Implementato....
# 0.0001 : Creazione della applicazione
# ==============================================================