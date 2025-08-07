# ==============================================================
# = Module......: md_dgt1					   =
# = Description.: Interfaccia di pesatura con più terminali =
# = Author......: Riccardo Meggiolaro				   =
# = Last rev....: 0.0002					   =
# ==============================================================

# ==== LIBRERIE DA IMPORTARE ===================================
import libs.lb_log as lb_log
import libs.lb_config as lb_config
from typing import Callable, Union, Any
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
	while lb_config.g_enabled:
		time.sleep(1)
	lb_log.info("end")

def stop():
    pass

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
  		cb_rele: Callable[[str], any] = None,
    	cb_code_identify: Callable[[str], any] = None):
		for name, instance in self.instances.items():
			instance.setActionAllWeigher(
				cb_realtime=cb_realtime, 
				cb_diagnostic=cb_diagnostic, 
				cb_weighing=cb_weighing, 
				cb_tare_ptare_zero=cb_tare_ptare_zero,
				cb_action_in_execution=cb_action_in_execution,
				cb_rele=cb_rele,
				cb_code_identify=cb_code_identify
			)
   
	def setApplicationCallback(
		self, 
		cb_realtime: Callable[[dict], any] = None, 
		cb_diagnostic: Callable[[dict], any] = None, 
		cb_weighing: Callable[[dict], any] = None, 
		cb_tare_ptare_zero: Callable[[str], any] = None,
		cb_action_in_execution: Callable[[str], any] = None,
  		cb_rele: Callable[[str], any] = None,
    	cb_code_identify: Callable[[str], any] = None):
		for name, instance in self.instances.items():
			instance.setActionAllWeigher(
				cb_realtime=cb_realtime, 
				cb_diagnostic=cb_diagnostic, 
				cb_weighing=cb_weighing, 
				cb_tare_ptare_zero=cb_tare_ptare_zero,
				cb_action_in_execution=cb_action_in_execution,
				cb_rele=cb_rele,
				cb_code_identify=cb_code_identify
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
  		cb_rele: Callable[[str], any] = None,
    	cb_code_identify: Callable[[str], any] = None):
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
			cb_rele=cb_rele,
			cb_code_identify=cb_code_identify
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
  		cb_rele: Callable[[str], any] = None,
    	cb_code_identify: Callable[[str], any] = None):
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
			cb_rele=cb_rele,
			cb_code_identify=cb_code_identify
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

	def setModope(self, instance_name, weigher_name: str, modope, presettare=0, data_assigned: int = None, port_rele=None):
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
		cb_rele: Callable[[str], any] = None,
		cb_code_identify: Callable[[str], any] = None
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
			cb_rele=cb_rele,
			cb_code_identify=cb_code_identify
		)
		self.thread = createThread(self.start)
		startThread(self.thread)
	# ==============================================================

	# ==== START ===================================================
	# funzione che fa partire il modulo
	# funzione che scrive e legge in loop conn e in base alla stringa ricevuta esegue funzioni specifiche
	def start(self):
		consecutive_errors = {}  # Traccia errori consecutivi per nodo
		reconnection_attempts = 0
		max_reconnection_attempts = 3
		last_reconnection_time = 0
		min_reconnection_interval = 10  # Secondi minimi tra riconnessioni
		
		while self.m_enabled:
			# Se non ci sono nodi, attendi
			if len(self.nodes) == 0:
				time.sleep(1)
				continue
				
			# Flag per tracciare se serve riconnessione
			needs_reconnection = False
			all_nodes_failing = True  # Assume che tutti falliscano finché non provato il contrario
			
			for name, weigher in self.nodes.items():
				if not weigher.run:
					continue
					
				# Inizializza contatore errori per questo nodo se non esiste
				if name not in consecutive_errors:
					consecutive_errors[name] = 0
				
				time_start = time.time()
				status, command, response, error = weigher.main()
				time_end = time.time()
				time_execute = time_end - time_start
				timeout = max(0, self.time_between_actions - time_execute)
				time.sleep(timeout)
				
				lb_log.info(f"Node: {weigher.node}, Status: {status}, Command: {command}, Response: {response}, Error: {error}")
				
				# Gestione errori di comunicazione
				if weigher.diagnostic.status == 301:  # Timeout error
					consecutive_errors[name] += 1
					
					# Solo dopo N errori consecutivi tenta la riconnessione
					if consecutive_errors[name] >= 3:
						lb_log.warning(f"Node {name} has {consecutive_errors[name]} consecutive timeout errors")
						
				elif weigher.diagnostic.status == 305:  # Node not reachable
					consecutive_errors[name] += 1
					if consecutive_errors[name] >= 2:
						lb_log.warning(f"Node {name} not reachable for {consecutive_errors[name]} attempts")
						
				elif weigher.diagnostic.status == 200:  # Success
					consecutive_errors[name] = 0  # Reset error counter
					reconnection_attempts = 0  # Reset reconnection attempts
					all_nodes_failing = False  # Almeno un nodo funziona
					
				elif weigher.diagnostic.status == 201:  # Bad response format
					consecutive_errors[name] += 1
					if consecutive_errors[name] >= 5:
						lb_log.warning(f"Node {name} returning bad format for {consecutive_errors[name]} attempts")
			
			# Determina se serve riconnessione: tutti i nodi attivi devono essere in errore
			if all_nodes_failing and len(self.nodes) > 0:
				active_nodes = [name for name, w in self.nodes.items() if w.run]
				if active_nodes:
					failing_nodes = [name for name in active_nodes if consecutive_errors.get(name, 0) >= 3]
					if len(failing_nodes) == len(active_nodes):
						needs_reconnection = True
						lb_log.warning(f"All active nodes are failing: {failing_nodes}")
			
			# Controlla se è passato abbastanza tempo dall'ultima riconnessione
			current_time = time.time()
			time_since_last_reconnection = current_time - last_reconnection_time
			
			# Esegui riconnessione solo se necessario e con controllo temporale
			if needs_reconnection and time_since_last_reconnection >= min_reconnection_interval:
				if reconnection_attempts < max_reconnection_attempts:
					lb_log.info(f"Attempting reconnection {reconnection_attempts + 1}/{max_reconnection_attempts}...")
					if self._perform_reconnection():
						# Reset error counters dopo riconnessione riuscita
						for name in consecutive_errors:
							consecutive_errors[name] = 0
						reconnection_attempts = 0
					else:
						reconnection_attempts += 1
					last_reconnection_time = current_time
				else:
					lb_log.error(f"Max reconnection attempts reached. Waiting {min_reconnection_interval} seconds...")
					time.sleep(min_reconnection_interval)
					reconnection_attempts = 0
					
			# except Exception as e:
			# 	lb_log.error(f"Unexpected error in main loop: {e}")
			# 	time.sleep(1)

	def _perform_reconnection(self):
		"""Gestisce la procedura di riconnessione in modo pulito"""
		try:
			lb_log.info("Starting reconnection procedure...")
			
			# 1. Prima prova a fare un flush pulito se la connessione è ancora aperta
			try:
				if self.connection.connection.is_open():
					lb_log.info("Connection still open, flushing buffer...")
					self.connection.connection.flush()
					time.sleep(0.2)
			except:
				pass  # Se il flush fallisce, procedi comunque
			
			# 2. Chiudi la connessione esistente
			lb_log.info("Closing connection...")
			try:
				self.connection.connection.close()
			except Exception as e:
				lb_log.warning(f"Error closing connection: {e}")
			
			# 3. Pausa per permettere al dispositivo di resettarsi
			lb_log.info("Waiting for device reset...")
			time.sleep(2)
			
			# 4. Riapri la connessione
			lb_log.info("Opening new connection...")
			status, error_message = self.connection.connection.try_connection()
			
			if not status:
				lb_log.error(f"Failed to open connection: {error_message}")
				return False
				
			lb_log.info("Connection opened successfully")
			
			# 5. Pausa per stabilizzazione
			time.sleep(1)
			
			# 6. Flush iniziale per pulire eventuali dati residui
			try:
				self.connection.connection.flush()
				time.sleep(0.2)
			except:
				pass
			
			# 7. Reinizializza tutti i nodi con verifica
			lb_log.info("Reinitializing nodes...")
			successful_inits = 0
			
			for name, weigher in self.nodes.items():
				if not weigher.run:
					continue
					
				try:
					# Usa il metodo initialize esistente che già fa i controlli VER e SN
					lb_log.info(f"Initializing node {name}...")
					
					# Flush prima di ogni inizializzazione
					weigher.flush()
					time.sleep(0.1)
					
					# Inizializza
					init_result = weigher.initialize()
					
					# Verifica il risultato
					if weigher.diagnostic.status == 200:
						lb_log.info(f"Node {name} initialized successfully")
						successful_inits += 1
					else:
						lb_log.warning(f"Node {name} initialization failed with status {weigher.diagnostic.status}")
						
					# Pausa tra inizializzazioni
					time.sleep(self.time_between_actions)
						
				except Exception as e:
					lb_log.error(f"Error initializing node {name}: {e}")
			
			# Verifica se almeno un nodo è stato inizializzato con successo
			if successful_inits > 0:
				lb_log.info(f"Reconnection successful: {successful_inits} nodes initialized")
				return True
			else:
				lb_log.error("Reconnection failed: no nodes initialized successfully")
				return False
				
		except Exception as e:
			lb_log.error(f"Critical error during reconnection: {e}")
			return False
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
		cb_rele: Callable[[str], any] = None,
  		cb_code_identify: Callable[[str], any] = None):
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
			cb_rele=cb_rele,
			cb_code_identify=cb_code_identify
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
  		cb_rele: Callable[[str], any] = None,
    	cb_code_identify: Callable[[str], any] = None):
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
				cb_rele=cb_rele,
    			cb_code_identify=cb_code_identify)
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
		cb_rele: Callable[[str], any] = None,
		cb_code_identify: Callable[[str], any] = None
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
					cb_rele=cb_rele,
					cb_code_identify=cb_code_identify
				)

	def setActionAllWeigher(
    	self, 
    	cb_realtime: Callable[[dict], any] = None, 
     	cb_diagnostic: Callable[[dict], any] = None, 
      	cb_weighing: Callable[[dict], any] = None, 
       	cb_tare_ptare_zero: Callable[[str], any] = None,
		cb_action_in_execution: Callable[[str], any] = None,
  		cb_rele: Callable[[str], any] = None,
    	cb_code_identify: Callable[[str], any] = None):
		for name, weigher in self.nodes.items():
			weigher.setAction(
				weigher_name=name,
       			cb_realtime=cb_realtime, 
          		cb_diagnostic=cb_diagnostic, 
            	cb_weighing=cb_weighing, 
             	cb_tare_ptare_zero=cb_tare_ptare_zero,
				cb_action_in_execution=cb_action_in_execution,
                cb_rele=cb_rele,
                cb_code_identify=cb_code_identify
    		)
   
	def canStartWeighing(self, weigher_name: str):
		return self.nodes[weigher_name].canStartWeighing()
	# ==============================================================