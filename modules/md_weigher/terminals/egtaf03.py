import libs.lb_log as lb_log
from libs.lb_utils import callCallback
import re
from modules.md_weigher.setup_terminal import Terminal
from libs.lb_utils import sum_number

class EgtAf03(Terminal):
	def __init__(self, self_config, max_weight, min_weight, division, maintaine_session_realtime_after_command, diagnostic_has_priority_than_realtime, always_execute_realtime_in_undeground, need_take_of_weight_before_weighing, need_take_of_weight_on_startup, node, terminal, run):
		# Chiama il costruttore della classe base
		super().__init__(self_config, max_weight, min_weight, division, maintaine_session_realtime_after_command, diagnostic_has_priority_than_realtime, always_execute_realtime_in_undeground, need_take_of_weight_before_weighing, need_take_of_weight_on_startup, node, terminal, run)
    
	def command(self):
		self.modope = self.modope_to_execute # modope assume il valore di modope_to_execute, che nel frattempo può aver cambiato valore tramite le funzioni richiambili dall'esterno
		# in base al valore del modope scrive un comando specifico nella conn
		if self.modope == "DIAGNOSTIC":
			if self.valore_alterno == 1: # se valore alterno uguale a 1 manda MVOL per ottnere determinati dati riguardanti la diagnostica
				self.write("MVOL")
			elif self.valore_alterno == 2: # altrimenti se valore alterno uguale a 2 manda RAZF per ottnere altri determinati dati riguardanti la diagnostica
				self.write("RAZF")		
				self.valore_alterno = 0 # imposto valore uguale a 0
			self.valore_alterno = self.valore_alterno + 1 # incremento di 1 il valore alterno
		elif self.modope == "REALTIME":
			self.write("REXT")
		elif self.modope == "OK":
			self.write("DINT2710")
		elif self.modope == "WEIGHING":
			self.write("PID")
			self.modope_to_execute = "OK" # setto modope_to_execute a stringa vuota per evitare che la stessa funzione venga eseguita anche nel prossimo ciclo
			self.maintaineSessionRealtime() # eseguo la funzione che si occupa di mantenere la sessione del peso in tempo reale in base a come la ho settata
		elif self.modope == "TARE":
			self.write("TARE")
			self.modope_to_execute = "OK" # setto modope_to_execute a stringa vuota per evitare che la stessa funzione venga eseguita anche nel prossimo ciclo
			self.maintaineSessionRealtime() # eseguo la funzione che si occupa di mantenere la sessione del peso in tempo reale in base a come la ho settata
		elif self.modope == "PRESETTARE":
			self.write("TMAN" + str(self.preset_tare))
			self.preset_tare = 0
			self.modope_to_execute = "OK" # setto modope_to_execute a stringa vuota per evitare che la stessa funzione venga eseguita anche nel prossimo ciclo
			self.maintaineSessionRealtime() # eseguo la funzione che si occupa di mantenere la sessione del peso in tempo reale in base a come la ho settata
		elif self.modope == "ZERO":
			self.write("ZERO")
			self.modope_to_execute = "OK" # setto modope_to_execute a stringa vuota per evitare che la stessa funzione venga eseguita anche nel prossimo ciclo
			self.maintaineSessionRealtime() # eseguo la funzione che si occupa di mantenere la sessione del peso in tempo reale in base a come la ho settata
		elif self.modope == "OPENRELE":
			key, value = self.port_rele
			self.write("OUTP" + str(key) + "0001")
			self.modope_to_execute = "OK"
			self.maintaineSessionRealtime()
		elif self.modope == "CLOSERELE":
			key, value = self.port_rele
			self.write("OUTP" + str(key) + "0000")
			self.modope_to_execute = "OK"
			self.maintaineSessionRealtime()
		elif self.modope == "VER":
			self.write("VER")
		elif self.modope == "SN":
			self.write("SN")
		return self.modope

	def initialize_content(self):
		try:
			self.setModope("VER")
			self.command()
			response = self.read()
			if response: # se legge la risposta e la lunghezza della stringa è di 12 la splitta per ogni virgola
				# lb_log.info(response)
				values = response.split(",")
				# se il numero di sottostringhe è 3 assegna i valori all'oggetto diagnostic
				if len(values) == 3:
					self.diagnostic.firmware = values[1].lstrip()
					self.diagnostic.model_name = values[2].rstrip()
				# se il numero di sottostringhe non è 3 manda errore
				else:
					raise ValueError("Firmware and model name not found")
			# ottenere numero conn
			self.setModope("SN")
			self.command()
			response = self.read()
			if response: # se legge la risposta e la lunghezza della stringa è di 12 la splitta per ogni virgola
				value = response.replace("SN: ", "")
				self.diagnostic.serial_number = value
			# controllo se ho ottenuto firmware, nome modello e numero conn
			if self.diagnostic.firmware and self.diagnostic.model_name and self.diagnostic.serial_number:
				self.diagnostic.status = 200 # imposto status della pesa a 200 per indicare che è accesa
				if self.modope not in ["REALTIME", "DIAGNOSTIC"]:
					self.setModope("OK") if self.always_execute_realtime_in_undeground is False else self.setModope("REALTIME")
				lb_log.info("------------------------------------------------------")
				lb_log.info("INITIALIZATION")
				lb_log.info("INFOSTART: " + "Accensione con successo")
				lb_log.info("NODE: " + str(self.node))
				lb_log.info("FIRMWARE: " + self.diagnostic.firmware) 
				lb_log.info("MODELNAME: " + self.diagnostic.model_name)
				lb_log.info("SERIALNUMBER: " + self.diagnostic.serial_number)
				lb_log.info("------------------------------------------------------")
		except TimeoutError as e:
			self.diagnostic.status = 301
			self.diagnostic.firmware = None
			self.diagnostic.model_name = None
			self.diagnostic.serial_number = None
		except BrokenPipeError as e:
			self.diagnostic.status = 305
			self.diagnostic.firmware = None
			self.diagnostic.model_name = None
			self.diagnostic.serial_number = None
		except ValueError as e:
			self.diagnostic.status = 201
			self.diagnostic.firmware = None
			self.diagnostic.model_name = None
			self.diagnostic.serial_number = None

	def initialize(self):
		self.initialize_content()
		return {
			"max_weight": self.max_weight,
			"min_weight": self.min_weight,
			"division": self.division,
			"maintaine_session_realtime_after_command": self.maintaine_session_realtime_after_command,
			"diagnostic_has_priority_than_realtime": self.diagnostic_has_priority_than_realtime,
			"node": self.node
		}

	def main(self):
		response, error = None, None
		try:
			if self.diagnostic.status in [200, 201]:
				self.command() # eseguo la funzione command() che si occupa di scrivere il comando sulla pesa in base al valore del modope_to_execute nel momento in cui ho chiamato la funzione
				response = self.read()
				split_response = response.split(",") # creo un array di sotto stringhe splittando la risposta per ogni virgola
				length_split_response = len(split_response) # ottengo la lunghezza dell'array delle sotto stringhe
				length_response = len(response) # ottengo la lunghezza della stringa della risposta
				######### Se in esecuzione peso in tempo reale ######################################################################
				if self.modope == "REALTIME":
					# Controlla formato stringa del peso in tempo reale, se corretta aggiorna oggetto e chiama callback
					if length_split_response == 7 and length_response == 53:
						nw = split_response[2].lstrip()
						tare_without_pt = re.sub('[PT]', '', split_response[3]).lstrip()
						gw = str(sum_number(nw, tare_without_pt))
						t = split_response[3].lstrip()
						self.pesa_real_time.status = split_response[1]
						self.pesa_real_time.type = "GS" if t == "0" else "NT"
						self.pesa_real_time.net_weight = nw
						self.pesa_real_time.gross_weight = gw
						self.pesa_real_time.tare = t
						self.pesa_real_time.unite_measure = split_response[6]
						self.diagnostic.status = 200
						if float(self.pesa_real_time.gross_weight) <= self.min_weight:
							self.take_of_weight_on_startup = False
							self.take_of_weight_before_weighing = False
					# Se formato stringa del peso in tempo reale non corretto, manda a video errore
					else:
						self.diagnostic.status = 201
						self.pesa_real_time.type = ""
						self.pesa_real_time.net_weight = ""
						self.pesa_real_time.gross_weight = ""
						self.pesa_real_time.tare = ""
						self.pesa_real_time.unite_measure = ""
						self.diagnostic.vl = ""
						self.diagnostic.rz = ""
					callCallback(self.callback_realtime) # chiamo callback
				######### Se in esecuzione la diagnostica ###########################################################################
				elif self.modope == "DIAGNOSTIC":
					# Controlla formato stringa della diagnostica, se corretta aggiorna oggetto e chiama callback
					if length_split_response == 4 and length_response == 19:
						self.pesa_real_time.status = "diagnostic in progress"
						if split_response[1] == "VL":
							self.diagnostic.vl = str(split_response[2]).lstrip() + " " + str(split_response[3])
						elif split_response[1] == "RZ":
							self.diagnostic.rz = str(split_response[2]).lstrip() + " " + str(split_response[3])
						self.diagnostic.status = 200
					# Se formato stringa della diagnostica non corretto, manda a video errore
					else:
						self.diagnostic.status = 201
					callCallback(self.callback_diagnostic) # chiamo callback
					self.pesa_real_time.status = "D"
					self.pesa_real_time.type = ""
					self.pesa_real_time.net_weight = ""
					self.pesa_real_time.gross_weight = ""
					self.pesa_real_time.tare = ""
					self.pesa_real_time.unite_measure = ""
				######### Se in esecuzione pesata pid ###############################################################################
				elif self.modope == "WEIGHING":
					# Controlla formato stringa pesata pid, se corretta aggiorna oggetto
					if length_split_response == 5 and (length_response == 48 or length_response == 38):
						gw = (re.sub('[KkGg\x00\n]', '', split_response[2]).lstrip())
						t = (re.sub('[PTKkGg\x00\n]', '', split_response[3])).lstrip()
						nw = str(int(gw) - int(t))
						self.weight.weight_executed.net_weight = nw
						self.weight.weight_executed.gross_weight = gw
						self.weight.weight_executed.tare.value = t
						self.weight.weight_executed.tare.is_preset_tare = True if "PT" in split_response[3]	else False
						self.weight.weight_executed.unite_misure = split_response[2][-2:]
						self.weight.weight_executed.pid = split_response[4]
						self.weight.weight_executed.bil = split_response[1]
						self.weight.weight_executed.status = split_response[0]
						self.weight.weight_executed.executed = True
						self.weight.weight_executed.log = response
						self.weight.weight_executed.serial_number = self.diagnostic.serial_number
						self.diagnostic.status = 200
						self.take_of_weight_before_weighing = True if self.need_take_of_weight_before_weighing else False
				# Se formato stringa pesata pid non corretto, manda a video errore e setta oggetto a None
					else:
						self.diagnostic.status = 201
					callCallback(self.callback_weighing) # chiamo callback
					self.weight.weight_executed.net_weight = ""
					self.weight.weight_executed.gross_weight = ""
					self.weight.weight_executed.tare.value = ""
					self.weight.weight_executed.tare.is_preset_tare = False
					self.weight.weight_executed.unite_misure = ""
					self.weight.weight_executed.pid = ""
					self.weight.weight_executed.bil = ""
					self.weight.weight_executed.status = ""
					self.weight.weight_executed.executed = False
					self.weight.weight_executed.log = None
					self.weight.weight_executed.serial_number = self.diagnostic.serial_number
					self.weight.data_assigned = None
				######### Se in esecuzione tara, preset tara o zero #################################################################
				elif self.modope in ["TARE", "PRESETTARE", "ZERO"]:
					if self.modope == "TARE":
						self.pesa_real_time.status = "T"
					if self.modope == "PRESETTARE":
						self.pesa_real_time.status = "PT"						
					elif self.modope == "ZERO":
						self.pesa_real_time.status = "Z"
					callCallback(self.callback_tare_ptare_zero) # chiamo callback
					self.diagnostic.status = 200
				######### Se non è arrivata nessuna risposta ################################
				elif self.modope == "OK":
					# Controlla formato stringa, se corretto aggiorna ok_value
					if length_response == 2 and response == "OK":
						self.ok_value = response
						self.diagnostic.status = 200
					# Se formato stringa non valido setto ok_value a None
					else:
						self.diagnostic.status = 201
				elif self.modope in ["OPENRELE", "CLOSERELE"]:
					# Controlla formato stringa, se corretto aggiorna ok_value
					if length_response == 2 and response == "OK":
						self.diagnostic.status = 200
						if self.modope == "OPENRELE":
							key, value = self.port_rele
							self.port_rele = (key, 1)
						elif self.modope == "CLOSERELE":
							key,value = self.port_rele
							self.port_rele = (key, 0)
					# Se formato stringa non valido setto ok_value a None
					else:
						self.diagnostic.status = 201
					callCallback(self.callback_rele)
					self.port_rele = None
				elif length_response == 16 and "$" in response:
					self.diagnostic.status = 200
					self.code_identify = response
					callCallback(self.callback_code_identify)
					self.code_identify = ""
			elif self.diagnostic.status == 305:
				self.initialize_content()
		except TimeoutError as e:
			error = e
			self.diagnostic.vl = ""
			self.diagnostic.rz = ""
			self.pesa_real_time.status = ""
			self.pesa_real_time.type = ""
			self.pesa_real_time.net_weight = ""
			self.pesa_real_time.gross_weight = ""
			self.pesa_real_time.tare = ""
			self.pesa_real_time.unite_measure = ""
			self.weight.weight_executed.net_weight = ""
			self.weight.weight_executed.gross_weight = ""
			self.weight.weight_executed.tare = ""
			self.weight.weight_executed.unite_misure = ""
			self.weight.weight_executed.pid = ""
			self.weight.weight_executed.bil = ""
			self.weight.weight_executed.status = ""
			self.weight.weight_executed.log = None
			self.weight.weight_executed.serial_number = None
			self.weight.data_assigned = None
			self.ok_value = ""
			self.port_rele = None
			self.diagnostic.status = 301
			if self.modope == "WEIGHING":
				self.weight.status = self.diagnostic.status
				callCallback(self.callback_weighing)
				self.weight.status = ""
			elif self.modope in ["TARE", "PTARE", "ZERO"]:
				self.ok_value = self.diagnostic.status
				callCallback(self.callback_tare_ptare_zero)
				self.ok_value = ""
			elif self.modope == "REALTIME":
				self.pesa_real_time.status = self.diagnostic.status
				callCallback(self.callback_realtime) # chiamo callback
				self.pesa_real_time.status = ""
			error = "Not connection set"
			self.setModope("OK") if self.always_execute_realtime_in_undeground is False else self.setModope("REALTIME")
		except BrokenPipeError as e:
			error = "Node not receivable"
			self.diagnostic.status = 305
			self.setModope("OK") if self.always_execute_realtime_in_undeground is False else self.setModope("REALTIME")
		return self.diagnostic.status, self.modope, response, error