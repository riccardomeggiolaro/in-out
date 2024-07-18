# ==============================================================
# 		GESTIONE CONFIGURAZIONE				=
# ==============================================================

# ==== LIBRERIE DA IMPORTARE ===================================
import os
import json
import time
import lib.lb_log as lb_log
from dateutil import tz
import sys
# ==============================================================

# ==== FUNZIONI RICHIAMABILI FUORI DALLA LIBRERIA ==================
# Funzione per salvare le configurazioni in un file JSON specificato.
# Questa funzione scrive le configurazioni memorizzate nelle variabili globali g_config
# in un file JSON e aggiorna il timestamp dell'ultima modifica del file di configurazione.
def saveconfig():
	global g_config, g_config_ts  # Utilizza le variabili globali per memorizzare le configurazioni e il timestamp dell'ultima modifica.
	global config_path

	# Registra un messaggio di informazione sulla salvataggio del file di configurazione.
	lb_log.info("save config file: config.json")
	try:
		# Apre il file di configurazione in modalità di scrittura.
		with open(config_path + "config.json", "w", encoding="utf-8") as config:
			# Scrive il contenuto JSON delle configurazioni nelle variabili globali g_config nel file.
			config.write(json.dumps(g_config, indent=4, sort_keys=True))
	except Exception as e:
		# Registra un messaggio di errore se si verifica un problema durante il salvataggio del file di configurazione.
		lb_log.error("error saving : config.json - " + str(e))

def readconfig():
	# Funzione per leggere e caricare le configurazioni da un file JSON specificato.
	# Questa funzione legge il file di configurazione e aggiorna le variabili globali g_config
	# e g_config_ts con i valori letti dal file e il timestamp dell'ultima modifica del file.

	global g_config, g_config_ts, g_tz, g_vers, g_name  # Utilizza le variabili globali per memorizzare le configurazioni e il timestamp dell'ultima modifica.
	global config_path

	xloadbackup = False  # Flag per indicare se è necessario provare a caricare una copia di backup.

	# Verifica se il file di configurazione principale esiste.
	if os.path.exists(config_path + "config.json"):
		# Registra un messaggio di informazione sulla lettura del file di configurazione principale.
		lb_log.info("read config file: config.json")
		# Ottiene il timestamp dell'ultima modifica del file di configurazione principale.
		g_config_ts = os.stat(config_path + "config.json").st_mtime
		try:
			# Apre il file di configurazione principale in modalità di lettura.
			with open(config_path + "config.json", "r", encoding="utf-8") as config:
				# Legge il contenuto del file.
				data = config.read()
				# Carica il contenuto JSON nelle variabili globali g_config.
				g_config = json.loads(data)
				g_name = g_config["name"]
		except Exception as e:
			# Registra un messaggio di errore se si verifica un problema durante la lettura del file di configurazione principale.
			lb_log.error(f"error loading : config.json, Error: {e}")
			# Imposta il flag per indicare che è necessario provare a caricare una copia di backup.
			xloadbackup = True
	else:
		# Registra un messaggio di errore se il file di configurazione principale non esiste.
		lb_log.error("missing configuration : config.json")
		# Imposta il flag per indicare che è necessario provare a caricare una copia di backup.
		xloadbackup = True

	# Se è necessario provare a caricare una copia di backup.
	if xloadbackup:
		# Verifica se esiste un file di backup della configurazione.
		if os.path.exists(config_path + "config.backup"):
			# Registra un messaggio di avviso sulla lettura del file di backup della configurazione.
			lb_log.warning("read BACKUP config file: config.backup")
			# Ottiene il timestamp dell'ultima modifica del file di backup della configurazione.
			g_config_ts = os.stat(config_path + "config.backup").st_mtime
			try:
				# Apre il file di backup della configurazione in modalità di lettura.
				with open(config_path + "config.backup", "r", encoding="utf-8") as config:
					# Legge il contenuto del file.
					data = config.read()
					# Carica il contenuto JSON nelle variabili globali g_config.
					g_config = json.loads(data)
			except Exception as e:
				# Registra un messaggio di errore se si verifica un problema durante la lettura del file di backup della configurazione.
				lb_log.error(f"error loading : config.backup, Error: {e}")
			else:
				# Se il backup è stato caricato correttamente, registra un messaggio di informazione e salva la configurazione.
				lb_log.info("backup restored")
				saveconfig()
		else:
			# Registra un messaggio di errore se il file di backup della configurazione non esiste.
			lb_log.error("missing backup")


	if "locale" in g_config:
		g_tz = tz.gettz(g_config["locale"]["timezone"])
# ==============================================================

# ==== MAINPRGLOOP =============================================
# Questa funzione controlla periodicamente la presenza e la modifica del file di configurazione,
# e chiama la funzione readconfig() per aggiornare le configurazioni se necessario.
def mainprg():
	global g_enabled, g_config_ts, config_path  # Utilizza le variabili globali per abilitare il ciclo principale, il timestamp della configurazione e il percorso di lavoro.
	
	secwait = 5  # Intervallo di attesa in secondi tra i controlli del file di configurazione.

	# Ciclo principale del programma.
	while g_enabled:
		# Verifica se il file di configurazione principale esiste.
		if os.path.exists(config_path + "config.json"):
			# Verifica se il timestamp del file di configurazione è cambiato rispetto al timestamp memorizzato.
			if not os.stat(config_path + "config.json").st_mtime == g_config_ts:
				# Se il file di configurazione è stato modificato, chiama la funzione readconfig() per aggiornare le configurazioni.
				readconfig()
		# Se il file di configurazione principale non esiste ma è presente un file di backup della configurazione.
		elif os.path.exists(config_path + "config.backup"):
			# Carica le configurazioni dal file di backup.
			readconfig()
		# Attesa per un periodo di tempo prima di effettuare un nuovo controllo del file di configurazione.
		time.sleep(secwait)
	return False
# ==============================================================

# ==== START ===================================================
# funzione che fa partire la libreria
def start():
	lb_log.info("start")
	mainprg()
	lb_log.info("end")
# ==============================================================

def stop():
    pass	
 
# ==== INIT ====================================================
# funzione che inizializza delle globali
def init():
	# Definizione di variabili globali necessarie all'inizializzazione.
	# Queste variabili vengono utilizzate per memorizzare configurazioni,
	# stati, timestamp, percorsi di lavoro e altre informazioni utili.

	global g_config  # Variabile per memorizzare le configurazioni.
	global g_status  # Variabile per memorizzare gli stati.
	global g_config_ts  # Variabile per memorizzare il timestamp dell'ultima modifica del file di configurazione.
	global g_enabled  # Variabile per abilitare/disabilitare funzionalità.
	global g_vers  # Variabile per memorizzare la versione dell'applicazione.
	global g_name # Variabile per memorizzare il nome dell'applicazione.
	global g_workpath  # Variabile per memorizzare il percorso di lavoro.
	global g_defalogfile  # Variabile per memorizzare il percorso del file di log predefinito.
	global g_tz  # Variabile per memorizzare il fuso orario predefinito.
	global config_path  # Variabile per memorizzare il percorso della configurazione.
	global database_path

	# Ottiene il percorso della directory del modulo corrente.
	# Determina il percorso base a seconda se l'applicazione è in esecuzione come eseguibile o come sorgente
	base_path = sys._MEIPASS if hasattr(sys, 'frozen') else os.path.abspath(".")
	config_path = os.path.join(base_path, "")
	g_workpath = config_path.replace("/lib", "/")

	# Imposta la versione dell'applicazione.
	g_vers = ""
	# Imposta il nome dell'applicazione.
	g_name = ""
	# Inizializza le variabili globali con valori predefiniti.
	g_config = {}
	g_status = {}
	g_enabled = True
	g_config_ts = ""
	# Imposta il percorso predefinito per il file di log.
	g_defalogfile = g_workpath + "/service.log"
	# Imposta il fuso orario predefinito su 'Europe / Rome'.
	g_tz = tz.gettz('Europe / Rome')

	# Registra un messaggio di informazione sulla inizializzazione delle configurazioni.
	lb_log.info("config initialize")
	# Richiama la funzione 'readconfig()', che è progettata per leggere e caricare le configurazioni da un file JSON specificato.
	# Questa chiamata alla funzione leggerà il file di configurazione e aggiornerà le variabili globali 'g_config' e 'g_config_ts'
	# con i valori letti dal file e il timestamp dell'ultima modifica del file di configurazione.
	readconfig()
# ==============================================================