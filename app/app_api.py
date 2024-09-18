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
import inspect
__frame = inspect.currentframe()
namefile = inspect.getfile(__frame).split("/")[-1].replace(".py", "")
import lib.lb_log as lb_log  # noqa: E402
import lib.lb_system as lb_system  # noqa: E402
import lib.lb_config as lb_config  # noqa: E402
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Path, Depends, Query, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
import uvicorn  # noqa: E402
import asyncio  # noqa: E402
import psutil  # noqa: E402
import modules.md_weigher.md_weigher as md_weigher  # noqa: E402
# import modules.md_rfid as rfid
from modules.md_weigher.types import DataInExecution  # noqa: E402
from modules.md_weigher.dto import SetupWeigherDTO, ConfigurationDTO, ChangeSetupWeigherDTO  # noqa: E402
from lib.lb_system import SerialPort, Tcp  # noqa: E402
from typing import Optional, Union  # noqa: E402
from lib.lb_utils import GracefulKiller, createThread, startThread, closeThread
from pydantic import BaseModel, validator
import threading
from os.path import exists
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import os
from fastapi.responses import RedirectResponse
# ==============================================================

# ==== FUNZIONI RICHIAMABILI DENTRO LA APPLICAZIONE =================
# Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di peso in tempo reale
def Callback_Realtime(pesa_real_time: dict):
	asyncio.run(manager_realtime.broadcast(pesa_real_time))
	lb_log.info(pesa_real_time)

# Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di diagnostica
def Callback_Diagnostic(diagnostic: dict):
	asyncio.run(manager_diagnostic.broadcast(diagnostic))
	lb_log.info(diagnostic)

# Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di pesata
def Callback_Weighing(last_pesata: dict):
	asyncio.run(manager_data_in_execution.broadcast(last_pesata))
	lb_log.info(last_pesata)
 
def Callback_TarePTareZero(ok_value: str):
	result = {"command_executend": ok_value}
	asyncio.run(manager_data_in_execution.broadcast(result))
	lb_log.info(ok_value)

def Callback_Cardcode(cardcode: str):
	result = {"cardcode": cardcode}
	asyncio.run(manager_data_in_execution.broadcast(result))
	lb_log.info(cardcode)

# Function to create a new instance of weigher module
def createIstanceWeigher(configuration):
	global WEIGHERS

	name = configuration["name"]
	module = md_weigher
	weigher_configuration = ConfigurationDTO(**configuration)
	module.initialize(configuration=weigher_configuration)
	module.setAction(
		cb_realtime=Callback_Realtime, 
		cb_diagnostic=Callback_Diagnostic, 
		cb_weighing=Callback_Weighing,
		cb_tare_ptare_zero=Callback_TarePTareZero)
	# Inizializza il modulo.
	module.init()  # Inizializzazione del modulo
	# Crea e avvia il thread del modulo.
	thread = createThread(module.start)
	WEIGHERS.append({"name": name, "module": module, "thread": thread})
	startThread(thread)
 
def findInstanceWeigher(name):
	global WEIGHERS

	index = None
 
	for i, weigher in enumerate(WEIGHERS):
		if weigher["name"] == name:
			exist = True
			index = i

	return index

def deleteInstanceWeigher(name):
	global WEIGHERS

	deleted = False
 
	for i, weigher in enumerate(WEIGHERS):
		if weigher["name"] == name:
			lb_log.info("..killing weigher configuration: %s" % weigher["name"])  # Logga un messaggio informativo
			closeThread(weigher["thread"], weigher["module"])
			deleted = True
	return deleted

def renameInstanceWeigher(name: str, newName: str):
	global WEIGHERS

	updated = False
 
	for i, weigher in enumerate(WEIGHERS):
		if weigher["name"] == name:
			weigher["name"] = newName
			lb_config.g_config["app_api"]["weighers"][i]["name"] = newName
			lb_config.saveconfig()
			updated = True
	return updated

# create connectio manager of weight real time
class ConnectionManager:
	def __init__(self):
		self.active_connections: list[WebSocket] = []

	async def connect(self, websocket: WebSocket):
		await websocket.accept()
		self.active_connections.append(websocket)

	def disconnect(self, websocket: WebSocket):
		self.active_connections.remove(websocket)

	async def send_personal_message(self, message: str, websocket: WebSocket):
		await websocket.send_text(message)

	async def broadcast(self, message: str):
		for connection in self.active_connections:
			try:
				await connection.send_json(message)
			except Exception:
				#print("client down")
				self.disconnect(connection)

class InstanceWeigherIndexDTO(BaseModel):
	name: str
 
class InstanceWeigherIndexNodeDTO(InstanceWeigherIndexDTO):
	node: Optional[str] = None

class InstanceIndexDTO(BaseModel):
	name: str
	index: int

class InstanceIndexNodeDTO(InstanceIndexDTO):
    node: Optional[str] = None
 
def get_query_params_index(params: InstanceWeigherIndexDTO = Depends()):
	global WEIGHERS

	index = findInstanceWeigher(params.name)
	if index is None:
		raise HTTPException(status_code=404, detail='Name instance does not exist')
	return InstanceIndexDTO(**{"name": params.name, "index": index})
 
def get_query_params_index_node(params: InstanceWeigherIndexNodeDTO = Depends()):
	global WEIGHERS

	index = findInstanceWeigher(params.name)
	if index is None:
		raise HTTPException(status_code=404, detail='Name instance does not exist')
	if WEIGHERS[index]["module"].getNode(params.node) is None:
		raise HTTPException(status_code=404, detail='Node not exist')
	return InstanceIndexNodeDTO(**{"name": params.name, "index": index, "node": params.node})
# ==============================================================

# ==== MAINPRGLOOP =============================================
# funzione che si connette a redis, setta i moduli e imposta le callback da richiamare dentro i moduli
def mainprg():
	global data_in_execution
	global manager_realtime
	global manager_diagnostic
	global manager_data_in_execution
	global app
	global WEIGHERS

	@app.get("/{filename:path}", response_class=HTMLResponse)
	async def Static(request: Request, filename: Optional[str] = None):
		base_dir_templates = os.getcwd()
		templates = Jinja2Templates(directory=f"{base_dir_templates}/app/static")
		if filename is None or filename == "":
			return templates.TemplateResponse("index.html", {"request": request})
		elif filename == "index.html":
			return RedirectResponse(url="/")
		file_path = f'app/static/{filename}'
		file_exist = os.path.isfile(f"{base_dir_templates}/{file_path}")
		if file_exist:
			return templates.TemplateResponse(filename, {"request": request})
		return RedirectResponse(url="not-found.html")

	@app.get("/list_serial_ports")
	async def ListSerialPorts():
		status, data = lb_system.list_serial_port()
		if status is True:
			return {
				"list_serial_ports": data
			}
		return data

	@app.get("/start/realtime")
	async def StartRealtime(instance: InstanceIndexNodeDTO = Depends(get_query_params_index_node)):
		status, status_modope, status_command, error_message = WEIGHERS[instance.index]["module"].setModope(node=instance.node, modope="REALTIME")
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
	async def StartDiagnostics(instance: InstanceIndexNodeDTO = Depends(get_query_params_index_node)):
		status, status_modope, status_command, error_message = WEIGHERS[instance.index]["module"].setModope(node=instance.node, modope="DIAGNOSTICS")
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
	async def StopAllCommand(instance: InstanceIndexNodeDTO = Depends(get_query_params_index_node)):
		status, status_modope, status_command, error_message = WEIGHERS[instance.index]["module"].setModope(node=instance.node, modope="OK")
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
	async def Print(instance: InstanceIndexNodeDTO = Depends(get_query_params_index_node)):
		status, status_modope, status_command, error_message = WEIGHERS[instance.index]["module"].setModope(node=instance.node, modope="WEIGHING", data_assigned=None)
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
	async def Weighing(instance: InstanceIndexNodeDTO = Depends(get_query_params_index_node), id: Optional[int] = None):
		data = None
		if id is not None:
			data = id
		else:
			data = WEIGHERS[instance.index]["module"].getDataInExecution(node=instance.node)
		status, status_modope, status_command, error_message = WEIGHERS[instance.index]["module"].setModope(node=instance.node, modope="WEIGHING", data_assigned=data)
		if status_command:
			WEIGHERS[instance.index]["module"].deleteDataInExecution(node=instance.node)
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
	async def Tare(instance: InstanceIndexNodeDTO = Depends(get_query_params_index_node)):
		status, status_modope, status_command, error_message = WEIGHERS[instance.index]["module"].setModope(node=instance.node, modope="TARE")
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
	async def PresetTare(instance: InstanceIndexNodeDTO = Depends(get_query_params_index_node), tare: Optional[int] = 0):
		status, status_modope, status_command, error_message = WEIGHERS[instance.index]["module"].setModope(node=instance.node, modope="PRESETTARE", presettare=tare)
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
	async def Zero(instance: InstanceIndexNodeDTO = Depends(get_query_params_index_node)):
		status, status_modope, status_command, error_message = WEIGHERS[instance.index]["module"].setModope(node=instance.node, modope="ZERO")
		return {
			"instance": instance,
			"command_executed": {
				"status": status,
				"status_modope": status_modope,
				"status_command": status_command,
				"error_message": error_message
			}
		}	 

	@app.get("/data_in_execution")
	async def GetDataInExecution(instance: InstanceIndexNodeDTO = Depends(get_query_params_index_node)):
		status, data = WEIGHERS[instance.index]["module"].getDataInExecution(node=instance.node)
		return {
			"instance": instance,
			"data_in_execution": data,
			"status": status
		}

	@app.patch("/set/data_in_execution")
	async def SetDataInExecution(data_in_execution: DataInExecution = {}, instance: InstanceIndexNodeDTO = Depends(get_query_params_index_node)):
		status, data = WEIGHERS[instance.index]["module"].setDataInExecution(node=instance.node, data_in_execution=data_in_execution)
		await manager_data_in_execution.broadcast(data)
		return {
			"instance": instance,
			"data_in_execution": data,
			"status": status
		}

	@app.delete("/delete/data_in_execution")
	async def DeleteDataInExecution(instance: InstanceIndexNodeDTO = Depends(get_query_params_index_node)):
		status, data = WEIGHERS[instance.index]["module"].deleteDataInExecution(node=instance.node)
		await manager_data_in_execution.broadcast(data)
		return {
			"instance": instance,
			"data_in_execution": data,
			"status": status
		}

	@app.get("/config_weigher")
	async def GetConfigWeigher(instance: InstanceIndexDTO = Depends(get_query_params_index)):
		response = WEIGHERS[instance.index]["module"].getConfig()
		return {
			"instance": instance,
			"config_weigher": response
		}

	@app.delete("/config_weigher")
	async def DeleteConfigWeigher(instance: InstanceIndexDTO = Depends(get_query_params_index)):
		WEIGHERS[instance.index]["module"].deleteConfig()
		result = deleteInstanceWeigher(WEIGHERS[instance.index]["name"])
		if result:
			WEIGHERS.pop(instance.index)
			lb_config.g_config["app_api"]["weighers"].pop(instance.index)
			lb_config.saveconfig()
		return {
			"instance": instance,
			"status_command": result
		}

	@app.get("/config_weigher/nodes")
	async def GetConfigWeigherNodes(instance: InstanceIndexDTO = Depends(get_query_params_index)):
		responses = WEIGHERS[instance.index]["module"].getNodes()
		response = {
      		"instance": instance,
			"nodes": responses
		}
		return response

	@app.get("/config_weigher/node")
	async def GetConfigWeigherNode(instance: InstanceIndexNodeDTO = Depends(get_query_params_index_node)):
		response = WEIGHERS[instance.index]["module"].getNode(instance.node)
		if not response:
			raise HTTPException(status_code=404, detail='Not found')
		response["instance"] = instance
		return response

	@app.post("/config_weigher/node")
	async def AddConfigWeigherNode(node: SetupWeigherDTO, instance: InstanceIndexDTO = Depends(get_query_params_index)):
		response = WEIGHERS[instance.index]["module"].addNode(node)
		if response:
			WEIGHERS[instance.index]["module"].setActionNode(
					node=node,
					cb_realtime=Callback_Realtime, 
					cb_diagnostic=Callback_Diagnostic, 
					cb_weighing=Callback_Weighing, 
					cb_tare_ptare_zero=Callback_TarePTareZero)
			lb_config.g_config["app_api"]["weighers"][instance.index]["nodes"].append(response)
			lb_config.saveconfig()
		response["instance"] = instance
		return response

	@app.patch("/config_weigher/node")
	async def SetConfigWeigherSetup(setup: ChangeSetupWeigherDTO = {}, instance: InstanceIndexNodeDTO = Depends(get_query_params_index_node)):
		response = WEIGHERS[instance.index]["module"].setNode(instance.node, setup)
		if response:
			node_found = [n for n in lb_config.g_config["app_api"]["weighers"][instance.index]["nodes"] if n["node"] == instance.node]
			index_node_found = lb_config.g_config["app_api"]["weighers"][instance.index]["nodes"].index(node_found[0])
			lb_config.g_config["app_api"]["weighers"][instance.index]["nodes"][index_node_found] = response
			lb_config.saveconfig()
			response["instance"] = instance
			return response
		else:
			raise HTTPException(status_code=404, detail='Not found')

	@app.delete("/config_weigher/node")
	async def DeleteConfigWeigherSetup(instance: InstanceIndexNodeDTO = Depends(get_query_params_index_node)):
		node_removed = WEIGHERS[instance.index]["module"].deleteNode(instance.node)
		if node_removed:
			node_found = [n for n in lb_config.g_config["app_api"]["weighers"][instance.index]["nodes"] if n["node"] == instance.node]
			lb_config.g_config["app_api"]["weighers"][instance.index]["nodes"].remove(node_found[0])
			lb_config.saveconfig()
			return {
				"instance": instance,
				"status_command": node_removed
			}
		else:
			raise HTTPException(status_code=404, detail='Not found')

	@app.delete("/config_weigher/nodes")
	async def DeleteConfigWeigherSetup(instance: InstanceIndexDTO = Depends(get_query_params_index)):
		nodes_removed = WEIGHERS[instance.index]["module"].deleteNodes()
		if nodes_removed:
			lb_config.g_config["app_api"]["weighers"][instance.index]["nodes"] = []
			lb_config.saveconfig()
			return {
				"instance": instance,
				"status_command": nodes_removed
			}
		else:
			raise HTTPException(status_code=404, detail='Not found')

	@app.get("/config_weigher/connection")
	async def GetConfigWeigherConnection(instance: InstanceIndexDTO = Depends(get_query_params_index)):
		conn = WEIGHERS[instance.index]["module"].getConnection()
		time_between_actions = WEIGHERS[instance.index]["module"].getTimeBetweenActions()
		if conn:
			return {
				"instance": instance,
       			"connection": conn,
				"time_between_actions": time_between_actions
			}
		raise HTTPException(status_code=404, detail='Not found')

	@app.patch("/config_weigher/connection")
	async def SetConfigWeigherConnection(connection: Union[SerialPort, Tcp], instance: InstanceIndexDTO = Depends(get_query_params_index)):
		conn = WEIGHERS[instance.index]["module"].setConnection(connection)
		time_between_actions = WEIGHERS[instance.index]["module"].getTimeBetweenActions()
		lb_config.g_config["app_api"]["weighers"][instance.index]["connection"] = conn
		lb_config.saveconfig()
		return {
			"instance": instance,
			"connection": conn,
			"time_between_actions": time_between_actions,
		}

	@app.delete("/config_weigher/connection")
	async def DeleteConfigWeigherConnection(instance: InstanceIndexDTO = Depends(get_query_params_index)):
		if lb_config.g_config["app_api"]["weighers"][instance.index]["connection"] != None:
			conn = WEIGHERS[instance.index]["module"].deleteConnection()
			lb_config.g_config["app_api"]["weighers"][instance.index]["connection"] = None
			lb_config.saveconfig()
			return {
				"instance": instance,
				"connection": conn,
				"status_command": True
			}
		raise HTTPException(status_code=404, detail='Not found')

	@app.patch("/config_weigher/time_between_actions/{time}")
	async def SetTimeBetweenActions(time: Union[int, float], instance: InstanceIndexDTO = Depends(get_query_params_index)):
		if time < 0:
			return {
				"message": "Time must be greater or same than 0"
			}
		result = WEIGHERS[instance.index]["module"].setTimeBetweenActions(time=time)
		connection = WEIGHERS[instance.index]["module"].getConnection()
		lb_config.g_config["app_api"]["weighers"][instance.index]["time_between_actions"] = result
		lb_config.saveconfig()
		return {
			"instance": instance,
			"connection": connection,
			"time_between_actions": result
		}

	@app.websocket("/realtime")
	async def websocket_endpoint(websocket: WebSocket, instance: InstanceIndexNodeDTO = Depends(get_query_params_index_node)):
		await manager_realtime.connect(websocket)
		try:
			if len(manager_realtime.active_connections) == 1:
				if WEIGHERS[instance.index]["module"] is not None:
					WEIGHERS[instance.index]["module"].realTime()
			while True:
				await asyncio.sleep(0.2)
		except WebSocketDisconnect:
			await manager_realtime.disconnect(websocket)
			if len(manager_realtime.active_connections) == 0:
				if WEIGHERS[instance.index]["module"] is not None:
					WEIGHERS[instance.index]["module"].stopCommand()

	@app.websocket("/diagnostic")
	async def websocket_diagnostic(websocket: WebSocket, instance: InstanceIndexNodeDTO = Depends(get_query_params_index_node)):
		await manager_diagnostic.connect(websocket)
		try:
			if len(manager_diagnostic.active_connections) == 1:
				if WEIGHERS[instance.index]["module"] is not None:
					WEIGHERS[instance.index]["module"].diagnostic()
			while True:
				await asyncio.sleep(0.2)
		except WebSocketDisconnect:
			await manager_diagnostic.disconnect(websocket)
			if len(manager_diagnostic.active_connections) == 0 and len(manager_realtime.active_connections) >= 1:
				if WEIGHERS[instance.index]["module"] is not None:
					WEIGHERS[instance.index]["module"].realTime()

	@app.websocket("/datainexecution")
	async def weboscket_datainexecution(websocket: WebSocket):
		await manager_data_in_execution.connect(websocket)
		try:
			while True:
				await asyncio.sleep(0.2)
		except WebSocketDisconnect:
			await manager_data_in_execution.disconnect(websocket)

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
	global WEIGHERS
    
	for weigher in WEIGHERS:  # Per ogni modulo
		lb_log.info("..killing weigher configuration: %s" % weigher["name"])  # Logga un messaggio informativo
		closeThread(weigher["thread"], weigher["module"])

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

# ==== INIT ====================================================
# funzione che dichiara tutte le globali
def init():    
	lb_log.info("init")
	global manager_realtime
	global manager_diagnostic
	global manager_data_in_execution
	global app
	global rfid
	global modules
	global weigher_modules
	global rfid_modules
	global WEIGHERS

	WEIGHERS = []

	manager_realtime = ConnectionManager()
	manager_diagnostic = ConnectionManager()
	manager_data_in_execution = ConnectionManager()

	app = FastAPI()

	# app.mount("/static/javascript", StaticFiles(directory="static/javascript"), name="javascript")
	# app.mount("/static/css", StaticFiles(directory="static/css"), name="css")
	# app.mount("/static/img", StaticFiles(directory="static/img"), name="img")
	# app.mount("/app/static", StaticFiles(directory="app/static"), name="static")

	app.add_middleware(
		CORSMiddleware, 
		allow_origins=["*"],
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)

	# Carica thread per i moduli esterni.
	lb_log.info("loading weighers...")
	for weigher_configuration in lb_config.g_config["app_api"]["weighers"]:
		createIstanceWeigher(weigher_configuration)

	# rfid.setAction(cb_cardcode=Callback_Cardcode)

	# if lb_config.g_config["app_api"]["rfid"]["connection"] != None:
	# 	config = (**lb_config.g_config["app_api"]["rfid"])
	# 	setup = info["class_setup"](**lb_config.g_config["app_api"]["rfid"]["setup"])
	# 	rfid.initialize(configuration=config)
# ==============================================================