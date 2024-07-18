# ==============================================================
# = App......: main					   =
# = Description.: Applicazione			   =
# = Author......: Riccardo Meggiolaro				   =
# = Last rev....: 0.0002					   =
# -------------------------------------------------------------=
# 0.0002 : Implementato....
# 0.0001 : Creazione della applicazione
# ==============================================================

# ==== Dati necessari nel file .json dentro setup per la corretta funzione dell'applicazione
        # "main_application": {
        #     "redis_config": { # configurazione server redis
        #         "host": "localhost",
        #         "port": 6379,
        #         "db": 0,
        #         "back_channel": "back", # canale dove scrive il backend e ascolta il frontend
        #         "front_channel": "front", # canale dove scrive il frontend e ascolta il backend
        #         "machine_channel": "machine"
        #     },
        #     "weight_after_scanned_card_code": false # imposta se la pesata deve essere eseguita in automatico dopo la lettura del codice tessera
        # }
# ==============================================================

# ==== LIBRERIE DA IMPORTARE ===================================
import lb_log
import lb_config
import time
import md_dgt1
import redis
import json
import threading
import md_apromix_rfid
# ==============================================================

# ==== FUNZIONI RICHIAMABILI DENTRO LA APPLICAZIONE =================
# Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di peso in tempo reale
def Callback_Realtime(data: dict):
	global back_channel
	sendData(back_channel, json.dumps(data))
	# logica da inserire (salvare su database, ecc..)

# Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di diagnostica
def Callback_Diagnostic(data: dict):
	global back_channel
	sendData(back_channel, json.dumps(data))
	# logica da inserire (salvare su database, ecc..)

# Callback che verrà chiamata dal modulo dgt1 quando viene ritornata un stringa di pesata
def Callback_Weighing(data: dict):
	global back_channel
	global data_machine
	odata = data
	odata["data_in_execution"] = data_machine["data_machine"]["data_in_execution"]
	sendData(back_channel, json.dumps(odata))
	# logica da inserire (salvare su database, ecc..)

# Callback che verrà chiamata dal modulo apromix_rfid quando viene ritornata un stringa di codice tessera
def Callback_Cardcode(data: str):
	global cardcode
	global machine_channel
	cardcode = data
	sendData(machine_channel, json.dumps({"cardcode": cardcode}))
	if lb_config.g_setup["main_application"]["weight_after_scanned_card_code"]:
		result = md_dgt1.weighing()

# Funzione che pubblica un dato su una canale redis
def sendData(channel, data):
	global redis_conn
	redis_conn.publish(channel, data)

def change_stream(stream, value):
    global redis_conn
    redis_conn.xadd(stream, value)

# Funzione che esegue i comandi verso la pesa in base alla stringa che gli arriva
def handle_action_data(message):
	global data_machine
	global machine_channel

	#data={"weight":{"command":"do_weight"}}
	odata = json.loads(message['data'])
	result = ""
# 	# Stiamo parlando di pesatura ?
	if "weight" in odata:
		if odata["weight"]["command"] == "weighing": # effettua una pesata
			result = md_dgt1.weighing()
			lb_log.info(result)
		elif odata["weight"]["command"] == "tare":
			result = md_dgt1.tare()
		elif odata["weight"]["command"] == "resettare":
			result = md_dgt1.resetTare()
		elif odata["weight"]["command"] == "presettare":
			result = md_dgt1.presetTare(int(odata["weight"]["tare"]))
		elif odata["weight"]["command"] == "zero":
			result = md_dgt1.zero()
		elif odata["weight"]["command"] == "realtime":
			result = md_dgt1.realTime()
		elif odata["weight"]["command"] == "start_diagnostic":
			result = md_dgt1.diagnsotics()
		elif odata["weight"]["command"] == "stop_diagnostic":
			md_dgt1.stopCommand()
			result = md_dgt1.realTime()
		elif odata["weight"]["command"] == "stop_all_command":
			result = md_dgt1.stopCommand()
			lb_log.info(result)
	elif "data_in_execution" in odata:
		if odata["data_in_execution"] == "get":
			pass
		if "plate" in odata["data_in_execution"]:
			data_machine["plate"] =	odata["data_in_execution"]["plate"]
		if "vehicle" in odata["data_in_execution"]:
			data_machine["vehicle"] = odata["data_in_execution"]["vehicle"]
		if "customer" in odata["data_in_execution"]:
			data_machine["customer"] = odata["data_in_execution"]["customer"]
		sendData(machine_channel, json.dumps(data_machine))
# ==============================================================

# ==== MAINPRGLOOP =============================================
# funzione che si connette a redis, setta i moduli e imposta le callback da richiamare dentro i moduli
def mainprg():
	global redis_conn
	global front_channel
	global machine_channel
	global data_machine
	
	pub_sub = redis_conn.pubsub() # Crea un oggetto PubSub per la comunicazione con Redis
	pub_sub.subscribe(**{front_channel: handle_action_data}) # Iscriviti al canale di azione per gestire i dati in arrivo	
	thread = pub_sub.run_in_thread(sleep_time=0.01) # Avvia un thread per l'ascolto dei messaggi Redis

	# Inizializza i moduli
	init = md_dgt1.initialize()
	rfid = md_apromix_rfid.initialize()

	# Controlla se l'inizializzazione è riuscita e se il thread è un'istanza di threading.Thread
	if init and rfid and isinstance(thread, threading.Thread):
		# Imposta le callback da richiamare dentro i moduli
		md_dgt1.setAction(cb_diagnostic=Callback_Diagnostic, cb_realtime=Callback_Realtime, cb_weighing=Callback_Weighing)
		md_apromix_rfid.setAction(cb_carcode=Callback_Cardcode)
		data_machine["data_machine"]["settings"] = md_dgt1.getData()
		sendData(machine_channel, json.dumps(data_machine))
		# Ciclo fino a quando il programma è abilitato
	while lb_config.g_enabled: 
		time.sleep(0.1)
	
	# Interrompe il thread del publisher/subscriber se è attivo
	if isinstance(thread, threading.Thread):
	    thread.stop()
# ==============================================================


# ==== START ===================================================
# funzione che fa partire la applicazione
def start():
	lb_log.info("start")
	mainprg() 
	lb_log.info("end")
# ==============================================================

def stop():
    pass

# ==== INIT ====================================================
# funzione che dichiara tutte le globali
def init():
	global redis_conn
	global back_channel
	global front_channel
	global machine_channel
	global data_machine
 
	redis_conn = redis.StrictRedis(
		host=lb_config.g_setup["main_application"]["redis_config"]["host"], 
		port=lb_config.g_setup["main_application"]["redis_config"]["port"], 
		db=lb_config.g_setup["main_application"]["redis_config"]["db"], decode_responses=True) # creo la connessione al broker di messaggi redis
	back_channel = lb_config.g_setup["main_application"]["redis_config"]["back_channel"] # assegno il canale dove vengono passati tutti i dati rigurdanti le stringhe ottenute dalla pesa dopo i comandi
	front_channel = lb_config.g_setup["main_application"]["redis_config"]["front_channel"] # assegno il canale dove vengono passati tutti i dati riguardanti le azioni da effettuare sulla pesa
	machine_channel = lb_config.g_setup["main_application"]["redis_config"]["machine_channel"]
	data_machine = {
			"data_machine": {
				"settings": {
					"firmware": "",
					"model_name": "",
					"serial_number": "",
					"division": None,
					"min_weight": None,
					"max_weight": None
				},
				"data_in_execution": {
					"customer": "",
					"vehicle": None,
					"plate": None,
					"social_reason": None,
					"number_card": None,
					"card_code": None
				}			
		}
	}
# ==============================================================