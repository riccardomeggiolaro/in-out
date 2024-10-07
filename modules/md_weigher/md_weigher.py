# ==============================================================
# = Module......: md_dgt1					   =
# = Description.: Interfaccia di pesatura con più terminali =
# = Author......: Riccardo Meggiolaro				   =
# = Last rev....: 0.0002					   =
# ==============================================================

# ==== LIBRERIE DA IMPORTARE ===================================
import inspect
__frame = inspect.currentframe()
namefile = inspect.getfile(__frame).split("/")[-1].replace(".py", "")
import libs.lb_log as lb_log
import libs.lb_config as lb_config
from typing import Callable, Union
import time
from libs.lb_system import SerialPort, Tcp, Connection
from modules.md_weigher.types import DataInExecution
from modules.md_weigher.dto import SetupWeigherDTO, ConfigurationDTO, ChangeSetupWeigherDTO
from modules.md_weigher.globals import terminalsClasses
from libs.lb_system import ConfigConnection
from modules.md_weigher.terminals.dgt1 import Dgt1
# ==============================================================

terminalsClasses["dgt1"] = Dgt1

class WeigherInstance:
	def __init__(self, name):
		self.m_enabled = True
		self.name = name
		self.nodes = []
		self.connection = ConfigConnection()
		self.time_between_actions = 0

	# ==== INIT ====================================================
	# funzione che dichiara tutte le globali
	def init(self):
		lb_log.info("init")
	# ==============================================================

	# ==== MAINPRGLOOP =============================================
	# funzione che scrive e legge in loop conn e in base alla stringa ricevuta esegue funzioni specifiche
	def mainprg(self):
		while self.m_enabled:
			for node in self.nodes:
				if node.run:
					time_start = time.time()
					status, command, response, error = node.main()
					time_end = time.time()
					time_execute = time_end - time_start
					timeout = max(0, self.time_between_actions - time_execute)
					time.sleep(timeout)
					lb_log.info(f"Node: {node.node}, Status: {status}, Command: {command}, Response; {response}, Error: {error}")
					if node.diagnostic.status == 301:
						self.connection.connection.close()
						status, error_message = self.connection.connection.try_connection()
						for w in self.nodes:
							if status:
								time_start = time.time()
								w.initialize()
								time_end = time.time()
								time_execute = time_end - time_start
								timeout = max(0, self.time_between_actions - time_execute)
								time.sleep(timeout)
							else:
								self.connection.connection.close()
	# ==============================================================

	# ==== START ===================================================
	# funzione che fa partire il modulo
	def start(self):
		lb_log.info("start")
		self.mainprg() # fa partire la funzione che scrive e legge la conn in loop
		lb_log.info("end")
		# se la globale conn è di tipo conn ed è aperta la chiude
	# ==============================================================

	def stop(self):
		self.m_enabled = False
		result = self.connection.deleteConnection()

	# ==== FUNZIONI RICHIAMABILI DA MODULI ESTERNI =================
	def initialize(self, configuration: ConfigurationDTO):
		lb_log.info("initialize")
		# inizializzazione della conn
		connected, message = False, None
		self.connection.connection = configuration.connection
		connected, message = self.connection.connection.try_connection()
		self.time_between_actions = configuration.time_between_actions
		for node in configuration.nodes:
			node_dict = node.dict()
			n = terminalsClasses[node.terminal](
       			self_config=self, 
          		max_weight=node.max_weight, 
            	min_weight=node.min_weight, 
             	division=node.division, 
              	maintaine_session_realtime_after_command=node.maintaine_session_realtime_after_command,
               	diagnostic_has_priority_than_realtime=node.diagnostic_has_priority_than_realtime,
                node=node.node, 
                terminal=node.terminal,
                run=node.run
            )
			n.initialize()
			self.nodes.append(n)
		return connected, message # ritorno True o False in base se status della pesa è 200

	def getConfig(self):
		conn = self.connection.getConnection()
		nodes_dict = [n.getSetup() for n in self.nodes]
		return {
			"connection": conn,
			"time_between_actions": self.time_between_actions,
			"nodes": nodes_dict
		}

	def deleteConfig(self):
		self.connection.deleteConnection()
		self.nodes = []
		self.time_between_actions = 0
		return self.getConfig()

	def getConnection(self):
		return self.connection.getConnection()

	def setConnection(self, conn: Union[SerialPort, Tcp]):
		self.deleteConnection()
		conn = self.connection.setConnection(connection=conn)
		for weigher in self.nodes:
			weigher.initialize()
		return conn

	def deleteConnection(self):
		return self.connection.deleteConnection()

	def getNodes(self):
		nodes_dict = []
		for weigher in self.nodes:
			n = weigher.getSetup()
			nodes_dict.append(n)
		return nodes_dict

	def getNode(self, node: Union[str, None]):
		result = None
		data = [n for n in self.nodes if n.node == node]
		if len(data) > 0:
			result = data[0].getSetup()
		return result

	def addNode(self, node: SetupWeigherDTO):
		n = terminalsClasses[node.terminal](
				self_config=self, 
          		max_weight=node.max_weight, 
            	min_weight=node.min_weight, 
             	division=node.division, 
              	maintaine_session_realtime_after_command=node.maintaine_session_realtime_after_command,
               	diagnostic_has_priority_than_realtime=node.diagnostic_has_priority_than_realtime,
                node=node.node, 
                terminal=node.terminal,
                run=node.run
		)
		if self.connection is not None:
			n.initialize()
		self.nodes.append(n)
		return n.getSetup()

	def setNode(self, node: Union[str, None], setup: ChangeSetupWeigherDTO = {}):
		node_found = [n for n in self.nodes if n.node == node]
		result = None
		if len(node_found) != 0:
			result = node_found[0].setSetup(setup)
			if setup.terminal:
				node_to_changed = SetupWeigherDTO(**result)
				self.deleteNode(node_to_changed.node)
				self.addNode(node_to_changed)
		return result

	def deleteNode(self, node: Union[str, None]):
		node_found = [n for n in self.nodes if n.node == node]
		response = False
		if len(node_found) != 0:
			self.nodes.remove(node_found[0])
			response = True
		return response

	def deleteNodes(self):
		response = False
		e_weighers = [n for n in self.nodes if n.node]
		if len(e_weighers) != 0:
			for weigher in e_weighers:
				self.nodes.remove(weigher)
			response = True
		return response

	def getTimeBetweenActions(self):
		return self.time_between_actions

	def setTimeBetweenActions(self, time: Union[int, float]):
		self.time_between_actions = time
		return self.time_between_actions

	def getDataInExecution(self, node: Union[str, None]):
		node_found = [n for n in self.nodes if n.node == node]
		if len(node_found) > 0:
			data = node_found[0].getDataInExecution()
			status = node_found[0].diagnostic.status
			return status, data
		return node_found

	def setDataInExecution(self, node: Union[str, None], data_in_execution: DataInExecution):
		node_found = [n for n in self.nodes if n.node == node]
		if len(node_found) > 0:
			data = node_found[0].setDataInExecution(data_in_execution)
			status = node_found[0].diagnostic.status
			return status, data
		return node_found

	def deleteDataInExecution(self, node: Union[str, None]):
		node_found = [n for n in self.nodes if n.node == node]
		if len(node_found) > 0:
			data = node_found[0].deleteDataInExecution()
			status = node_found[0].diagnostic.status
			return status, data
		return node_found

	def getModope(self, node: Union[str, None]):
		node_found = [n for n in self.nodes if n.node == node]
		if len(node_found) != 0:
			return node_found[0].modope_to_execute

	def setModope(self, node: Union[str, None], modope, presettare=0, data_assigned = None):
		node_found = [n for n in self.nodes if n.node == node]
		status, status_modope, command_execute, error_message = None, None, False, None
		if len(node_found) != 0:
			status_modope, error_message = node_found[0].setModope(mod=modope, presettare=presettare, data_assigned=data_assigned)
			status = node_found[0].diagnostic.status
			command_execute = status_modope == 100
		return status, status_modope, command_execute, error_message

	def setActionNode(self, node: Union[str, None], cb_realtime: Callable[[dict], any] = None, cb_diagnostic: Callable[[dict], any] = None, cb_weighing: Callable[[dict], any] = None, cb_tare_ptare_zero: Callable[[str], any] = None):
		global nodes
		node_found = [n for n in self.nodes if n.node == node]
		if len(node_found) > 0:
			node_found[0].setAction(
				cb_realtime=cb_realtime,
				cb_diagnostic=cb_diagnostic,
				cb_weighing=cb_weighing,
				cb_tare_ptare_zero=cb_tare_ptare_zero
			)

	def setAction(self, cb_realtime: Callable[[dict], any] = None, cb_diagnostic: Callable[[dict], any] = None, cb_weighing: Callable[[dict], any] = None, cb_tare_ptare_zero: Callable[[str], any] = None):
		for weigher in self.nodes:
			weigher.setAction(cb_realtime=cb_realtime, cb_diagnostic=cb_diagnostic, cb_weighing=cb_weighing, cb_tare_ptare_zero=cb_tare_ptare_zero)
	# ==============================================================