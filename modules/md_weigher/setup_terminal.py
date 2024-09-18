from modules.md_weigher.types import Realtime, Diagnostic, Weight, DataInExecution
from modules.md_weigher.dto import SetupWeigherDTO
from modules.md_weigher.globals import connection
from lib.lb_system import Connection
import lib.lb_log as lb_log
from lib.lb_utils import checkCallbackFormat
from pydantic import BaseModel
from typing import Optional, Callable, Union
import select

class __SetupWeigherConnection(BaseModel):
	max_weight: int
	min_weight: int
	division: int
	maintaine_session_realtime_after_command: bool = True
	diagnostic_has_priority_than_realtime: bool = True
	node: Optional[str] = None
	terminal: str
	run: bool = True

	def try_connection(self):
		return connection.connection.try_connection()
	
	def write(self, cmd):
		if self.node and self.node is not None:
			cmd = self.node + cmd
		status = connection.connection.write(cmd=cmd)
		if not status:
			if not self.is_open():
				raise TimeoutError()
			else:
				raise BrokenPipeError()

	def read(self):
		read = connection.connection.read()
		if read:
			decode = read.decode("utf-8", errors="ignore").replace(self.node, "", 1).replace("\r\n", "")
			read = decode
		else:
			connected = self.is_open()
			if not connected:
				raise TimeoutError()
			else:
				raise BrokenPipeError()
		return read

	def flush(self):
		connection.connection.flush()

	def is_open(self):
		return connection.connection.is_open()

	def close_connection(self):
		connection.connection.close()
		connection.connection = Connection(**{})

class __SetupWeigher(__SetupWeigherConnection):
	pesa_real_time: Realtime = Realtime(**{
		"status": "",
		"type": "",
		"net_weight": "", 
		"gross_weight": "", 
		"tare": "",
		"unite_measure": ""
	})
	diagnostic: Diagnostic = Diagnostic(**{
		"status": 301,
		"firmware": "",
		"model_name": "",
		"serial_number": "",
		"vl": "",
		"rz": ""
	})
	weight: Weight = Weight(**{
		"weight_executed": {
			"net_weight": "",
			"gross_weight": "",
			"tare": "",
			"unite_misure": "",
			"pid": "",
			"bil": "",
			"status": ""
		},
		"data_assigned": None
	})
	ok_value: str = ""
	modope: str = ""
	modope_to_execute: str = ""
	valore_alterno: int = 1
	preset_tare: int = 0
	just_send_message_failed_reconnection: bool = False
	callback_realtime: str = ""
	callback_diagnostics: str = ""
	callback_weighing: str = ""
	callback_tare_ptare_zero: str = ""
	data_in_execution: DataInExecution = DataInExecution(**{
		"customer": None,
		"supplier": None,
		"plate": None,
		"vehicle": None,
		"material": None
	})

	def getSetup(self):
		return {
			"node": self.node,
			"max_weight": self.max_weight,
			"min_weight": self.min_weight,
			"division": self.division,
			"maintaine_session_realtime_after_command": self.maintaine_session_realtime_after_command,
			"diagnostic_has_priority_than_realtime": self.diagnostic_has_priority_than_realtime,
			"terminal": self.terminal,
			"run": self.run,
   			"status": self.diagnostic.status
		}

	def setSetup(self, setup: SetupWeigherDTO):
		if setup.max_weight is not None:
			self.max_weight = setup.max_weight
		if setup.min_weight is not None:
			self.min_weight = setup.min_weight
		if setup.division is not None:
			self.division = setup.division
		if setup.maintaine_session_realtime_after_command is not None:
			self.maintaine_session_realtime_after_command = setup.maintaine_session_realtime_after_command
		if setup.diagnostic_has_priority_than_realtime is not None:
			self.diagnostic_has_priority_than_realtime = setup.diagnostic_has_priority_than_realtime
		if setup.node != "undefined":
			self.node = setup.node
		if setup.run is not None:
			self.run = setup.run
		return self.getSetup()

	def getDataInExecution(self):
		return self.data_in_execution.dict()

	def setDataInExecution(self, data: DataInExecution):
		for key, value in data:
			if value is None:
				continue
			elif value == "undefined":
				self.data_in_execution.setAttribute(key=key, value=None)
			else:
				self.data_in_execution.setAttribute(key, value)
		return self.getDataInExecution()

	def deleteDataInExecution(self):
		self.data_in_execution = DataInExecution(**{
			"customer": None,
			"supplier": None,
			"plate": None,
			"vehicle": None,
			"material": None
		})
		return self.getDataInExecution()

	def maintaineSessionRealtime(self):
		if self.maintaine_session_realtime_after_command:
			self.modope_to_execute = "REALTIME"

	def setAction(self,
		cb_realtime: Callable[[dict], any] = None, 
		cb_diagnostic: Callable[[dict], any] = None, 
		cb_weighing: Callable[[dict], any] = None, 
		cb_tare_ptare_zero: Callable[[str], any] = None):
		check_cb_realtime = checkCallbackFormat(cb_realtime) # controllo se la funzione cb_realtime è richiamabile
		if check_cb_realtime: # se è richiamabile assegna alla globale callback_realtime la funzione passata come parametro
			self.callback_realtime = lambda: cb_realtime(self.pesa_real_time) 
		check_cb_diagnostic = checkCallbackFormat(cb_diagnostic) # controllo se la funzione cb_diagnostic è richiamabile
		if check_cb_diagnostic: # se è richiamabile assegna alla globale callback_diagnostics la funzione passata come parametro
			self.callback_diagnostics = lambda: cb_diagnostic(self.diagnostic)
		check_cb_weighing = checkCallbackFormat(cb_weighing) # controllo se la funzione cb_weighing è richiamabile
		if check_cb_weighing: # se è richiamabile assegna alla globale callback_weighing la funzione passata come parametro
			self.callback_weighing = lambda: cb_weighing(self.weight)
		check_cb_tare_ptare_zero = checkCallbackFormat(cb_tare_ptare_zero) # controllo se la funzione cb_tare_ptare_zero è richiamabile
		if check_cb_tare_ptare_zero: # se è richiamabile assegna alla globale callback_tare_ptare_zero la funzione passata come parametro
			self.callback_tare_ptare_zero = lambda: cb_tare_ptare_zero(self.ok_value)

	# setta il modope_to_execute
	def setModope(self, mod: str, presettare: int = 0, data_assigned: Union[DataInExecution, int] = None):
		commands = ["VER", "SN", "OK"]
		direct_commands = ["TARE", "ZERO", "RESETTARE", "PRESETTARE", "WEIGHING"]
		if mod in commands:
			self.modope_to_execute = mod
			return 100, None
		if self.diagnostic.status in [301, 305] and mod != "REALTIME" and mod != "DIAGNOSTICS" and mod != "OK":
			error_message = "Connection not set"
			if self.diagnostic.status == 305:
				error_message = "Node not exist"
			return 500, error_message
		# se passo una stringa vuota imposta a stringa vuota il comando da eseguire dopo, quindi non verranno più eseguiti comandi diretti sulla pesa
		# se passo DIAGNOSTICS lo imposto come comando da eseguire, se c'era qualsiasi altro comando viene sovrascritto perchè la diagnostica ha la precedenza
		if mod == "DIAGNOSTICS":
			self.modope_to_execute = mod # imposto la diagnostica
			return 100, None # ritorno il successo
		# se passo REALTIME
		if mod == "REALTIME":
			# se il comando in esecuzione o il comando che dovrà essere eseguito è la diagnostica ed ha la priorità ritorno errore
			if self.modope_to_execute == "DIAGNOSTICS" and self.diagnostic_has_priority_than_realtime:
				return 400, "Diagnostic in executing"
			self.modope_to_execute = mod # se non si è verificata nessuna delle condizioni imposto REALTIME come comando da eseguire
			return 100, None # ritorno il successo
		# se il mod passato è un comando diretto verso la pesa ("TARE", "ZERO", "RESETTARE", "PRESETTARE", "WEIGHING")
		elif mod in direct_commands:
			# controllo se il comando attualmente in esecuzione in loop è DIAGNOSTICS e se si ritorno errore
			if self.modope == "DIAGNOSTICS":
				return 400, "Diagnostic in executing"
			# controllo se c'è qualche comando diretto verso la pesa attualmente in esecuzione e se si ritorno errore
			elif self.modope in commands or self.modope in direct_commands:
				return 405, f"{self.modope} in executing"
			# controllo che il comando attualmente in esecuzione in loop sia REALTIME
			elif self.modope == "REALTIME":
				# controllo che anche il comando da eseguire sia impostato a REALTIME per assicurarmi che non sia cambiato
				if self.modope_to_execute == "REALTIME":
					# se passo PRESETTARE
					if mod == "PRESETTARE" and mod:
						# controllo che la presettare passata sia un numero e maggiore o uguale di 0
						if str(presettare).isdigit() and int(presettare) >= 0:
							self.preset_tare = presettare # imposto la presettare
						else:
							return 500, "Tare need to be bigger or equal than 0" # ritorno errore se la presettare non era valida
					# se passo WEIGHING
					elif mod == "WEIGHING":
						# controllo che il peso sia maggiore o uguale al peso minimo richiesto
						if self.pesa_real_time.gross_weight != "" and self.pesa_real_time.status == "ST" and int(self.pesa_real_time.gross_weight) >= self.min_weight and int(self.pesa_real_time.gross_weight) <= self.max_weight:
							self.weight.data_assigned = data_assigned
						else:
							return 500, f"Weight need to be bigger or equal than {self.min_weight}" # ritorno errore se il peso non era valido
					self.modope_to_execute = mod # se tutte le condizioni sono andate a buon fine imposto il mod passato come comando da eseguire
					return 100, None # ritorno il successo
				elif self.modope_to_execute == "DIAGNOSTICS":
					return 400, "Diagnostic in executing"
				elif self.modope_to_execute in commands or self.modope_to_execute in direct_commands:
					return 405, f"{self.modope} in executing"
		# se il comando passato non è valido ritorno errore
		else:
			return 404, "Modope not exist"

class Terminal(__SetupWeigher):
	########################
	# functions to overwrite
	########################
 
	def command(self):
		pass

	def initialize(self):
		pass

	def main(self):
		pass

	########################