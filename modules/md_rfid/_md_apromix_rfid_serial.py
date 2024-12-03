# ==============================================================
# = Module......: md_apromix_rfid					   =
# = Description.: Interfaccia di lettura tessere rfid		=
# = Author......: Riccardo Meggiolaro				   =
# = Last rev....: 0.0002					   =
# -------------------------------------------------------------=
# 0.0002 : Implementato....
# 0.0001 : Creazione del modulo
# ==============================================================

# ==== Dati necessari nel file .json dentro setup per la corretta funzione del modulo
        # "apromix_rfid": {
        #     "serialport": {
        #         "name": "/dev/ttyS1",
        #         "speed": 9600,
        #         "time_read": 1
        #     }
        # },
# ==============================================================

# ==== LIBRERIE DA IMPORTARE ===================================
import inspect
__frame = inspect.currentframe()
namefile = inspect.getfile(__frame).split("/")[-1].replace(".py", "")
import lib.lb_log as lb_log
import lib.lb_config as lb_config
import time
import serial
import binascii
import inspect
from typing import Callable, Optional
from pydantic import BaseModel
# ==============================================================

class SerialPort(BaseModel):
	serial_port_name: str
	baudrate: int = 19200
	timeout: int = 1
	protocol: str

class SetupRfid(BaseModel):
	pass

# ==== FUNZIONI RICHIAMABILI DA MODULI ESTERNI =================
# funzione che inizializza delle globali e la seriale
def initialize(connection: SerialPort, setup: SetupRfid):
	lb_log.info("initialize")
	global seriale2
	global read_seriale2
	global status_card_reader
	global config2
	try:
		if isinstance(seriale2, serial.Serial) and seriale2.is_open:
			seriale2.close()
		seriale2 = None
		# inizializzazione della seriale
		seriale2 = serial.Serial(connection.serial_port_name,
								baudrate=connection.baudrate,
								timeout=connection.timeout)
		# aspetta che la seriale sia aperta un massimo di tot secondi, altrimenti manda a video errore
		if wait_for_serial_ready():
			config2 = {
				"setup": setup.dict(),
				"connection": {
					"serial_port_name": connection.serial_port_name,
					"baudrate": connection.baudrate,
					"timeout": connection.timeout,
					"protocol": connection.protocol
				}
       		}			
			status_card_reader = 305
			lb_log.info("------------------------------------------------------")
			lb_log.info("INITIALIZATION")
			lb_log.info("INFOSTART: " + "Accensione con successo")
			lb_log.info("------------------------------------------------------")
		else:
			lb_log.error("Serial port not ready after initialization.")
	except serial.SerialException as e:
		lb_log.error(f"SerialException: {e}")
	except ValueError as e:
		lb_log.error(f"ValueError: {e}")
	except Exception as e:
		lb_log.error(f"Exception: {e}. Seriale: {seriale2}")
	return status_card_reader == 305 # ritorno True o False in base se status della pesa è 200

# Funzione per settare la funzione di callback
# Il parametro può essere omesso o passato come funzione che ha un solo parametro come stringa
def setAction(cb_cardcode: Callable[[str], any] = None):
	global callback_cardcode
	global last_cardcode
	try:
		check_cb_cardcode = checkCallbackFormat(cb_cardcode) # controllo se la funzione cb_tare_ptare_zero è richiamabile
		if check_cb_cardcode: # se è richiamabile assegna alla globale callback_tare_ptare_zero la funzione passata come parametro
			callback_cardcode = lambda: cb_carcode(last_cardcode)
	except Exception as e:
		lb_log.error(e)

def getConfig():
	global config2
	global status_card_reader

	data = copy.copy(config2)
	data["status"] = status_card_reader

def is_initializated_successfully():
	global status_card_reader
	return status_card_reader == 305

def status_connection_weigher():
	global status_card_reader
	return status_card_reader

def setSetup(setup: SetupRfid):
	try:
		global config2
	except Exception as e:
		lb_log.info(e)
	return config2["setup"]

def deleteConfig():
	try:
		global seriale2
		global config2
		global status_card_reader
		status_card_reader = 301
		time.sleep(1)
		if isinstance(seriale2, serial.Serial) and seriale2.is_open:
			seriale2.flush()
			seriale2.close()
		seriale2 = None
		config2 = {
			"setup": {},
			"connection": {
				"serial_port_name": None,
				"baudrate": None,
				"timeout": None,
				"protocol": None
			}
		}
		return True
	except:
		return False
# ==============================================================

# ==== FUNZIONI RICHIAMABILI DENTRO IL MODULO ==================
# aspetta un massimo di tot secondi per controllare e ritornare se la seriale sia aperta 
def wait_for_serial_ready(max_attempts=5, delay_seconds=1):
	global seriale2
	for _ in range(max_attempts):
		if isinstance(seriale2, serial.Serial) and seriale2.is_open:
			return True
		time.sleep(delay_seconds)
	return False

# controlla se la callback è eseguibile, se si la esegue
def callCallback(callback):
	if callable(callback):
		callback()

# controlla se il formato della callback è giusto, ovvero se è richiamabile e se ha 1 solo parametro
def checkCallbackFormat(callback):
	if callable(callback):
		signature = inspect.signature(callback)
		num_params = len(signature.parameters)
		if num_params == 1:
			return True
	return False
# ==============================================================

# ==== MAINPRGLOOP =============================================
# funzione che scrive e legge in loop seriale e in base alla stringa ricevuta esegue funzioni specifiche
def mainprg():
	global seriale2
	global read_seriale2
	global status_card_reader
	global last_cardcode
	global callback_cardcode
	while lb_config.g_enabled:
		if status_card_reader == 305:
			read_seriale2 = seriale2.readline().strip()
			if read_seriale2:
				hex_string = binascii.hexlify(read_seriale2).decode('UTF-8') # Converte la sequenza di byte ottenuta dalla seriale in una stringa esadecimale    
				length_seriale2 = len(hex_string) # Ottengo la lunghezza della stringa convertita in esadecimale
				# Se la stringa ha 14 caratteri controllo che il checksum sia corretto e chiamo la callback se non lo ho ancora fatto
				if length_seriale2 == 14:
					byte_sequence = bytes.fromhex(hex_string[0:-2]) # Converte la stringa esadecimale in una sequenza di byte tranne le ultime due lettere
					checksum = hex_string[-2:] # ottiene checksum dalla stringa esadecimale
					bcc = (-sum(byte_sequence)) % 256 # Calcola il checksum utilizzando la formula BCC = -MOD256
					bcc_hex = format(bcc, '02X') # Formatta il risultato del checksum in esadecimale a due cifre
					cardcode = hex_string[2:-2]
					if bcc_hex.lower() == checksum.lower():
						# Controllo che il codice tessera non sia già stato elaborato
						if cardcode != last_cardcode:
							last_cardcode = cardcode # Setto il last_cardcode con il codice tessera corrente
							callCallback(callback_cardcode) # Chiamo callback
					# Se il checksum non è corretto mando a video errore
					else:
						lb_log.error(f"Incorrect checksum of the card code {cardcode}")
				# Se la stringa ha 18 caratteri controllo che le ultime 4 lettere siano uguali a ff01 come segno che la carta è stata rimossa dal sensore
				elif length_seriale2 == 18:
					if hex_string[-4:] == "ff01":
						last_cardcode = "" # Setto last_cardcode a stringa vuota
				# Se la stringa ha 4 caratteri controllo che siano uguali a ff01 come segno che la carta è stata rimossa dal sensore
				elif length_seriale2 == 4:
					if hex_string == "ff01":
						last_cardcode = "" # Setto last_cardcode a stringa vuota
			time.sleep(0.1)
		else:
			time.sleep(0.1)
# ==============================================================

# ==== START ===================================================
# funzione che fa partire il modulo
def start():
	global seriale2
	lb_log.info("start")
	mainprg() # fa partire la funzione che scrive e legge la seriale in loop
	lb_log.info("end")
	# se la globale seriale è di tipo seriale ed è aperta la chiude
	if isinstance(seriale2, serial.Serial) and seriale2.is_open:
		seriale2.close()
# ==============================================================

def stop():
    pass

# ==== INIT ====================================================
# funzione che dichiara tutte le globali
def init():
	lb_log.info("init")
	global seriale2
	global read_seriale2
	global callback_cardcode
	global status_card_reader
	global last_cardcode
	global config2
	global NAME_MODULE
	global TYPE_MODULE
	global TYPE_CONNECTION
	global CLASS_CONNECTION
	global CLASS_SETUP

	seriale2 = None
	read_seriale2 = ""
	callback_cardcode = ""
	status_card_reader = 301
	initializated2 = False
	last_cardcode = ""
	config2 = {
		"setup": {},
		"connection": {
			"serial_port_name": None,
			"baudrate": None,
			"timeout": None,
			"protocol": None
		}
	}
	NAME_MODULE = "apromix"
	TYPE_MODULE = "rfid"
	TYPE_CONNECTION = "serial"
	CLASS_CONNECTION = SerialPort
	CLASS_SETUP = SetupRfid
# ==============================================================

def info():
	global NAME_MODULE
	global TYPE_MODULE
	global TYPE_CONNECTION
	global CLASS_CONNECTION
	global CLASS_SETUP
	return {
		"name_module": NAME_MODULE,
		"type_module": TYPE_MODULE,
  		"type_connection": TYPE_CONNECTION,
		"class_connection": CLASS_CONNECTION,
		"class_setup": CLASS_SETUP
	}