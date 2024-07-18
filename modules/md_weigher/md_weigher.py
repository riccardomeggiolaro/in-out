# ==============================================================
# = Module......: md_dgt1					   =
# = Description.: Interfaccia di pesatura con più terminali =
# = Author......: Riccardo Meggiolaro				   =
# = Last rev....: 0.0002					   =
# ==============================================================

from modules.md_weigher.globals import connection, weighers, time_between_actions

# ==== LIBRERIE DA IMPORTARE ===================================
import inspect
__frame = inspect.currentframe()
namefile = inspect.getfile(__frame).split("/")[-1].replace(".py", "")
import lib.lb_log as lb_log  # noqa: E402
import lib.lb_config as lb_config  # noqa: E402
from typing import Callable, Union  # noqa: E402
import time  # noqa: E402
from lib.lb_system import SerialPort, Tcp  # noqa: E402
from modules.md_weigher.types import DataInExecution  # noqa: E402
from modules.md_weigher.dto import SetupWeigherDTO, ConfigurationDTO, ChangeSetupWeigherDTO  # noqa: E402
from modules.md_weigher.terminals.dgt1 import Dgt1  # noqa: E402
from modules.md_weigher.globals import terminalsClasses  # noqa: E402
# ==============================================================

# ==== INIT ====================================================
# funzione che dichiara tutte le globali
def init():
	lb_log.info("init")
# ==============================================================

# ==== MAINPRGLOOP =============================================
# funzione che scrive e legge in loop conn e in base alla stringa ricevuta esegue funzioni specifiche
def mainprg():
	while lb_config.g_enabled:
		for weigher in weighers:
			time_start = time.time()
			status, command, response, error = weigher.main()
			time_end = time.time()
			time_execute = time_end - time_start
			timeout = max(0, time_between_actions - time_execute)
			time.sleep(timeout)
			lb_log.info(f"Status: {status}, Command: {command}, Response; {response}, Error: {error}")
			if weigher.diagnostic.status == 301:
				connection.connection.close()
				status, error_message = connection.connection.try_connection()
				if status:
					for w in weighers:
						time_start = time.time()
						w.initialize()
						time_end = time.time()
						time_execute = time_end - time_start
						timeout = max(0, time_between_actions - time_execute)
						time.sleep(timeout)
				else:
					for w in weighers:
						w.diagnostic.status = 301
					connection.connection.close()
# ==============================================================

# ==== START ===================================================
# funzione che fa partire il modulo
def start():
	lb_log.info("start")
	mainprg() # fa partire la funzione che scrive e legge la conn in loop
	lb_log.info("end")
	# se la globale conn è di tipo conn ed è aperta la chiude
# ==============================================================

def stop():
	result = connection.deleteConnection()
	lb_log.info(f"Result {result}")

# ==== FUNZIONI RICHIAMABILI DA MODULI ESTERNI =================
def initialize(configuration: ConfigurationDTO):
	global time_between_actions
	lb_log.info("initialize")
	# inizializzazione della conn
	connected, message = False, None
	connection.connection = configuration.connection
	connected, message = connection.connection.try_connection()
	time_between_actions = configuration.time_between_actions
	for node in configuration.nodes:
		node_dict = node.dict()
		n = Dgt1(**node_dict)
		n.initialize()
		weighers.append(n)
		# ottenere firmware e nome del modello
	return connected, message # ritorno True o False in base se status della pesa è 200

def getConfig():
	conn = connection.getConnection()
	nodes_dict = [n.getSetup() for n in weighers]
	return {
		"connection": conn,
		"nodes": nodes_dict,
		"time_between_actions": time_between_actions
	}

def deleteConfig():
	global weighers
	global time_between_actions
	connection.deleteConnection()
	weighers = []
	time_between_actions = 0
	return getConfig()

def getConnection():
	return connection.getConnection()

def setConnection(conn: Union[SerialPort, Tcp]):
	deleteConnection()
	connected = connection.setConnection(connection=conn)
	for weigher in weighers:
		weigher.initialize()
	return connected

def deleteConnection():
	response = connection.deleteConnection()
	return response

def getNodes():
	global weighers
	nodes_dict = []
	for weigher in weighers:
		n = weigher.getSetup()
		nodes_dict.append(n)
	return nodes_dict

def getNode(node: Union[str, None]):
	result = None
	data = [n for n in weighers if n.node == node]
	if len(data) > 0:
		result = data[0].getSetup()
	return result

def addNode(node: SetupWeigherDTO):
	node_to_add = node.dict()
	terminalClass = [terminal for terminal in terminalsClasses if terminal["terminal"] == node.terminal]			
	n = terminalClass[0]["class"](**node_to_add)
	if connection is not None:
		n.initialize()
	weighers.append(n)
	return n.getSetup()

def setNode(node: Union[str, None], setup: ChangeSetupWeigherDTO = {}):
	node_found = [n for n in weighers if n.node == node]
	result = None
	if len(node_found) != 0:
		result = node_found[0].setSetup(setup)
		if setup.terminal:
			node_to_changed = SetupWeigherDTO(**result)
			deleteNode(node_to_changed.node)
			addNode(node_to_changed)
		else:
			node_found[0].initialize()
	return result

def deleteNode(node: Union[str, None]):
	node_found = [n for n in weighers if n.node == node]
	response = False
	if len(node_found) != 0:
		weighers.remove(node_found[0])
		response = True
	return response

def setTimeBetweenActions(time: Union[int, float]):
    global time_between_actions
    time_between_actions = time
    return time_between_actions

def getDataInExecution(node: Union[str, None]):
	node_found = [n for n in weighers if n.node == node]
	if len(node_found) > 0:
		return node_found[0].getDataInExecution()
	return node_found

def setDataInExecution(node: Union[str, None], data_in_execution: DataInExecution):
	node_found = [n for n in weighers if n.node == node]
	if len(node_found) > 0:
		return node_found[0].setDataInExecution(data_in_execution)
	return node_found

def deleteDataInExecution(node: Union[str, None]):
	node_found = [n for n in weighers if n.node == node]
	if len(node_found) > 0:
		return node_found[0].deleteDataInExecution()
	return node_found

# Funzione per settare le funzioni di callback
# I parametri possono essere omessi o passati come funzioni che hanno un solo parametro come
# 	1) REALTIME 
# 			{
# 				"status": "Pesa scollegata", 
# 				"type": "",
# 				"net_weight": "", 
# 				"gross_weight": "", 
# 				"tare": "",
# 				"unite_measure": ""
# 			}
# 	2) DIAGNOSTICS
# 			{
#	 			"status": "Pesa scollegata",
# 				"firmware": "",
# 				"model_name": "",
# 				"serial_number": "",
# 				"vl": "",
# 				"rz": ""
# 			}
# 	3) WEIGHING
# 			{
# 				"net_weight": "",
# 				"gross_weight": "",
# 				"tare": "",
# 				"unite_misure": "",
# 				"pid": "",
# 				"bil": "",
# 				"status": ""
#	 		}
#   4) OK
#		   string

# funzione per impostare la diagnostica continua
# DIAGNOSTICS, REALTIME, WEIGHING, TARE, PRESETTARE, ZERO
def setModope(node: Union[str, None], modope, presettare=0, data_assigned = None):
	node_found = [n for n in weighers if n.node == node]
	status, status_modope, command_execute = False, None, False
	if len(node_found) != 0:
		status = True
		status_modope = node_found[0].setModope(mod=modope, presettare=presettare, data_assigned=data_assigned)
		command_execute = status_modope == 100
	return status, status_modope, command_execute

def setActionNode(node: Union[str, None], cb_realtime: Callable[[dict], any] = None, cb_diagnostic: Callable[[dict], any] = None, cb_weighing: Callable[[dict], any] = None, cb_tare_ptare_zero: Callable[[str], any] = None):
	global weighers
	node_found = [n for n in weighers if n.node == node]
	if len(node_found) > 0:
		node_found[0].setAction(
			cb_realtime=cb_realtime,
			cb_diagnostic=cb_diagnostic,
			cb_weighing=cb_weighing,
			cb_tare_ptare_zero=cb_tare_ptare_zero
		)

def setAction(cb_realtime: Callable[[dict], any] = None, cb_diagnostic: Callable[[dict], any] = None, cb_weighing: Callable[[dict], any] = None, cb_tare_ptare_zero: Callable[[str], any] = None):
	global weighers
	for weigher in weighers:
		weigher.setAction(cb_realtime=cb_realtime, cb_diagnostic=cb_diagnostic, cb_weighing=cb_weighing, cb_tare_ptare_zero=cb_tare_ptare_zero)
# ==============================================================