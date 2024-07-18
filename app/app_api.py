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
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
import uvicorn  # noqa: E402
import asyncio  # noqa: E402
import psutil  # noqa: E402
import modules.md_weigher.md_weigher as weigher  # noqa: E402
# import modules.md_rfid as rfid
from modules.md_weigher.types import DataInExecution  # noqa: E402
from modules.md_weigher.dto import SetupWeigherDTO, ConfigurationDTO, ChangeSetupWeigherDTO  # noqa: E402
from lib.lb_system import SerialPort, Tcp  # noqa: E402
from typing import Optional, Union  # noqa: E402
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
# ==============================================================

# ==== MAINPRGLOOP =============================================
# funzione che si connette a redis, setta i moduli e imposta le callback da richiamare dentro i moduli
def mainprg():
	global data_in_execution
	global manager_realtime
	global manager_diagnostic
	global manager_data_in_execution
	global app

	@app.get("/list_serial_ports")
	async def ListSerialPorts():
		status, data = lb_system.list_serial_port()
		if status is True:
			return {
				"list_serial_ports": data
			}
		return data

	@app.get("/start/realtime")
	async def StartRealtime(node: Optional[str] = None):
		result = weigher.setModope(node=node, modope="REALTIME")
		return {
			"status_command": result
		}

	@app.get("/start/diagnostics")
	async def StartDiagnostics(node: Optional[str] = None):
		result = weigher.setModope(node=node, modope="DIAGNOSTICS")
		return {
			"status_command": result
		}

	@app.get("/stop/all_command")
	async def StopAllCommand(node: Optional[str] = None):
		result = weigher.setModope(node=node, modope="")
		return {
			"status_command": result
		}

	@app.get("/print")
	async def Print(node: Optional[str] = None):
		result = weigher.setModope(node=node, modope="WEIGHING", data_assigned=None)
		if result:
			return {
				"status_command": result,
			}
		else:
			raise HTTPException(status_code=404, detail='Not found')

	@app.get("/weighing")
	async def Weighing(node: Optional[str] = None, id: Optional[int] = None):
		data = None
		if id is not None:
			data = id
		else:
			data = weigher.getDataInExecution(node=node)
			if data is not None:
				data = weigher.DataInExecution(**data)
		result = weigher.setModope(node=node, modope="WEIGHING", data_assigned=data)
		if result:
			weigher.deleteDataInExecution(node=node)
			return {
				"status_command": result
			}
		else:
			raise HTTPException(status_code=404, detail='Not found')

	@app.get("/tare")
	async def Tare(node: Optional[str] = None):
		result = weigher.setModope(node=node, modope="TARE")
		return {
			"status_command": result
		}

	@app.get("/presettare")
	async def PresetTare(node: Optional[str] = None, tare: Optional[int] = 0):
		result = weigher.setModope(node=node, modope="PRESETTARE", presettare=tare)
		return {
			"status_command": result
		}

	@app.get("/zero")
	async def Zero(node: Optional[str] = None):
		result = weigher.setModope(node=node, modope="ZERO")
		return {
			"status_command": result
		}	 

	@app.get("/data_in_execution")
	async def GetDataInExecution(node: Optional[str] = None):
		result = weigher.getDataInExecution(node=node)
		if result:
			return {
				"node": node,
				"data_in_execution": result
			}
		else:
			raise HTTPException(status_code=404, detail='Not found')

	@app.patch("/set/data_in_execution")
	async def SetDataInExecution(node: Optional[str] = None, data: DataInExecution = {}):
		result = weigher.setDataInExecution(node=node, data_in_execution=data)
		if result:
			await manager_data_in_execution.broadcast(result)
			return {
				"node": node,
				"data_in_execution": result
			}
		else:
			raise HTTPException(status_code=404, detail='Not found')

	@app.delete("/delete/data_in_execution")
	async def DeleteDataInExecution(node: Optional[str] = None):
		result = weigher.deleteDataInExecution(node=node)
		if result:
			await manager_data_in_execution.broadcast(result)
			return {
				"node": node,
				"data_in_execution": result
			}
		else:
			raise HTTPException(status_code=404, detail='Not found')

	@app.get("/config_weigher")
	async def GetConfigWeigher():
		return weigher.getConfig()

	@app.delete("/config_weigher")
	async def DeleteConfigWeigher():
		result, message = weigher.deleteConfig()
		if result:
			lb_config.g_config["app_api"]["weigher"]["nodes"] = []
			lb_config.g_config["app_api"]["weigher"]["connection"] = None
			lb_config.saveconfig()
		return {
			"status_command": result,
			"message": message
		}

	@app.get("/config_weigher/nodes")
	async def GetConfigWeigherNodes():
		result = weigher.getNodes()
		return result

	@app.get("/config_weigher/node")
	async def GetConfigWeigherNode(node: Optional[str] = None):
		result = weigher.getNode(node)
		if not result:
			raise HTTPException(status_code=404, detail='Not found')
		return result

	@app.post("/config_weigher/node")
	async def AddConfigWeigherNode(node: SetupWeigherDTO):
		result = weigher.addNode(node)
		if result:
			weigher.setActionNode(
					node=node,
					cb_realtime=Callback_Realtime, 
					cb_diagnostic=Callback_Diagnostic, 
					cb_weighing=Callback_Weighing, 
					cb_tare_ptare_zero=Callback_TarePTareZero)
			lb_config.g_config["app_api"]["weigher"]["nodes"].append(result)
			lb_config.saveconfig()
		return result

	@app.patch("/config_weigher/node")
	async def SetConfigWeigherSetup(node: Optional[str] = None, setup: ChangeSetupWeigherDTO = {}):
		if node == "null":
			node = None
		response = weigher.setNode(node, setup)
		if response:
			node_found = [n for n in lb_config.g_config["app_api"]["weigher"]["nodes"] if n["node"] == node]
			index_node_found = lb_config.g_config["app_api"]["weigher"]["nodes"].index(node_found[0])
			lb_config.g_config["app_api"]["weigher"]["nodes"][index_node_found] = response
			lb_config.saveconfig()
			return response
		else:
			raise HTTPException(status_code=404, detail='Not found')

	@app.delete("/config_weigher/node")
	async def DeleteConfigWeigherSetup(node: Optional[str] = None):
		node_removed = weigher.deleteNode(node)
		if node_removed:
			node_found = [n for n in lb_config.g_config["app_api"]["weigher"]["nodes"] if n["node"] == node]
			lb_config.g_config["app_api"]["weigher"]["nodes"].remove(node_found[0])
			lb_config.saveconfig()
			return {
				"status_command": node_removed
			}
		else:
			raise HTTPException(status_code=404, detail='Not found')

	@app.get("/config_weigher/connection")
	async def GetConfigWeigherConnection():
		connection = weigher.getConnection()
		if connection:
			return connection
		raise HTTPException(status_code=404, detail='Not found')

	@app.patch("/config_weigher/connection")
	async def SetConfigWeigherConnection(connection: Union[SerialPort, Tcp]):
		connected, conn, message = weigher.setConnection(connection)
		lb_config.g_config["app_api"]["weigher"]["connection"] = conn
		lb_config.saveconfig()
		return {
			"connected": connected,
			"connection": conn,
			"message": message
		}

	@app.patch("/config_weigher/time_between_actions/{time}")
	async def SetTimeBetweenActions(time: Union[int, float]):
		if time < 0:
			return {
				"message": "Time must be greater or same than 0"
			}
		result = weigher.setTimeBetweenActions(time=time)
		lb_config.g_config["app_api"]["weigher"]["time_between_actions"] = result
		lb_config.saveconfig()
		return {
			"time_between_actions": result
		}

	@app.delete("/config_weigher/connection")
	async def DeleteConfigWeigherConnection():
		connection_removed = weigher.deleteConnection()
		if connection_removed:
			lb_config.g_config["app_api"]["weigher"]["connection"] = None
			lb_config.saveconfig()
		return {
			"status_command": connection_removed
		}

	# @app.get("/config_rfid")
	# async def GetConfiRfid():
	# 	return lb_config.g_config["app_api"]["rfid"]

	# @app.patch("/set/config_rfid")
	# async def SetConfigRfid(config: ConfigRfid):
	# 	global rfid
	# 	global modules
	# 	code = config.module
	# 	r_module = next((m for m in modules if m["code"] == code), None)
	# 	rfid = r_module["module"]
	# 	result = rfid.initialize(connection=config.connection, setup=config.setup)
	# 	if result is True:
	# 		lb_config.g_config["app_api"]["rfid"] = config.dict()
	# 		lb_config.saveconfig()
	# 		rfid.setAction(cb_cardcode=Callback_Cardcode)
	# 	else:
	# 		rfid = None
	# 	return {
	# 		"message": result
	# 	}

	# @app.patch("/set/config_rfid/setup")
	# async def SetConfigRfidSetup(setup: SetupRfid):
	# 	global rfid
	# 	if rfid is not None:
	# 		result = rfid.setSetup(setup)
	# 		lb_config.g_config["app_api"]["rfid"]["setup"] = result
	# 		lb_config.saveconfig()
	# 		return result
	# 	return {
	# 		"status_command": 0
	# 	}

	# @app.delete("/config_rfid")
	# async def DeleteConfigRfid():
	# 	global rfid
	# 	if rfid is not None:
	# 		result = rfid.deleteConfig()
	# 		if result is True:
	# 			rfid = None
	# 			lb_config.g_config["app_api"]["rfid"]["module"] = None
	# 			lb_config.g_config["app_api"]["rfid"]["connection"] = None
	# 			lb_config.g_config["app_api"]["rfid"]["setup"] = {}
	# 			lb_config.saveconfig()
	# 		return {
	# 			"message": result
	# 		}
	# 	return {
	# 		"status_command": 0
	# 	}

	@app.websocket("/realtime")
	async def websocket_endpoint(websocket: WebSocket):
		await manager_realtime.connect(websocket)
		try:
			if len(manager_realtime.active_connections) == 1:
				if weigher is not None:
					weigher.realTime()
			while True:
				await asyncio.sleep(0.2)
		except WebSocketDisconnect:
			await manager_realtime.disconnect(websocket)
			if len(manager_realtime.active_connections) == 0:
				if weigher is not None:
					weigher.stopCommand()

	@app.websocket("/diagnostic")
	async def websocket_diagnostic(websocket: WebSocket):
		await manager_diagnostic.connect(websocket)
		try:
			if len(manager_diagnostic.active_connections) == 1:
				if weigher is not None:
					weigher.diagnostic()
			while True:
				await asyncio.sleep(0.2)
		except WebSocketDisconnect:
			await manager_diagnostic.disconnect(websocket)
			if len(manager_diagnostic.active_connections) == 0 and len(manager_realtime.active_connections) >= 1:
				if weigher is not None:
					weigher.realTime()

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
	try:
		port = lb_config.g_config["app_api"]["port"]
		connection = [conn for conn in psutil.net_connections() if conn.laddr.port == port] 
		print(f"Chiudendo il processo che utilizza la porta {port}...")
		p = psutil.Process(connection[-1].pid)
		p.kill()
		p.wait(timeout=5)  # Attendere al massimo 5 secondi per la chiusura
		print(f"Processo sulla porta {port} chiuso con successo.")
	except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired) as e:	
		print(f"Impossibile chiudere il processo sulla porta {port}. {e}")

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

	manager_realtime = ConnectionManager()
	manager_diagnostic = ConnectionManager()
	manager_data_in_execution = ConnectionManager()

	app = FastAPI()

	app.add_middleware(
		CORSMiddleware, 
		allow_origins=["*"],
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)

	configuration = ConfigurationDTO(**lb_config.g_config["app_api"]["weigher"])
	weigher.initialize(configuration=configuration)
	weigher.setAction(
			cb_realtime=Callback_Realtime, 
			cb_diagnostic=Callback_Diagnostic, 
			cb_weighing=Callback_Weighing, 
			cb_tare_ptare_zero=Callback_TarePTareZero)

	# rfid.setAction(cb_cardcode=Callback_Cardcode)

	# if lb_config.g_config["app_api"]["rfid"]["connection"] != None:
	# 	config = (**lb_config.g_config["app_api"]["rfid"])
	# 	setup = info["class_setup"](**lb_config.g_config["app_api"]["rfid"]["setup"])
	# 	rfid.initialize(configuration=config)
# ==============================================================