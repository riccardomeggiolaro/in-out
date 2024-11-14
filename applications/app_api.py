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
import libs.lb_log as lb_log  # noqa: E402
import libs.lb_system as lb_system  # noqa: E402
import libs.lb_config as lb_config  # noqa: E402
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Path, Depends, Query, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
import uvicorn  # noqa: E402
import asyncio  # noqa: E402
import psutil  # noqa: E402
# import modules.md_rfid as rfid
from modules.md_weigher.md_weigher import WeigherInstance   # noqa: E402
from modules.md_weigher.types import DataInExecution, Weight  # noqa: E402
from modules.md_weigher.dto import SetupWeigherDTO, ConfigurationDTO, ChangeSetupWeigherDTO, DataInExecutionDTO  # noqa: E402
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
from fastapi.responses import RedirectResponse
import json
from modules.md_weigher.types import Realtime
from libs.lb_ssh import ssh_tunnel, SshClientConnection
import time
import libs.lb_database as lb_database  # noqa: E402
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np
from libs.lb_database import required_columns, required_dtos, filter_data, load_records_into_db, add_data, update_data, delete_data, delete_all_data, VehicleDTO, SocialReasonDTO, MaterialDTO
# ==============================================================

# ==== FUNZIONI RICHIAMABILI DENTRO LA APPLICAZIONE =================
# Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di peso in tempo reale
def Callback_Realtime(instance_name: str, instance_node: Union[str, None], pesa_real_time: Realtime):
	global WEIGHERS
	pesa_real_time.net_weight = pesa_real_time.net_weight.zfill(6)
	pesa_real_time.tare = pesa_real_time.tare.zfill(6)
	asyncio.run(WEIGHERS[instance_name]["node_sockets"][instance_node].manager_realtime.broadcast(pesa_real_time.dict()))

# Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di diagnostica
def Callback_Diagnostic(instance_name: str, instance_node: Union[str, None], diagnostic: dict):
	global WEIGHERS
	asyncio.run(WEIGHERS[instance_name]["node_sockets"][instance_node].manager_diagnostic.broadcast(diagnostic))

# Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di pesata
def Callback_Weighing(instance_name: str, instance_node: Union[str, None], last_pesata: Weight):
	global WEIGHERS
	time.sleep(1)
	asyncio.run(WEIGHERS[instance_name]["node_sockets"][instance_node].manager_realtime.broadcast(last_pesata.dict()))
 
def Callback_TarePTareZero(instance_name: str, instance_node: Union[str, None], ok_value: str):
	global WEIGHERS
	result = {"command_executend": ok_value}
	asyncio.run(WEIGHERS[instance_name]["node_sockets"][instance_node].manager_realtime.broadcast(result))

def Callback_DataInExecution(instance_name: str, instance_node: Union[str, None], data_in_execution: DataInExecution):
	global WEIGHERS
	if asyncio.get_event_loop().is_running():
		asyncio.create_task(WEIGHERS[instance_name]["node_sockets"][instance_node].manager_realtime.broadcast(data_in_execution.dict()))	
	else:
		loop = asyncio.get_event_loop()
		loop.run_until_complete(WEIGHERS[instance_name]["node_sockets"][instance_node].manager_realtime.broadcast(data_in_execution.dict()))

def Callback_ActionInExecution(instance_name: str, instance_node: Union[str, None], action_in_execution: str):
	global WEIGHERS
	result = {"command_in_executing": action_in_execution}
	if asyncio.get_event_loop().is_running():
		asyncio.create_task(WEIGHERS[instance_name]["node_sockets"][instance_node].manager_realtime.broadcast(result))
	else:
		loop = asyncio.get_event_loop()
		loop.run_until_complete(WEIGHERS[instance_name]["node_sockets"][instance_node].manager_realtime.broadcast(result))

def Callback_Cardcode(cardcode: str):
	result = {"cardcode": cardcode}
	asyncio.run(manager_data_in_execution.broadcast(result))
	lb_log.info(cardcode)

# Function to create a new instance of weigher module
def createIstanceWeigher(name, configuration):
	global WEIGHERS

	module = WeigherInstance(name)
	if configuration["connection"] is None:
		configuration["connection"] = Connection(**{})
	weigher_configuration = Configuration(**configuration)
	module.initialize(configuration=weigher_configuration)
	module.setAction(
		cb_realtime=Callback_Realtime,
		cb_diagnostic=Callback_Diagnostic, 
		cb_weighing=Callback_Weighing,
		cb_tare_ptare_zero=Callback_TarePTareZero,
		cb_data_in_execution=Callback_DataInExecution,
		cb_action_in_execution=Callback_ActionInExecution
 	)
	# Inizializza il modulo.
	module.init()  # Inizializzazione del modulo
	# Crea e avvia il thread del modulo.
	thread = createThread(module.start)
	nodes_sockets = {}
	for node in weigher_configuration.nodes:
		nodes_sockets[node.node] = NodeConnectionManager()
	WEIGHERS[name] = {
		"module": module, 
		"thread": thread,
		"node_sockets": nodes_sockets
	}
	startThread(thread)

async def deleteInstanceWeigher(name):
	global WEIGHERS

	deleted = False
 
	if name in WEIGHERS:
		for node in WEIGHERS[name]["node_sockets"]:
			await WEIGHERS[name]["node_sockets"][node].manager_realtime.broadcast("Weigher instance deleted")
			WEIGHERS[name]["node_sockets"][node].manager_realtime.disconnect_all()
			await WEIGHERS[name]["node_sockets"][node].manager_diagnostic.broadcast("Weigher instance deleted")
			WEIGHERS[name]["node_sockets"][node].manager_diagnostic.disconnect_all()
			await WEIGHERS[name]["node_sockets"][node].manager_execution.broadcast("Weigher instance deleted")
			WEIGHERS[name]["node_sockets"][node].manager_execution.disconnect_all()
		closeThread(WEIGHERS[name]["thread"], WEIGHERS[name]["module"])
		deleted = True
	return deleted

# create connectio manager of weight real time
class ConnectionManager:
	def __init__(self):
		self.active_connections: list[WebSocket] = []

	async def connect(self, websocket: WebSocket):
		await websocket.accept()
		self.active_connections.append(websocket)

	def disconnect(self, websocket: WebSocket):
		self.active_connections.remove(websocket)

	def disconnect_all(self):
		for connection in self.active_connections:
			self.disconnect(connection)

	async def send_personal_message(self, message: str, websocket: WebSocket):
		try:
			await websocket.send_text(message)
		except Exception:
			self.disconnect(websocket)

	async def broadcast(self, message: str):
		for connection in self.active_connections:
			try:
				await connection.send_json(message)
			except Exception:
				#print("client down")
				self.disconnect(connection)

class InstanceNameDTO(BaseModel):
	name: str

class InstanceNameNodeDTO(InstanceNameDTO):
	node: Optional[str] = None

class NodeConnectionManager:
	def __init__(self):
		self.manager_realtime = ConnectionManager()
		self.manager_diagnostic = ConnectionManager()
		self.manager_execution = ConnectionManager()

def get_query_params_name(params: InstanceNameDTO = Depends()):
	global WEIGHERS

	if params.name not in WEIGHERS:
		raise HTTPException(status_code=404, detail='Name instance does not exist')
	return params
 
def get_query_params_name_node(params: InstanceNameNodeDTO = Depends()):
	global WEIGHERS

	if params.name not in WEIGHERS:
		raise HTTPException(status_code=404, detail='Name instance does not exist')
	if WEIGHERS[params.name]["module"].getNode(params.node) is None:
		raise HTTPException(status_code=404, detail='Node not exist')
	return params
# ==============================================================

async def get_query_params(request: Request) -> Dict[str, Union[str, int]]:
	"""
	Converts URL query parameters into a dictionary
	"""
	return dict(request.query_params)

# ==== MAINPRGLOOP =============================================
# funzione che si connette a redis, setta i moduli e imposta le callback da richiamare dentro i moduli
def mainprg():
	global data_in_execution
	global app
	global WEIGHERS
	global base_dir_templates
	global templates
	global thread_ssh_tunnel

	@app.get("/list/anagrafic/{anagrafic}")
	async def getListAnagrafic(anagrafic: str, query_params: Dict[str, Union[str, int]] = Depends(get_query_params)):
		if anagrafic not in required_columns:
			return HTTPException(status_code=400, detail=f"Anagrafic {anagrafic} is not supported")
		try:
			lb_log.warning(query_params)
			data = filter_data(anagrafic, query_params)
			return data
		except Exception as e:
			return HTTPException(status_code=400, detail=f"{e}")

	@app.post("/anagrafic/{anagrafic}")
	async def addAnagrafic(anagrafic: str, body: Union[VehicleDTO, SocialReasonDTO, MaterialDTO]):
		if anagrafic not in required_columns:
			return HTTPException(status_code=400, detail=f"Anagrafic {anagrafic} is not supported")

		# Definizione delle colonne richieste
		required_dto = required_dtos[anagrafic]

		if not isinstance(body, required_dto):
			return HTTPException(status_code=400, detail=f"Invalid body for {anagrafic}")

		try:
			add_data(anagrafic, body.dict())
		except e:
			return e

		return {"message": "Data added successfully"}

	@app.patch("/anagrafic/{anagrafic}/{id}")
	async def setAnagrafic(anagrafic: str, id: int, body: Union[VehicleDTO, SocialReasonDTO, MaterialDTO]):
		if anagrafic not in required_columns:
			return HTTPException(status_code=400, detail=f"Anagrafic {anagrafic} is not supported")

		# Definizione delle colonne richieste
		required_dto = required_dtos[anagrafic]

		if not isinstance(body, required_dto):
			return HTTPException(status_code=400, detail=f"Invalid body for {anagrafic}")

		try:
			update_data(anagrafic, id, body.dict(), True)
		except Exception as e:
			return HTTPException(status_code=400, detail=f"{e}")

		return {"message": "Data updated successfully"}

	@app.delete("/anagrafic/{anagrafic}/{id}")
	async def deleteAnagrafic(anagrafic: str, id: int):
		if anagrafic not in required_columns:
			return HTTPException(status_code=400, detail=f"Anagrafic {anagrafic} is not supported")

		try:
			delete_data(anagrafic, id, True)
		except Exception as e:
			return HTTPException(status_code=400, detail=f"{e}")
		return {"message": "Data deleted successfully"}

	@app.delete("/all/anagrafic/{anagrafic}")
	async def deleteAllAnagrafic(anagrafic: str):
		if anagrafic not in required_columns:
			return HTTPException(status_code=400, detail=f"Anagrafic {anagrafic} is not supported")
		try:
			length = delete_all_data(anagrafic, True)
			return {"message": f"records deleted successfully"}
		except Exception as e:
			return HTTPException(status_code=400, detail=f"{e}")

	@app.post("/upload-file/{anagrafic}")
	async def upload_file(anagrafic: str, file: UploadFile = File(...)):
		# Verifica l'estensione del file
		if file.content_type not in ["text/csv", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
			return HTTPException(status_code=400, detail="File type not supported")

		try:
			# Leggi il file in base al tipo di contenuto
			if file.content_type == "text/csv":
				df = pd.read_csv(file.file)
			elif file.content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
				df = pd.read_excel(file.file)

			# Rimuovi le colonne senza titolo (solitamente con nome 'Unnamed') e verifica che non ci siano
			df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

			if anagrafic not in required_columns:
				return HTTPException(status_code=400, detail=f"Anagrafic {anagrafic} is not supported")

			# Definizione delle colonne richieste
			required_column = required_columns[anagrafic]

			allowed_columns = set(required_column.keys())

			# Verifica se ci sono colonne non previste
			if not set(df.columns).issubset(allowed_columns):
				unexpected_columns = set(df.columns) - allowed_columns
				return HTTPException(status_code=400, detail=f"Unexpected columns found: {', '.join(unexpected_columns)}")

			# Aggiungi le colonne mancanti con valore None e verifica i tipi delle colonne esistenti
			for column, expected_type in required_column.items():
				if column not in df.columns:
					df[column] = None  # Colonna assente nel file, aggiunta con valori null
				else:
					# Verifica il tipo di dati della colonna esistente e consenti celle vuote
					if not df[column].map(lambda x: pd.isna(x) or isinstance(x, expected_type)).all():
						return HTTPException(status_code=400, detail=f"Column '{column}' must be of type {expected_type} if present")

			# Sostituisci valori NaN, Inf e -Inf con None
			df = df.replace([np.nan, np.inf, -np.inf], None)

		except Exception as e:
			# Log dell'errore e risposta HTTP 500
			lb_log.error(f"Error reading file: {e}")
			raise HTTPException(status_code=500, detail="Error reading file") from e

		# Converti i dati in JSON
		data = df.to_dict(orient="records")

		try:
			# Salva i dati nel database
			length = load_records_into_db(anagrafic, data)

			return {"message": f"{length} records loaded successfully"}
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
		status, status_modope, status_command, error_message = WEIGHERS[instance.name]["module"].setModope(node=instance.node, modope="REALTIME")

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
		status, status_modope, status_command, error_message = WEIGHERS[instance.name]["module"].setModope(node=instance.node, modope="DIAGNOSTICS")
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
		status, status_modope, status_command, error_message = WEIGHERS[instance.name]["module"].setModope(node=instance.node, modope="OK")
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
		status, status_modope, status_command, error_message = WEIGHERS[instance.name]["module"].setModope(node=instance.node, modope="WEIGHING", data_assigned=None)
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
			data = WEIGHERS[instance.name]["module"].getDataInExecution(node=instance.node)
		status, status_modope, status_command, error_message = WEIGHERS[instance.name]["module"].setModope(node=instance.node, modope="WEIGHING", data_assigned=data)
		if status_command:
			WEIGHERS[instance.name]["module"].deleteDataInExecution(node=instance.node)
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
		status, status_modope, status_command, error_message = WEIGHERS[instance.name]["module"].setModope(node=instance.node, modope="TARE")
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
		status, status_modope, status_command, error_message = WEIGHERS[instance.name]["module"].setModope(node=instance.node, modope="PRESETTARE", presettare=tare)
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
		status, status_modope, status_command, error_message = WEIGHERS[instance.name]["module"].setModope(node=instance.node, modope="ZERO")
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
	async def GetDataInExecution(instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
		status, data = WEIGHERS[instance.name]["module"].getDataInExecution(node=instance.node)
		return {
			"instance": instance,
			"data_in_execution": data,
			"status": status
		}

	@app.patch("/set/data_in_execution")
	async def SetDataInExecution(data_in_execution: DataInExecutionDTO = {}, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
		status, data = WEIGHERS[instance.name]["module"].setDataInExecution(node=instance.node, data_in_execution=data_in_execution)
		node_found = [n for n in lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"] if n["node"] == instance.node]
		index_node_found = lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"].index(node_found[0])
		lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"][index_node_found]["data_in_execution"] = data
		lb_config.saveconfig()
		return {
			"instance": instance,
			"data_in_execution": data,
			"status": status
		}

	@app.delete("/delete/data_in_execution")
	async def DeleteDataInExecution(instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
		status, data = WEIGHERS[instance.name]["module"].deleteDataInExecution(node=instance.node)
		node_found = [n for n in lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"] if n["node"] == instance.node]
		index_node_found = lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"].index(node_found[0])
		lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"][index_node_found]["data_in_execution"] = data
		lb_config.saveconfig()
		return {
			"instance": instance,
			"data_in_execution": data,
			"status": status
		}

	@app.get("/all/config_weigher")
	async def GetConfigWeighers():
		return lb_config.g_config["app_api"]["weighers"]

	@app.get("/config_weigher")
	async def GetConfigWeigher(instance: InstanceNameDTO = Depends(get_query_params_name)):
		response = WEIGHERS[instance.name]["module"].getConfig()
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
		WEIGHERS[instance.name]["module"].deleteConfig()
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
		responses = WEIGHERS[instance.name]["module"].getNodes()
		response = {
	  		"instance_name": instance.name,
			"nodes": responses
		}
		return response

	@app.get("/config_weigher/node")
	async def GetConfigWeigherNode(instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
		response = WEIGHERS[instance.name]["module"].getNode(instance.node)
		if not response:
			raise HTTPException(status_code=404, detail='Not found')
		response["instance_name"] = instance.name
		return response

	@app.post("/config_weigher/node")
	async def AddConfigWeigherNode(node: SetupWeigherDTO, instance: InstanceNameDTO = Depends(get_query_params_name)):
		if node.node in lb_config.g_config["app_api"]["weighers"][instance.name]["nodes"]:
			raise HTTPException(status_code=400, detail='Node just exist')
		response = WEIGHERS[instance.name]["module"].addNode(node)
		if response:
			WEIGHERS[instance.name]["module"].setActionNode(
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
		response = WEIGHERS[instance.name]["module"].setNode(instance.node, setup)
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
		node_removed = WEIGHERS[instance.name]["module"].deleteNode(instance.node)
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
		nodes_removed = WEIGHERS[instance.name]["module"].deleteNodes()
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
		conn = WEIGHERS[instance.name]["module"].getConnection()
		time_between_actions = WEIGHERS[instance.name]["module"].getTimeBetweenActions()
		if conn:
			return {
				"instance": instance,
	   			"connection": conn,
				"time_between_actions": time_between_actions
			}
		raise HTTPException(status_code=404, detail='Not found')

	@app.patch("/config_weigher/connection")
	async def SetConfigWeigherConnection(connection: Union[SerialPort, Tcp], instance: InstanceNameDTO = Depends(get_query_params_name)):
		conn = WEIGHERS[instance.name]["module"].setConnection(connection)
		time_between_actions = WEIGHERS[instance.name]["module"].getTimeBetweenActions()
		lb_config.g_config["app_api"]["weighers"][instance.name]["connection"] = conn
		lb_config.saveconfig()
		return {
			"instance": instance,
			"connection": conn,
			"time_between_actions": time_between_actions,
		}

	@app.delete("/config_weigher/connection")
	async def DeleteConfigWeigherConnection(instance: InstanceNameDTO = Depends(get_query_params_name)):
		if lb_config.g_config["app_api"]["weighers"][instance.name]["connection"] != None:
			conn = WEIGHERS[instance.name]["module"].deleteConnection()
			lb_config.g_config["app_api"]["weighers"][instance.name]["connection"] = None
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
		result = WEIGHERS[instance.name]["module"].setTimeBetweenActions(time=time)
		connection = WEIGHERS[instance.name]["module"].getConnection()
		lb_config.g_config["app_api"]["weighers"][instance.name]["time_between_actions"] = result
		lb_config.saveconfig()
		return {
			"instance": instance,
			"connection": connection,
			"time_between_actions": result
		}

	@app.websocket("/realtime")
	async def websocket_endpoint(websocket: WebSocket, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
		await WEIGHERS[instance.name]["node_sockets"][instance.node].manager_realtime.connect(websocket)
		while True:
			if len(WEIGHERS[instance.name]["node_sockets"][instance.node].manager_realtime.active_connections) > 0:
				status = WEIGHERS[instance.name]["module"].getNode(instance.node)["status"]
				if status == 200:
					modope_in_execution = WEIGHERS[instance.name]["module"].getModope(instance.node)
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
						WEIGHERS[instance.name]["module"].setModope(instance.node, "REALTIME")
				else:
					message = "Pesa scollegata"
					if status == 301:
						message = "Connessione non settata"
					elif status == 201:
						message = "Protocollo pesa non valido"
					await WEIGHERS[instance.name]["node_sockets"][instance.node].manager_realtime.broadcast({
		 				"status":"--",
			 			"type":"--",
						"net_weight": message,
				  		"gross_weight":"--",
						"tare":"--",
					 	"unite_measure": str(status)
					})
			else:
				WEIGHERS[instance.name]["module"].setModope(instance.node, "OK")
				break
			await asyncio.sleep(1)

	@app.websocket("/diagnostic")
	async def websocket_diagnostic(websocket: WebSocket, instance: InstanceNameNodeDTO = Depends(get_query_params_name_node)):
		await WEIGHERS[instance.name]["node_sockets"][instance.node].manager_diagnostic.connect(websocket)
		try:
			if len(WEIGHERS[instance.name]["node_sockets"][instance.node].manager_diagnostic.active_connections) == 1:
				if WEIGHERS[instance.name]["module"] is not None:
					WEIGHERS[instance.name]["module"].diagnostic()
			while True:
				await asyncio.sleep(0.2)
		except WebSocketDisconnect:
			await WEIGHERS[instance.name]["node_sockets"][instance.node].manager_diagnostic.disconnect(websocket)
			if len(WEIGHERS[instance.name]["node_sockets"][instance.node].manager_diagnostic.active_connections) == 0 and len(WEIGHERS[instance.name]["websockets"].manager_realtime.active_connections) >= 1:
				if WEIGHERS[instance.name]["module"] is not None:
					WEIGHERS[instance.name]["module"].realTime()

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
	global WEIGHERS
	global ssh_client
	
	for weigher in WEIGHERS:  # Per ogni modulo
		lb_log.info("..killing weigher configuration: %s" % weigher)  # Logga un messaggio informativo
		asyncio.run(deleteInstanceWeigher(weigher))
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
	global weigher_modules
	global rfid_modules
	global WEIGHERS
	global base_dir_templates
	global templates
	global ssh_client

	WEIGHERS = {}

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

	# Carica thread per i moduli esterni.
	lb_log.info("loading weighers...")
	for instance_name, instance_data in lb_config.g_config["app_api"]["weighers"].items():
		createIstanceWeigher(instance_name, instance_data)

	ssh_client = None
	if lb_config.g_config["app_api"]["ssh_client"]:
		ssh_client = lb_config.g_config["app_api"]["ssh_client"]
		ssh_client["local_port"] = lb_config.g_config["app_api"]["port"]
		ssh_client = createThread(ssh_tunnel, (SshClientConnection(**ssh_client),))
		startThread(ssh_client)

	lb_database.init()

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