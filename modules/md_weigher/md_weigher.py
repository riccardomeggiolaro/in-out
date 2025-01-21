# ==============================================================
# = Module......: md_dgt1					   =
# = Description.: Interfaccia di pesatura con più terminali =
# = Author......: Riccardo Meggiolaro				   =
# = Last rev....: 0.0002					   =
# ==============================================================

# ==== LIBRERIE DA IMPORTARE ===================================
import libs.lb_log as lb_log
import libs.lb_config as lb_config
from typing import Callable, Union
import time
from libs.lb_system import SerialPort, Tcp
from modules.md_weigher.types import DataInExecution
from modules.md_weigher.dto import SetupWeigherDTO, ConfigurationDTO, ChangeSetupWeigherDTO, DataDTO, ChangeSetupWeigherDTO
from modules.md_weigher.globals import terminalsClasses
from libs.lb_system import ConfigConnection
from modules.md_weigher.terminals.dgt1 import Dgt1
from libs.lb_utils import createThread, startThread
from modules.md_weigher.types import Configuration, ConfigurationWithoutControls
from fastapi import HTTPException
# ==============================================================

name_module = "md_weigher"

terminalsClasses["dgt1"] = Dgt1

def init():
	global module_weigher
	lb_log.info("init")
	module_weigher = WeigherModule()
	lb_log.info("end")

def start():
	lb_log.info("start")
	while lb_config.g_config.g_enabled:
		time.sleep(1)
	lb_log.info("end")

class WeigherModule:
	def __init__(self):

		self.instances = {}

		for name, configuration in lb_config.g_config["app_api"]["weighers"].items():
			weigher_configuration = ConfigurationWithoutControls(**configuration)
			instance = WeigherInstance(name, weigher_configuration)
			self.instances[name] = instance
		
	def setApplicationCallback(
		self, 
		cb_realtime: Callable[[dict], any] = None, 
		cb_diagnostic: Callable[[dict], any] = None, 
		cb_weighing: Callable[[dict], any] = None, 
		cb_tare_ptare_zero: Callable[[str], any] = None,
		cb_data_in_execution: Callable[[str], any] = None,
		cb_action_in_execution: Callable[[str], any] = None):
		for name, instance in self.instances.items():
			instance.setAction(
				cb_realtime=cb_realtime, 
				cb_diagnostic=cb_diagnostic, 
				cb_weighing=cb_weighing, 
				cb_tare_ptare_zero=cb_tare_ptare_zero,
				cb_data_in_execution=cb_data_in_execution,
				cb_action_in_execution=cb_action_in_execution
			)

	def getAllInstance(self):
		instances = {}
		for name in self.instances:
			instances[name] = self.instances[name].getInstance()
		return instances

	def getInstance(self, name):
		instance = self.instances[name].getInstance()
		return {
			name: instance
       	}

	def createInstance(
     	self,
		configuration: ConfigurationDTO):
		details = []
		if configuration.name in self.getAllInstance():
			details.append({"type": "value_error", "loc": ["", "name"], "msg": "Nome già esistente", "input": configuration.name, "ctx": {"error":{}}})
		if details:
			raise HTTPException(status_code=400, detail=details)
		name = configuration.name
		weigher_configuration = Configuration(**configuration.dict())
		instance = WeigherInstance(name, weigher_configuration)
		self.instances[name] = instance
		instance_created = instance.getInstance()
		instance_to_save = instance_created.copy()
		del instance_to_save["connection"]["connected"]
		lb_config.g_config["app_api"]["weighers"][configuration.name] = instance_to_save
		lb_config.saveconfig()
		instance_created["name"] = configuration.name
		return instance_created

	def deleteInstance(
		self,
		name):
		self.instances[name].deleteInstance()
		self.instances.pop(name)
		lb_config.g_config["app_api"]["weighers"].pop(name)
		lb_config.saveconfig()

	def getAllInstanceNode(self, name):
		return self.instances[name].getNodes()

	def getInstanceNode(self, name, node):
		instance = self.instances[name].getNode(node)
		if instance:
			return {
				name: instance
			}
		else:
			return None

	def addInstanceNode(
    	self, 
     	name, 
      	setup: SetupWeigherDTO,
	  	cb_realtime: Callable[[dict], any] = None, 
	   	cb_diagnostic: Callable[[dict], any] = None, 
		cb_weighing: Callable[[dict], any] = None, 
		cb_tare_ptare_zero: Callable[[str], any] = None,
		cb_data_in_execution: Callable[[str], any] = None,
		cb_action_in_execution: Callable[[str], any] = None):
		details = []
		if any(setup.name == current_node["name"] for current_node in self.getAllInstanceNode(name=name)):
			details.append({"type": "value_error", "loc": ["", "name"], "msg": "Nome già esistente", "input": setup.name, "ctx": {"error":{}}})
		if any(setup.node == current_node["node"] for current_node in self.getAllInstanceNode(name=name)):
			details.append({"type": "value_error", "loc": ["", "node"], "msg": "Nodo già esistente", "input": setup.node, "ctx": {"error":{}}})
		if details:
			raise HTTPException(status_code=400, detail=details)
		node_created = self.instances[name].addNode(
			setup=setup,
			cb_realtime=cb_realtime,
			cb_diagnostic=cb_diagnostic,
			cb_weighing=cb_weighing,
			cb_tare_ptare_zero=cb_tare_ptare_zero,
			cb_data_in_execution=cb_data_in_execution,
			cb_action_in_execution=cb_action_in_execution
		)
		terminal_data = node_created["terminal_data"]
		status = node_created["status"]
		del node_created["terminal_data"]
		del node_created["status"]
		lb_config.g_config["app_api"]["weighers"][name]["nodes"].append(node_created)
		lb_config.saveconfig()
		node_created["terminal_data"] = terminal_data
		node_created["status"] = status
		return node_created

	def setInstanceNode(
		self,
  		name,
    	node,
     	setup: ChangeSetupWeigherDTO,
	  	cb_realtime: Callable[[dict], any] = None, 
	   	cb_diagnostic: Callable[[dict], any] = None, 
		cb_weighing: Callable[[dict], any] = None, 
		cb_tare_ptare_zero: Callable[[str], any] = None,
		cb_data_in_execution: Callable[[str], any] = None,
		cb_action_in_execution: Callable[[str], any] = None):
		details = []
		if any(setup.name == current_node["name"] for current_node in self.getAllInstanceNode(name=name)):
			details.append({"type": "value_error", "loc": ["", "name"], "msg": "Nome già esistente", "input": setup.name, "ctx": {"error":{}}})
		if any(setup.node == current_node["node"] for current_node in self.getAllInstanceNode(name=name)):
			details.append({"type": "value_error", "loc": ["", "node"], "msg": "Nodo già esistente", "input": setup.node, "ctx": {"error":{}}})
		if details:
			raise HTTPException(status_code=400, detail=details)
		node_set = self.instances[name].setNode(
      		node=node, 
        	setup=setup,
			cb_realtime=cb_realtime,
			cb_diagnostic=cb_diagnostic,
			cb_weighing=cb_weighing,
			cb_tare_ptare_zero=cb_tare_ptare_zero,
			cb_data_in_execution=cb_data_in_execution,
			cb_action_in_execution=cb_action_in_execution
		)
		lb_log.warning(node_set)
		node_found = [n for n in lb_config.g_config["app_api"]["weighers"][name]["nodes"] if n["node"] == node]
		index_node_found = lb_config.g_config["app_api"]["weighers"][name]["nodes"].index(node_found[0])
		terminal_data = node_set["terminal_data"]
		status = node_set["status"]
		del node_set["terminal_data"]
		del node_set["status"]
		lb_config.g_config["app_api"]["weighers"][name]["nodes"][index_node_found] = node_set
		lb_config.saveconfig()
		node_set["terminal_data"] = terminal_data
		node_set["status"] = status
		return node_set

	def deleteInstanceNode(
		self,
		name,
		node):
		node_removed = self.instances[name].deleteNode(node=node)
		node_found = [n for n in lb_config.g_config["app_api"]["weighers"][name]["nodes"] if n["node"] == node]
		lb_config.g_config["app_api"]["weighers"][name]["nodes"].remove(node_found[0])
		lb_config.saveconfig()

	def getInstanceConnection(self, name, delete_connected: bool = False):
		connection = self.instances[name].getConnection()
		if delete_connected:
			del connection["connected"]
		return connection

	def setInstanceConnection(self, name, conn: Union[SerialPort, Tcp]):
		conn_set = self.instances[name].setConnection(conn=conn)
		conn_to_save = conn_set.copy()
		del conn_to_save["connected"]
		lb_config.g_config["app_api"]["weighers"][name]["connection"] = conn_to_save
		lb_config.saveconfig()
		return conn_set

	def deleteInstanceConnection(self, name):
		conn_deleted = self.instances[name].deleteConnection()
		conn_to_save = conn_deleted.copy()
		del conn_to_save["connected"]
		lb_config.g_config["app_api"]["weighers"][name]["connection"] = conn_to_save
		lb_config.saveconfig()
		return conn_deleted

	def setInstanceTimeBetweenActions(self, name, time_between_actions):
		time = self.instances[name].setTimeBetweenActions(time=time_between_actions)
		lb_config.g_config["app_api"]["weighers"][name]["time_between_actions"] = time
		lb_config.saveconfig()
		return time

	def getModope(self, name, node: Union[str, None]):
		return self.instances[name].getModope(node=node)

	def setModope(self, name, node: Union[str, None], modope, presettare=0, data_assigned: Union[DataInExecution, int] = None):
		return self.instances[name].setModope(node=node, modope=modope, presettare=presettare, data_assigned=data_assigned)

	def getData(self, name, node: Union[str, None]):
		return self.instances[name].getData(node=node)

	def setData(self, name, node: Union[str, None], data_dto: DataDTO, call_callback):
		data_in_execution = DataInExecution(**data_dto.data_in_execution.dict())
		status, data_set = self.instances[name].setDataInExecution(node=node, data_in_execution=data_in_execution, call_callback=call_callback)
		if data_dto.id_selected.id is not None:
			status, data_set = self.instances[name].setIdSelected(node=node, new_id=data_dto.id_selected.id, call_callback=call_callback)
		node_found = [n for n in lb_config.g_config["app_api"]["weighers"][name]["nodes"] if n["node"] == node]
		index_node_found = lb_config.g_config["app_api"]["weighers"][name]["nodes"].index(node_found[0])
		lb_config.g_config["app_api"]["weighers"][name]["nodes"][index_node_found]["data"] = data_set
		lb_config.saveconfig()
		return status, data_set

	def deleteData(self, name, node: Union[str, None], call_callback):
		status, data = self.instances[name].deleteData(node=node, call_callback=call_callback)
		node_found = [n for n in lb_config.g_config["app_api"]["weighers"][name]["nodes"] if n["node"] == node]
		index_node_found = lb_config.g_config["app_api"]["weighers"][name]["nodes"].index(node_found[0])
		lb_config.g_config["app_api"]["weighers"][name]["nodes"][index_node_found]["data"] = data
		lb_config.saveconfig()
		return status, data

class WeigherInstance:
	def __init__(
		self, 
		name,
		configuration: ConfigurationDTO,
		cb_realtime: Callable[[dict], any] = None, 
	 	cb_diagnostic: Callable[[dict], any] = None, 
	  	cb_weighing: Callable[[dict], any] = None, 
	   	cb_tare_ptare_zero: Callable[[str], any] = None,
		cb_data_in_execution: Callable[[str], any] = None,
		cb_action_in_execution: Callable[[str], any] = None
		):
		self.m_enabled = True
		self.name = name
		self.nodes = []
		self.connection = ConfigConnection()
		self.time_between_actions = 0

		lb_log.info("initialize")
		# inizializzazione della conn
		connected, message = False, None
		self.connection.connection = configuration.connection
		connected, message = self.connection.connection.try_connection()
		self.time_between_actions = configuration.time_between_actions
		for node in configuration.nodes:
			n = terminalsClasses[node.terminal](
	   			self_config=self, 
		  		max_weight=node.max_weight, 
				min_weight=node.min_weight, 
			 	division=node.division, 
			  	maintaine_session_realtime_after_command=node.maintaine_session_realtime_after_command,
			   	diagnostic_has_priority_than_realtime=node.diagnostic_has_priority_than_realtime,
				node=node.node, 
				terminal=node.terminal,
				run=node.run,
				data=node.data,
				name=node.name,
				cam1=node.cam1,
				cam2=node.cam2,
				cam3=node.cam3,
				cam4=node.cam4
			)
			n.initialize()
			self.nodes.append(n)
		self.setAction(
			cb_realtime=cb_realtime, 
			cb_diagnostic=cb_diagnostic, 
			cb_weighing=cb_weighing, 
			cb_tare_ptare_zero=cb_tare_ptare_zero,
			cb_data_in_execution=cb_data_in_execution,
			cb_action_in_execution=cb_action_in_execution
		)
		self.thread = createThread(self.start)
		startThread(self.thread)
	# ==============================================================

	# ==== START ===================================================
	# funzione che fa partire il modulo
	# funzione che scrive e legge in loop conn e in base alla stringa ricevuta esegue funzioni specifiche
	def start(self):
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
								# se la globale conn è di tipo conn ed è aperta la chiude
								self.connection.connection.close()
					elif node.diagnostic.status in [305, 201]:
						node.initialize()
			if len(self.nodes) == 0:
				time.sleep(1)
	# ==============================================================

	def stop(self):
		self.m_enabled = False

	# ==== FUNZIONI RICHIAMABILI DA MODULI ESTERNI =================

	def getInstance(self):
		conn = self.connection.getConnection()
		nodes_dict = [n.getSetup() for n in self.nodes]
		return {
			"connection": conn,
			"time_between_actions": self.time_between_actions,
			"nodes": nodes_dict
		}

	def deleteInstance(self):
		self.connection.deleteConnection()
		self.deleteNodes()
		self.stop()

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

	def addNode(
		self, 
		setup: SetupWeigherDTO,
	  	cb_realtime: Callable[[dict], any] = None, 
	   	cb_diagnostic: Callable[[dict], any] = None, 
		cb_weighing: Callable[[dict], any] = None, 
		cb_tare_ptare_zero: Callable[[str], any] = None,
		cb_data_in_execution: Callable[[str], any] = None,
		cb_action_in_execution: Callable[[str], any] = None):
		n = terminalsClasses[setup.terminal](
			self_config=self, 
			max_weight=setup.max_weight, 
			min_weight=setup.min_weight, 
			division=setup.division, 
			maintaine_session_realtime_after_command=setup.maintaine_session_realtime_after_command,
			diagnostic_has_priority_than_realtime=setup.diagnostic_has_priority_than_realtime,
			node=setup.node, 
			terminal=setup.terminal,
			run=setup.run,
			data=DataDTO(**{}),
			name=setup.name,
			cam1=setup.cam1,
			cam2=setup.cam2,
			cam3=setup.cam3,
			cam4=setup.cam4
		)
		if self.connection is not None:
			n.initialize()
		self.nodes.append(n)
		node_found = [n for n in self.nodes if n.node == setup.node]
		if len(node_found) > 0:
			node_found[0].setAction(
				cb_realtime=cb_realtime,
				cb_diagnostic=cb_diagnostic,
				cb_weighing=cb_weighing,
				cb_tare_ptare_zero=cb_tare_ptare_zero,
				cb_data_in_execution=cb_data_in_execution,
				cb_action_in_execution=cb_action_in_execution
			)
		return n.getSetup()

	def setNode(
    	self, 
     	node: Union[str, None], 
      	setup: ChangeSetupWeigherDTO = {},
	  	cb_realtime: Callable[[dict], any] = None, 
	   	cb_diagnostic: Callable[[dict], any] = None, 
		cb_weighing: Callable[[dict], any] = None, 
		cb_tare_ptare_zero: Callable[[str], any] = None,
		cb_data_in_execution: Callable[[str], any] = None,
		cb_action_in_execution: Callable[[str], any] = None):
		node_found = [n for n in self.nodes if n.node == node]
		result = None
		if len(node_found) != 0:
			result = node_found[0].setSetup(setup)
			if setup.terminal:
				node_to_changed = SetupWeigherDTO(**result)
				self.deleteNode(node_to_changed.node)
				result = self.addNode(
        			node=node_to_changed,
					cb_realtime=cb_realtime,
					cb_diagnostic=cb_diagnostic,
					cb_weighing=cb_weighing,
					cb_tare_ptare_zero=cb_tare_ptare_zero,
					cb_data_in_execution=cb_data_in_execution,
					cb_action_in_execution=cb_action_in_execution
           		)
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
		e_weighers = [n for n in self.nodes]
		if len(e_weighers) > 0:
			for weigher in e_weighers:
				self.deleteDataInExecution(weigher.node, True)
				self.nodes.remove(weigher)
			response = True
		return response

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

	def getTimeBetweenActions(self):
		return self.time_between_actions

	def setTimeBetweenActions(self, time: Union[int, float]):
		self.time_between_actions = time
		return self.time_between_actions

	def getData(self, node: Union[str, None]):
		node_found = [n for n in self.nodes if n.node == node]
		if len(node_found) > 0:
			data = node_found[0].getData()
			status = node_found[0].diagnostic.status
			return status, data
		return node_found

	def setDataInExecution(self, node: Union[str, None], data_in_execution: DataInExecution, call_callback):
		node_found = [n for n in self.nodes if n.node == node]
		if len(node_found) > 0:
			data = node_found[0].setDataInExecution(data_in_execution, call_callback)
			status = node_found[0].diagnostic.status
			return status, data
		return node_found

	def deleteDataInExecution(self, node: Union[str, None], call_callback):
		node_found = [n for n in self.nodes if n.node == node]
		if len(node_found) > 0:
			data = node_found[0].deleteDataInExecution(call_callback)
			status = node_found[0].diagnostic.status
			return status, data
		return node_found

	def setIdSelected(self, node: Union[str, None], new_id: int, call_callback: bool):
		node_found = [n for n in self.nodes if n.node == node]
		if len(node_found) > 0:
			data = node_found[0].setIdSelected(new_id, call_callback)
			status = node_found[0].diagnostic.status
			return status, data
		return node_found

	def deleteData(self, node: Union[str, None], call_callback: bool):
		node_found = [n for n in self.nodes if n.node == node]
		if len(node_found) > 0:
			data = node_found[0].deleteData(call_callback=call_callback)
			status = node_found[0].diagnostic.status
			return status, data
		return node_found

	def getModope(self, node: Union[str, None]):
		node_found = [n for n in self.nodes if n.node == node]
		if len(node_found) != 0:
			return node_found[0].modope_to_execute

	def setModope(self, node: Union[str, None], modope, presettare=0, data_assigned: Union[DataInExecution, int] = None):
		node_found = [n for n in self.nodes if n.node == node]
		status, status_modope, command_execute, error_message = None, None, False, None
		if len(node_found) != 0:
			status_modope, error_message = node_found[0].setModope(mod=modope, presettare=presettare, data_assigned=data_assigned)
			status = node_found[0].diagnostic.status
			command_execute = status_modope == 100
		return status, status_modope, command_execute, error_message

	def setActionNode(
    	self, 
     	node: Union[str, None], 
      	cb_realtime: Callable[[dict], any] = None, 
       	cb_diagnostic: Callable[[dict], any] = None, 
        cb_weighing: Callable[[dict], any] = None, 
        cb_tare_ptare_zero: Callable[[str], any] = None,
		cb_data_in_execution: Callable[[str], any] = None,
		cb_action_in_execution: Callable[[str], any] = None):
		global nodes
		node_found = [n for n in self.nodes if n.node == node]
		if len(node_found) > 0:
			node_found[0].setAction(
				cb_realtime=cb_realtime,
				cb_diagnostic=cb_diagnostic,
				cb_weighing=cb_weighing,
				cb_tare_ptare_zero=cb_tare_ptare_zero,
				cb_data_in_execution=cb_data_in_execution,
				cb_action_in_execution=cb_action_in_execution
			)

	def setAction(
    	self, 
    	cb_realtime: Callable[[dict], any] = None, 
     	cb_diagnostic: Callable[[dict], any] = None, 
      	cb_weighing: Callable[[dict], any] = None, 
       	cb_tare_ptare_zero: Callable[[str], any] = None,
		cb_data_in_execution: Callable[[str], any] = None,
		cb_action_in_execution: Callable[[str], any] = None):
		for weigher in self.nodes:
			weigher.setAction(
       			cb_realtime=cb_realtime, 
          		cb_diagnostic=cb_diagnostic, 
            	cb_weighing=cb_weighing, 
             	cb_tare_ptare_zero=cb_tare_ptare_zero,
				cb_data_in_execution=cb_data_in_execution,
				cb_action_in_execution=cb_action_in_execution
    		)
	# ==============================================================