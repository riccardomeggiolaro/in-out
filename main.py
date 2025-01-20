# -*- coding: utf-8 -*-

# ==============================================================
#						- LOADER -							  =
# ==============================================================

# ==== LIBRERIE DA IMPORTARE ===================================
import os
import time
import threading
import sys
import signal
import libs.lb_config as lb_config  # Importa il modulo per la configurazione
import libs.lb_log as lb_log  # Importa il modulo per il logger
import modules.md_weigher.md_weigher as md_weigher
# import modules.md_rfid as md_rfid
import modules.md_tunnel_connections.md_tunnel_connections as md_tunnel_connections
import applications.app_api as app_api
from libs.lb_utils import GracefulKiller, createThread, startThread, closeThread
import libs.lb_database as lb_database
# ==============================================================

APPS = [app_api]

MODULES = [md_weigher, md_tunnel_connections]

# ==== MAINPRGLOOP =============================================
# Configura globale e lo stato del programma.
# Carica moduli esterni e avvia i thread corrispondenti.
def mainprg():
	# Imposta il tempo di attesa tra aggiornamenti.
	secwait = 0.5

	# Carica thread per la configurazione in background.
	thr_config = createThread(lb_config.start)

	# Carica thread per il logger in background.
	thr_logger = createThread(lb_log.start)

	# Carica thread per i mdouli esterni.
	modules_thr = {}
	lb_log.info("loading mdoules...")
	for modulepath in MODULES:
		# Estrae informazioni sul modulo.
		name_module = modulepath.name_module
		lb_log.info("... " + name_module)
		# Inizializza il modulo.
		modulepath.init()  # Inizializzazione della applicazione
		# Crea e avvia il thread della applicazione.
		thread = createThread(modulepath.start)
		modules_thr[name_module] = {"name_module": name_module, "module": modulepath, "thread": thread}

	# Carica thread per le applicazioni esterne.
	app_thr = {}
	lb_log.info("loading applications...")
	for apppath in APPS:
		# Estrae informazioni sulla applicazione.
		name_app = apppath.name_app
		lb_log.info("... " + name_app)
		# Inizializza la applicazione.
		apppath.init()  # Inizializzazione della applicazione
		# Crea e avvia il thread della applicazione.
		thread = createThread(apppath.start)
		app_thr[name_app] = {"name_app": name_app, "application": apppath, "thread": thread}

	while lb_config.g_enabled:
		# === THREAD Livello 0:
		startThread(thr_config)
		startThread(thr_logger)

		# === THREAD Livello 3:
		# Applicazioni
		for appname in app_thr.keys():  # Per ogni applicazione
			startThread(app_thr[appname]["thread"])
		# Attesa loop
		time.sleep(secwait)  # Mette in pausa l'esecuzione del loop per un certo periodo di tempo

	# Chiusura dei thread collegati
	lb_log.info("ending threads:")  # Logga un messaggio informativo

	for appname in app_thr.keys(): # Per ogni applicazione
		lb_log.info("::killing %s" % appname) # Logga un messaggio informativo
		closeThread(app_thr[appname]["thread"], app_thr[appname]["application"])

	if thr_config.is_alive(): # Se il thread della configurazione e' attivo
		lb_log.info("::killing configuration") # Logga un messaggio informativo
		closeThread(thr_config)

	if thr_logger.is_alive(): # Se il thread del logger e' attivo
		lb_log.info("::killing logger") # Logga un messaggio informativo
		closeThread(thr_logger)
# ==============================================================

# ==== AVVIO PROGRAMMA PRINCIPALE ========================
# Funzione principale del programma.
# Questa funzione gestisce l'avvio e l'esecuzione del programma principale,
# inizializzando i moduli necessari, controllando la configurazione dell'applicazione
# e avviando il ciclo principale di esecuzione (mainprg).
if __name__ == "__main__":
	# Crea un'istanza della classe GracefulKiller (non definita nel codice fornito)
	killer = GracefulKiller()  # Inizializza l'oggetto per la gestione della terminazione sicura

	# Inizializza il modulo lb_config e imposta la variabile globale g_workpath
	lb_config.init()  # Inizializza il modulo di configurazione

	# Inizializza il modulo lb_log e scrive un messaggio di log
	lb_log.init()  # Inizializza il modulo di logger
	lb_log.info("====================== BARON " + lb_config.g_name + " rel. " + lb_config.g_vers +" =======================")  # Stampa un messaggio di log con la versione

	# Controlla se l'applicazione e' abilitata e chiama la funzione mainprg se lo e'
	if lb_config.g_enabled:  # Se l'applicazione e' abilitata
		mainprg()  # Avvia il programma principale

	lb_log.info("exitpoint.")
	print("")
	sys.exit()  # Termina l'esecuzione del programma
# ==============================================================
