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
import lib.lb_config as lb_config  # Importa il modulo per la configurazione
import lib.lb_log as lb_log  # Importa il modulo per il logger
import modules.md_weigher.md_weigher as md_weigher
# import modules.md_rfid as md_rfid
import app.app_api as app_api
# ==============================================================

MODULES = [md_weigher]
APPS = [app_api]

# ==== CLASSE PER KILLARE I PROCESSI ===========================
# Classe per gestire l'uscita controllata del programma in risposta a segnali come SIGINT (Ctrl+C) e SIGTERM.
class GracefulKiller:
	# Flag di terminazione, inizializzato a False.
	kill_now = False

	# Metodo di inizializzazione che registra i gestori dei segnali.
	def __init__(self):
		signal.signal(signal.SIGINT, self.exit_gracefully)
		signal.signal(signal.SIGTERM, self.exit_gracefully)

	# Metodo invocato quando viene ricevuto un segnale.
	def exit_gracefully(self, *args):
		# Registra un messaggio informativo che indica l'uscita dovuta a un segnale.
		lb_log.info("SIGTEM exit")
		# Imposta un flag nella configurazione globale per indicare la terminazione controllata.
		lb_config.g_enabled = False
# ==============================================================

# ==== MAINPRGLOOP =============================================
# Configura globale e lo stato del programma.
# Carica moduli esterni e avvia i thread corrispondenti.
def mainprg():
	# Imposta il tempo di attesa tra aggiornamenti.
	secwait = 0.5

	# Inizializza lo stato globale del programma.
	lb_config.g_status["board"] = {}
	lb_config.g_status["board"]["status-code"] = 0
	lb_config.g_status["board"]["network"] = {}
	lb_config.g_status["board"]["cpu"] = {}
	lb_config.g_status["board"]["battery"] = {}
	lb_config.g_status["board"]["gsm"] = {}
	lb_config.g_status["board"]["gsm"]["imei"] = ""
	lb_config.g_status["socket"] = {}
	lb_config.g_status["socket"]["server"] = ""
	lb_config.g_status["socket"]["port"] = 0
	lb_config.g_status["socket"]["is_connected"] = False
	lb_config.g_status["operative"] = {}

	# Carica thread per la configurazione in background.
	thr_config = threading.Thread(target=lb_config.start)

	# Carica thread per il logger in background.
	thr_logger = threading.Thread(target=lb_log.start)

	# Carica thread per i moduli esterni.
	md_thr = {}  # Dizionario per archiviare informazioni sui moduli
	lb_log.info("loading modules...")
	for modpath in MODULES:
		# Estrae informazioni sul modulo.
		namefile = modpath.namefile
		lb_log.info("... " + namefile)
		# Inizializza il modulo.
		modpath.init()  # Inizializzazione del modulo
		# Crea e avvia il thread del modulo.
		thread = threading.Thread(target=modpath.start, daemon=True)
		md_thr[namefile] = {"filename": namefile, "module": modpath, "thread": thread}

	# Carica thread per le applicazioni esterne.
	app_thr = {}
	lb_log.info("loading applications...")
	for apppath in APPS:
		# Estrae informazioni sulla applicazione.
		namefile = apppath.namefile
		lb_log.info("... " + namefile)
		# Inizializza la applicazione.
		apppath.init()  # Inizializzazione della applicazione
		# Crea e avvia il thread della applicazione.
		thread = threading.Thread(target=apppath.start, daemon=True)
		app_thr[namefile] = {"filename": namefile, "application": apppath, "thread": thread}

	while lb_config.g_enabled:
		# === THREAD Livello 0:
		# Configurazione
		if not thr_config.is_alive():  # Se il thread di configurazione non e' attivo
			thr_config = threading.Thread(target=lb_config.start)  # Ricrea il thread di configurazione
			thr_config.start()  # Avvia il thread di configurazione
		# Logger
		if not thr_logger.is_alive():  # Se il thread di logger non e' attivo
			thr_logger = threading.Thread(target=lb_log.start)  # Ricrea il thread di logger
			thr_logger.start()  # Avvia il thread di logger

		# === THREAD Livello 3:
		# Moduli
		for modname in md_thr.keys():  # Per ogni modulo
			if not md_thr[modname]["thread"].is_alive():  # Se il thread del modulo non e' attivo
				md_thr[modname]["thread"] = threading.Thread(target=md_thr[modname]["module"].start)  # Ricrea il thread del modulo
				md_thr[modname]["thread"].start()  # Avvia il thread del modulo
		# Applicazioni
		for appname in app_thr.keys():  # Per ogni applicazione
			if not app_thr[appname]["thread"].is_alive():  # Se il thread della applicazione non e' attivo
				app_thr[appname]["thread"] = threading.Thread(target=app_thr[appname]["application"].start)  # Ricrea il thread della applicazione
				app_thr[appname]["thread"].start()  # Avvia il thread della applicazione
		# Attesa loop
		time.sleep(secwait)  # Mette in pausa l'esecuzione del loop per un certo periodo di tempo

	# Chiusura dei thread collegati
	lb_log.info("ending threads:")  # Logga un messaggio informativo

	for modname in md_thr.keys():  # Per ogni modulo
		if md_thr[modname]["thread"].is_alive():  # Se il thread del modulo e' attivo
			lb_log.info("..killing: %s" % modname)  # Logga un messaggio informativo
			md_thr[modname]["module"].stop()
			md_thr[modname]["thread"].join()  # Aspetta che il thread del modulo sia terminato prima di proseguire

	for appname in app_thr.keys(): # Per ogni applicazione
		if app_thr[appname]["thread"].is_alive(): # Se il thread della applicazione e' attivo
			lb_log.info("::killing %s" % appname) # Logga un messaggio informativo
			app_thr[appname]["application"].stop()
			app_thr[appname]["thread"].join() # Aspetta che il thread della applicazione sia terminato prima di proseguire

	if thr_config.is_alive(): # Se il thread della configurazione e' attivo
		lb_log.info("::killing configuration") # Logga un messaggio informativo
		thr_config.stop()
		thr_config.join() # Aspetta che il thread della configurazione sia terminato prima di proseguire

	if thr_logger.is_alive(): # Se il thread del logger e' attivo
		lb_log.info("::killing logger") # Logga un messaggio informativo
		thr_logger.stop()
		thr_logger.join() # Aspetta che il thread del logger sia terminato prima di proseguire
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
	lb_config.g_vers = "0.0002"

	print(os.path.exists(lb_config.g_workpath + "modules/md_weigher.py"))

	# Inizializza il modulo lb_log e scrive un messaggio di log
	lb_log.init()  # Inizializza il modulo di logger
	lb_log.info("====================== BARON " + lb_config.g_name + " rel. " + lb_config.g_vers +" =======================")  # Stampa un messaggio di log con la versione

	# Controlla se l'applicazione e' abilitata e chiama la funzione mainprg se lo e'
	if lb_config.g_enabled:  # Se l'applicazione e' abilitata
		mainprg()  # Avvia il programma principale

	# Scrive un messaggio di log di uscita
	lb_log.info("exitpoint.")  # Stampa un messaggio di log per indicare il punto di uscita

	# Stampa una riga vuota
	print("")  # Stampa una riga vuota per una migliore leggibilita'

	# Termina il programma
	sys.exit()  # Termina l'esecuzione del programma
# ==============================================================
