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
from applications.utils.utils import get_query_params_name, get_query_params_name_node
from applications.router.generic import router as genericRouter
from applications.router.printer import router as printerRouter
from applications.router.anagrafic import router as anagraficRouter
from applications.router.weigher import router as routerWeigher, initWeigherRouter
from applications.router.weigher_data_execution import router as weigherDataExecutionRouter
from applications.router.weigher_database import router as weigherDatabaseRouter
# ==============================================================

name_app = "app_api"

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
# ==============================================================

# ==== MAINPRGLOOP =============================================
# funzione che si connette a redis, setta i moduli e imposta le callback da richiamare dentro i moduli
def mainprg():
	global app
	global thread_ssh_tunnel

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
	global ssh_client

	app = FastAPI()

	# app.mount("/_app", StaticFiles(directory=f"{base_dir_templates}/_app"), name="_app")
	# app.mount("/assets", StaticFiles(directory=f"{base_dir_templates}/assets"), name="assets")

	app.add_middleware(
		CORSMiddleware, 
		allow_origins=["*"],
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)

	# Usa la sottoroute "printer"
	app.include_router(printerRouter, prefix="", tags=["printer"])

	app.include_router(anagraficRouter, prefix="", tags=["anagrafic"])

	initWeigherRouter()

	app.include_router(routerWeigher, prefix="", tags=["weigher"])

	app.include_router(weigherDataExecutionRouter, prefix="", tags=["weigher data execution"])

	app.include_router(weigherDatabaseRouter, prefix="", tags=["weigher database"])

	app.include_router(genericRouter, prefix="", tags=["generic"])

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