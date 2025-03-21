# ==============================================================
# = Module......: md_dgt1					   =
# = Description.: Interfaccia di pesatura con più terminali =
# = Author......: Riccardo Meggiolaro				   =
# = Last rev....: 0.0002					   =
# ==============================================================

# ==== LIBRERIE DA IMPORTARE ===================================
import libs.lb_log as lb_log
import libs.lb_config as lb_config
from typing import Callable, Union, Optional, Any
import time
from libs.lb_system import SerialPort, Tcp
from modules.md_weigher.globals import terminalsClasses
from libs.lb_system import ConfigConnection
from modules.md_weigher.terminals.dgt1 import Dgt1
from modules.md_weigher.terminals.egtaf03 import EgtAf03
from libs.lb_utils import createThread, startThread
from modules.md_weigher.types import Configuration, ConfigurationWithoutControls
from fastapi import HTTPException
from modules.md_weigher.dto import ConfigurationDTO, SetupWeigherDTO, ChangeSetupWeigherDTO
# ==============================================================

name_module = "md_weigher"

terminalsClasses["dgt1"] = Dgt1
terminalsClasses["egt-af03"] = EgtAf03

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

	def initializeModuleConfig(self, config):
		for name, configuration in config.items():
			weigher_configuration = ConfigurationWithoutControls(**configuration)
			instance = WeigherInstance(name, weigher_configuration)
			self.instances[name] = instance
   		
	def setApplicationCallback(
		self, 
		cb_realtime: Callable[[dict], any] = None, 
		cb_diagnostic: Callable[[dict], any] = None, 
		cb_weighing: Callable[[dict], any] = None, 
		cb_tare_ptare_zero: Callable[[str], any] = None,
		cb_action_in_execution: Callable[[str], any] = None,
  		cb_rele: Callable[[str], any] = None):
		for name, instance in self.instances.items():
			instance.setActionAllWeigher(
				cb_realtime=cb_realtime, 
				cb_diagnostic=cb_diagnostic, 
				cb_weighing=cb_weighing, 
				cb_tare_ptare_zero=cb_tare_ptare_zero,
				cb_action_in_execution=cb_action_in_execution,
				cb_rele=cb_rele
			)
   
	def setApplicationCallback(
		self, 
		cb_realtime: Callable[[dict], any] = None, 
		cb_diagnostic: Callable[[dict], any] = None, 
		cb_weighing: Callable[[dict], any] = None, 
		cb_tare_ptare_zero: Callable[[str], any] = None,
		cb_action_in_execution: Callable[[str], any] = None,
  		cb_rele: Callable[[str], any] = None):
		for name, instance in self.instances.items():
			instance.setActionAllWeigher(
				cb_realtime=cb_realtime, 
				cb_diagnostic=cb_diagnostic, 
				cb_weighing=cb_weighing, 
				cb_tare_ptare_zero=cb_tare_ptare_zero,
				cb_action_in_execution=cb_action_in_execution,
				cb_rele=cb_rele
			)

	def getAllInstance(self):
		instances = {}
		for name, instance in self.instances.items():
			instances[name] = instance.getInstance()
		return instances

	def getInstance(self, instance_name):
		instance = self.instances[instance_name].getInstance()
		return {
			instance_name: instance
       	}

	def createInstance(self, configuration: ConfigurationDTO):
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
		return {
			configuration.name: instance_created
		}

	def deleteInstance(self, instance_name):
		deleted = self.instances[instance_name].deleteInstance()
		self.instances.pop(instance_name)
		return deleted

	def getAllInstanceWeigher(self, instance_name):
		return self.instances[instance_name].getNodes()

	def getInstanceWeigher(self, instance_name, weigher_name):
		instance = self.instances[instance_name].getNode(weigher_name)
		if instance:
			return {
				instance_name: instance
			}
		else:
			return None

	def addInstanceWeigher(
    	self, 
     	instance_name, 
      	setup: SetupWeigherDTO,
	  	cb_realtime: Callable[[dict], any] = None, 
	   	cb_diagnostic: Callable[[dict], any] = None, 
		cb_weighing: Callable[[dict], any] = None, 
		cb_tare_ptare_zero: Callable[[str], any] = None,
		cb_action_in_execution: Callable[[str], any] = None,
  		cb_rele: Callable[[str], any] = None):
		details = []
		if setup.name in self.getAllInstanceWeigher(instance_name=instance_name):
			details.append({"type": "value_error", "loc": ["", "name"], "msg": "Nome già esistente", "input": setup.name, "ctx": {"error":{}}})
		if any(setup.node == weigher["node"] for name, weigher in self.getAllInstanceWeigher(instance_name=instance_name).items()):
			details.append({"type": "value_error", "loc": ["", "node"], "msg": "Nodo già esistente", "input": setup.node, "ctx": {"error":{}}})
		if details:
			raise HTTPException(status_code=400, detail=details)
		weigher_created = self.instances[instance_name].addNode(
			setup=setup,
			cb_realtime=cb_realtime,
			cb_diagnostic=cb_diagnostic,
			cb_weighing=cb_weighing,
			cb_tare_ptare_zero=cb_tare_ptare_zero,
			cb_action_in_execution=cb_action_in_execution,
			cb_rele=cb_rele
		)
		return {
			setup.name: weigher_created
		}

	def setInstanceWeigher(
		self,
  		instance_name,
    	weigher_name,
     	setup: ChangeSetupWeigherDTO,
	  	cb_realtime: Callable[[dict], any] = None, 
	   	cb_diagnostic: Callable[[dict], any] = None, 
		cb_weighing: Callable[[dict], any] = None, 
		cb_tare_ptare_zero: Callable[[str], any] = None,
		cb_action_in_execution: Callable[[str], any] = None,
  		cb_rele: Callable[[str], any] = None):
		details = []
		if any(setup.name == name for name in self.getAllInstanceWeigher(instance_name=instance_name)):
			details.append({"type": "value_error", "loc": ["", "name"], "msg": "Nome già esistente", "input": setup.name, "ctx": {"error":{}}})
		if any(setup.node == weigher["node"] for name, weigher in self.getAllInstanceWeigher(instance_name=instance_name).items()):
			details.append({"type": "value_error", "loc": ["", "node"], "msg": "Nodo già esistente", "input": setup.node, "ctx": {"error":{}}})
		if details:
			raise HTTPException(status_code=400, detail=details)
		weigher_set = self.instances[instance_name].setNode(
			name=weigher_name,
        	setup=setup,
			cb_realtime=cb_realtime,
			cb_diagnostic=cb_diagnostic,
			cb_weighing=cb_weighing,
			cb_tare_ptare_zero=cb_tare_ptare_zero,
			cb_action_in_execution=cb_action_in_execution,
			cb_rele=cb_rele
		)
		return {
			weigher_name: weigher_set
		}

	def deleteInstanceWeigher(self, instance_name, weigher_name):
		return self.instances[instance_name].deleteNode(weigher_name)

	def getInstanceConnection(self, instance_name):
		return self.instances[instance_name].getConnection()

	def setInstanceConnection(self, instance_name, conn: Union[SerialPort, Tcp]):
		return self.instances[instance_name].setConnection(conn=conn)

	def deleteInstanceConnection(self, instance_name):
		return self.instances[instance_name].deleteConnection()

	def setInstanceTimeBetweenActions(self, instance_name, time_between_actions):
		return self.instances[instance_name].setTimeBetweenActions(time=time_between_actions)

	def getRealtime(self, instance_name, weigher_name: str):
		return self.instances[instance_name].getRealtime(weigher_name=weigher_name)

	def getModope(self, instance_name, weigher_name: str):
		return self.instances[instance_name].getModope(weigher_name=weigher_name)

	def setModope(self, instance_name, weigher_name: str, modope, presettare=0, data_assigned: Any = None, port_rele=None):
		return self.instances[instance_name].setModope(weigher_name=weigher_name, modope=modope, presettare=presettare, data_assigned=data_assigned, port_rele=port_rele)

	def canStartWeighing(self, instance_name, weigher_name: str):
		return self.instances[instance_name].canStartWeighing(weigher_name=weigher_name)

class WeigherInstance:
	def __init__(
		self, 
		name,
		configuration: ConfigurationDTO,
		cb_realtime: Callable[[dict], any] = None, 
	 	cb_diagnostic: Callable[[dict], any] = None, 
	  	cb_weighing: Callable[[dict], any] = None, 
	   	cb_tare_ptare_zero: Callable[[str], any] = None,
		cb_action_in_execution: Callable[[str], any] = None,
		cb_rele: Callable[[str], any] = None
		):
		self.m_enabled = True
		self.name = name
		self.nodes = {}
		self.connection = ConfigConnection()
		self.time_between_actions = 0

		lb_log.info("initialize")
		# inizializzazione della conn
		connected, message = False, None
		self.connection.connection = configuration.connection
		connected, message = self.connection.connection.try_connection()
		self.time_between_actions = configuration.time_between_actions
		for key, value in configuration.nodes.items():
			n = terminalsClasses[value.terminal](
	   			self_config=self, 
		  		max_weight=value.max_weight,
				min_weight=value.min_weight, 
			 	division=value.division, 
			  	maintaine_session_realtime_after_command=value.maintaine_session_realtime_after_command,
			   	diagnostic_has_priority_than_realtime=value.diagnostic_has_priority_than_realtime,
				always_execute_realtime_in_undeground=value.always_execute_realtime_in_undeground,
				need_take_of_weight_before_weighing=value.need_take_of_weight_before_weighing,
				need_take_of_weight_on_startup=value.need_take_of_weight_on_startup,
				node=value.node, 
				terminal=value.terminal,
				run=value.run
			)
			n.initialize()
			self.nodes[key] = n			
		self.setActionAllWeigher(
			cb_realtime=cb_realtime, 
			cb_diagnostic=cb_diagnostic, 
			cb_weighing=cb_weighing, 
			cb_tare_ptare_zero=cb_tare_ptare_zero,
			cb_action_in_execution=cb_action_in_execution,
			cb_rele=cb_rele
		)
		self.thread = createThread(self.start)
		startThread(self.thread)
	# ==============================================================

	# ==== START ===================================================
	# funzione che fa partire il modulo
	# funzione che scrive e legge in loop conn e in base alla stringa ricevuta esegue funzioni specifiche
	def start(self):
		while self.m_enabled:
			for name, weigher in self.nodes.items():
				if weigher.run:
					time_start = time.time()
					status, command, response, error = weigher.main()
					time_end = time.time()
					time_execute = time_end - time_start
					timeout = max(0, self.time_between_actions - time_execute)
					time.sleep(timeout)
					lb_log.info(f"Node: {weigher.node}, Status: {status}, Command: {command}, Response; {response}, Error: {error}")
					if weigher.diagnostic.status == 301:
						self.connection.connection.close()
						status, error_message = self.connection.connection.try_connection()
						for n, w in self.nodes.items():
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
					elif weigher.diagnostic.status in [305, 201]:
						weigher.initialize()
			if len(self.nodes) == 0:
				time.sleep(1)
	# ==============================================================

	def stop(self):
		self.m_enabled = False

	# ==== FUNZIONI RICHIAMABILI DA MODULI ESTERNI =================

	def getInstance(self):
		conn = self.connection.getConnection()
		nodes = {name: weigher.getSetup() for name, weigher in self.nodes.items()}
		return {
			"connection": conn,
			"time_between_actions": self.time_between_actions,
			"nodes": nodes
		}

	def deleteInstance(self):
		self.connection.deleteConnection()
		self.deleteNodes()
		self.stop()
		return True

	def getNodes(self):
		nodes_dict = {}
		for name, weigher in self.nodes.items():
			nodes_dict[name] = weigher.getSetup()
		return nodes_dict

	def getNode(self, name: str):
		return self.nodes[name].getSetup()

	def addNode(
		self, 
		setup: SetupWeigherDTO,
	  	cb_realtime: Callable[[dict], any] = None, 
	   	cb_diagnostic: Callable[[dict], any] = None, 
		cb_weighing: Callable[[dict], any] = None, 
		cb_tare_ptare_zero: Callable[[str], any] = None,
		cb_action_in_execution: Callable[[str], any] = None,
		cb_rele: Callable[[str], any] = None):
		n = terminalsClasses[setup.terminal](
			self_config=self, 
			max_weight=setup.max_weight, 
			min_weight=setup.min_weight, 
			division=setup.division, 
			maintaine_session_realtime_after_command=setup.maintaine_session_realtime_after_command,
			diagnostic_has_priority_than_realtime=setup.diagnostic_has_priority_than_realtime,
			always_execute_realtime_in_undeground=setup.always_execute_realtime_in_undeground,
   			need_take_of_weight_before_weighing=setup.need_take_of_weight_before_weighing,
			need_take_of_weight_on_startup=setup.need_take_of_weight_on_startup,
			node=setup.node, 
			terminal=setup.terminal,
			run=setup.run
		)
		# per non far partire l'errore di modifica durante l'iterazione
		nodes_copy = self.nodes.copy()
		nodes_copy.update({setup.name: n})
		self.nodes = nodes_copy
		self.setActionWeigher(
      		setup.name,
			cb_realtime=cb_realtime,
			cb_diagnostic=cb_diagnostic,
			cb_weighing=cb_weighing,
			cb_tare_ptare_zero=cb_tare_ptare_zero,
			cb_action_in_execution=cb_action_in_execution,
			cb_rele=cb_rele
        )
		return self.nodes[setup.name].getSetup()

	def setNode(
    	self, 
     	name: str,
      	setup: ChangeSetupWeigherDTO = {},
	  	cb_realtime: Callable[[dict], any] = None, 
	   	cb_diagnostic: Callable[[dict], any] = None, 
		cb_weighing: Callable[[dict], any] = None, 
		cb_tare_ptare_zero: Callable[[str], any] = None,
		cb_action_in_execution: Callable[[str], any] = None,
  		cb_rele: Callable[[str], any] = None):
		result = self.nodes[name].setSetup(setup)
		if setup.name != "undefined" or setup.terminal:
			result["name"] = setup.name if setup.name != "undefined" else name
			result["terminal"] = setup.terminal if setup.terminal else result["terminal"]
			weigher_to_change = SetupWeigherDTO(**result)
			self.deleteNode(name=name)
			result = self.addNode(
				setup=weigher_to_change,
				cb_realtime=cb_realtime,
				cb_diagnostic=cb_diagnostic,
				cb_weighing=cb_weighing,
				cb_tare_ptare_zero=cb_tare_ptare_zero,
				cb_action_in_execution=cb_action_in_execution,
				cb_rele=cb_rele)
		return result

	def deleteNode(self, name: str):
		response = False
		if name in self.nodes:
			nodes_copy = self.nodes.copy()
			del nodes_copy[name]
			self.nodes = nodes_copy
			response = True
		return response

	def deleteNodes(self):
		response = False
		self.nodes = {}
		return response

	def getConnection(self):
		return self.connection.getConnection()

	def setConnection(self, conn: Union[SerialPort, Tcp]):
		self.deleteConnection()
		conn = self.connection.setConnection(connection=conn)
		for name, weigher in self.nodes.items():
			weigher.initialize()
		return conn

	def deleteConnection(self):
		return self.connection.deleteConnection()

	def getTimeBetweenActions(self):
		return self.time_between_actions

	def setTimeBetweenActions(self, time: Union[int, float]):
		self.time_between_actions = time
		return self.time_between_actions

	def getRealtime(self, weigher_name: str):
		return self.nodes[weigher_name].pesa_real_time

	def getModope(self, weigher_name: str):
		return self.nodes[weigher_name].modope_to_execute

	def setModope(self, weigher_name: str, modope, presettare=0, data_assigned: Any = None, port_rele=None):
		status_modope, error_message = self.nodes[weigher_name].setModope(mod=modope, presettare=presettare, data_assigned=data_assigned, port_rele=port_rele)
		command_executed = status_modope == 100
		return status_modope, command_executed, error_message

	def setActionWeigher(
    	self, 
     	weigher_name: str, 
      	cb_realtime: Callable[[dict], any] = None, 
       	cb_diagnostic: Callable[[dict], any] = None, 
        cb_weighing: Callable[[dict], any] = None, 
        cb_tare_ptare_zero: Callable[[str], any] = None,
		cb_action_in_execution: Callable[[str], any] = None,
		cb_rele: Callable[[str], any] = None
    	):
		for name, weigher in self.nodes.items():
			if name == weigher_name:
				weigher.setAction(
					weigher_name=name,
					cb_realtime=cb_realtime,
					cb_diagnostic=cb_diagnostic,
					cb_weighing=cb_weighing,
					cb_tare_ptare_zero=cb_tare_ptare_zero,
					cb_action_in_execution=cb_action_in_execution,
					cb_rele=cb_rele
				)

	def setActionAllWeigher(
    	self, 
    	cb_realtime: Callable[[dict], any] = None, 
     	cb_diagnostic: Callable[[dict], any] = None, 
      	cb_weighing: Callable[[dict], any] = None, 
       	cb_tare_ptare_zero: Callable[[str], any] = None,
		cb_action_in_execution: Callable[[str], any] = None,
  		cb_rele: Callable[[str], any] = None):
		for name, weigher in self.nodes.items():
			weigher.setAction(
				weigher_name=name,
       			cb_realtime=cb_realtime, 
          		cb_diagnostic=cb_diagnostic, 
            	cb_weighing=cb_weighing, 
             	cb_tare_ptare_zero=cb_tare_ptare_zero,
				cb_action_in_execution=cb_action_in_execution,
                cb_rele=cb_rele
    		)
   
	def canStartWeighing(self, weigher_name: str):
		return self.nodes[weigher_name].canStartWeighing()
	# ==============================================================