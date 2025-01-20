import libs.lb_log as lb_log
from libs.lb_utils import callCallback
import re
from modules.md_weigher.setup_terminal import Terminal
from libs.lb_capture_camera import capture_camera_image
from modules.md_weigher.types import ImageCaptured

class Dgt1(Terminal):
	def __init__(self, self_config, max_weight, min_weight, division, cam1, cam2, cam3, cam4, maintaine_session_realtime_after_command, diagnostic_has_priority_than_realtime, node, terminal, run, data, name):
		# Chiama il costruttore della classe base
		super().__init__(self_config, max_weight, min_weight, division, cam1, cam2, cam3, cam4, maintaine_session_realtime_after_command, diagnostic_has_priority_than_realtime, node, terminal, run, data, name)
    
	def command(self):
		self.modope = self.modope_to_execute # modope assume il valore di modope_to_execute, che nel frattempo può aver cambiato valore tramite le funzioni richiambili dall'esterno
		# in base al valore del modope scrive un comando specifico nella conn
		if self.modope == "DIAGNOSTICS":
			if self.valore_alterno == 1: # se valore alterno uguale a 1 manda MVOL per ottnere determinati dati riguardanti la diagnostica
				self.write("MVOL")
			elif self.valore_alterno == 2: # altrimenti se valore alterno uguale a 2 manda RAZF per ottnere altri determinati dati riguardanti la diagnostica
				self.write("RAZF")		
				self.valore_alterno = 0 # imposto valore uguale a 0
			self.valore_alterno = self.valore_alterno + 1 # incremento di 1 il valore alterno
		elif self.modope == "REALTIME":
			self.write("RALL")
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
		elif self.modope == "VER":
			self.write("VER")
			self.modope_to_execute = "OK" # setto modope_to_execute a stringa vuota per evitare che la stessa funzione venga eseguita anche nel prossimo ciclo
		elif self.modope == "SN":
			self.write("SN")
			self.modope_to_execute = "OK" # setto modope_to_execute a stringa vuota per evitare che la stessa funzione venga eseguita anche nel prossimo ciclo
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
					self.setModope("OK")
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
			if self.modope not in ["REALTIME", "DIAGNOSTIC"]:
				self.setModope("OK")
		except BrokenPipeError as e:
			self.diagnostic.status = 305
			self.diagnostic.firmware = None
			self.diagnostic.model_name = None
			self.diagnostic.serial_number = None
			if self.modope not in ["REALTIME", "DIAGNOSTIC"]:
				self.setModope("OK")
		except ValueError as e:
			self.diagnostic.status = 201
			self.diagnostic.firmware = None
			self.diagnostic.model_name = None
			self.diagnostic.serial_number = None
			if self.modope not in ["REALTIME", "DIAGNOSTIC"]:
				self.setModope("OK")

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
					if length_split_response == 10 and length_response == 63:
						nw = (re.sub('[KkGg\x00\n]', '', split_response[2]).lstrip())
						gw = (re.sub('[KkGg\x00\n]', '', split_response[3]).lstrip())
						t = (re.sub('[KkGg\x00\n]', '', split_response[4]).lstrip())
						self.pesa_real_time.status = split_response[0]
						self.pesa_real_time.type = "GS" if t == "0" else "NT"
						self.pesa_real_time.net_weight = nw
						self.pesa_real_time.gross_weight = gw
						self.pesa_real_time.tare = t
						self.pesa_real_time.unite_measure = split_response[2][-2:]
						self.diagnostic.status = 200
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
						lb_log.error(f"Received string format does not comply with the REALTIME function: {response}")
					callCallback(self.callback_realtime) # chiamo callback
				######### Se in esecuzione la diagnostica ###########################################################################
				elif self.modope == "DIAGNOSTICS":
					# Controlla formato stringa della diagnostica, se corretta aggiorna oggetto e chiama callback
					if length_split_response == 4 and length_response == 19:
						self.pesa_real_time.status = "diagnostics in progress"
						if split_response[1] == "VL":
							self.diagnostic.vl = str(split_response[2]).lstrip() + " " + str(split_response[3])
						elif split_response[1] == "RZ":
							self.diagnostic.rz = str(split_response[2]).lstrip() + " " + str(split_response[3])
						self.diagnostic.status = 200
					# Se formato stringa della diagnostica non corretto, manda a video errore
					else:
						pass
						self.diagnostic.status = 201
						lb_log.error(f"Received string format does not comply with the DIAGNOSTICS function: {response}")
					callCallback(self.callback_diagnostics) # chiamo callback
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
						self.weight.weight_executed.tare = t
						self.weight.weight_executed.unite_misure = split_response[2][-2:]
						self.weight.weight_executed.pid = split_response[4]
						self.weight.weight_executed.bil = split_response[1]
						self.weight.weight_executed.status = split_response[0]
						self.weight.weight_executed.executed = True
						if self.cam1:
							image_capture1 = capture_camera_image(self.cam1.ip, self.cam1.username, self.cam1.password)
							self.weight.image1 = ImageCaptured(**image_capture1)
						if self.cam2:
							image_capture2 = capture_camera_image(self.cam2.ip, self.cam2.username, self.cam2.password)
							self.weight.image2 = ImageCaptured(**image_capture2)
						if self.cam3:
							image_capture3 = capture_camera_image(self.cam3.ip, self.cam3.username, self.cam3.password)
							self.weight.image3 = ImageCaptured(**image_capture3)
						if self.cam4:
							image_capture4 = capture_camera_image(self.cam4.ip, self.cam4.username, self.cam4.password)
							self.weight.image4 = ImageCaptured(**image_capture4)
						self.diagnostic.status = 200
				# Se formato stringa pesata pid non corretto, manda a video errore e setta oggetto a None
					else:
						self.diagnostic.status = 201
						lb_log.error(f"Received string format does not comply with the WEIGHING function: {response}")
					callCallback(self.callback_weighing) # chiamo callback
					self.weight.weight_executed.net_weight = ""
					self.weight.weight_executed.gross_weight = ""
					self.weight.weight_executed.tare = ""
					self.weight.weight_executed.unite_misure = ""
					self.weight.weight_executed.pid = ""
					self.weight.weight_executed.bil = ""
					self.weight.weight_executed.status = ""
					self.weight.weight_executed.executed = False
					self.weight.data_assigned = None
					self.weight.image1 = None
					self.weight.image2 = None
					self.weight.image3 = None
					self.weight.image4 = None
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
						lb_log.error(f"Received string format does not comply with the function {self.modope}: {response}")
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
			self.weight.data_assigned = None
			self.ok_value = ""
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
			self.setModope("OK")
		except BrokenPipeError as e:
			error = "Node not receivable"
			self.diagnostic.status = 305
			self.setModope("OK")
		return self.diagnostic.status, self.modope, response, error