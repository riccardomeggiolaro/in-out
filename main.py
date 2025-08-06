# -*- coding: utf-8 -*-

# ==============================================================
#						- LOADER -							  =
# ==============================================================

# ==== LIBRERIE DA IMPORTARE ===================================
import time
import sys
import signal
import os
import tkinter as tk
from tkinter import ttk, messagebox
import modules.md_weigher.md_weigher as md_weigher
# import modules.md_rfid as md_rfid
from libs.lb_utils import GracefulKiller, createThread, startThread, closeThread
import libs.lb_config as lb_config  # Importa il modulo per la configurazione
import libs.lb_log as lb_log  # Importa il modulo per il logger
import libs.lb_singleton as lb_singleton  # Importa il singleton manager
# ==============================================================

def check_port_permission():
	"""Controlla se possiamo usare la porta 80"""
	try:
		# Leggi la configurazione per vedere quale porta usa
		lb_config.init()
		
		# Cerca la porta nella configurazione
		port = 80  # Default
		if hasattr(lb_config, 'g_config') and isinstance(lb_config.g_config, dict):
			# Cerca la porta nell'API config
			if 'app_api' in lb_config.g_config and 'port' in lb_config.g_config['app_api']:
				port = lb_config.g_config['app_api']['port']
		
		# Se non è porta privilegiata, non c'è problema
		if port >= 1024:
			return True
		
		# Se siamo root, non c'è problema
		if os.name != 'nt' and os.geteuid() == 0:
			return True
		
		# Su Windows, proviamo direttamente
		if os.name == 'nt':
			return True
		
		# Su Linux, controlla capabilities
		import subprocess
		try:
			# Controlla se abbiamo capabilities
			result = subprocess.run(['getcap', sys.argv[0]], 
								  capture_output=True, text=True, timeout=5)
			if 'cap_net_bind_service' in result.stdout:
				return True
		except:
			pass
		
		# Nessun privilegio trovato per porta privilegiata
		return False
		
	except Exception as e:
		print(f"Errore nel controllo privilegi: {e}")
		return True  # In caso di errore, lascia provare

def show_permission_error():
	"""Mostra finestra di errore per mancanza privilegi"""
	try:
		root = tk.Tk()
		root.title("BARON - Errore Privilegi")
		root.geometry("450x250")
		root.resizable(False, False)
		
		# Centra la finestra
		root.update_idletasks()
		x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
		y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
		root.geometry(f"+{x}+{y}")
		
		# Frame principale
		main_frame = ttk.Frame(root, padding="20")
		main_frame.pack(fill=tk.BOTH, expand=True)
		
		# Icona di errore (emoji)
		error_label = ttk.Label(main_frame, text="⚠️", font=('Arial', 32))
		error_label.pack(pady=(0, 10))
		
		# Titolo errore
		title_label = ttk.Label(
			main_frame, 
			text="Errore di Permessi",
			font=('Arial', 14, 'bold'),
			foreground='red'
		)
		title_label.pack(pady=(0, 10))
		
		# Messaggio
		message_label = ttk.Label(
			main_frame,
			text="Il programma non può avviarsi a causa di\nproblemi con i permessi o la porta configurata.",
			font=('Arial', 11),
			justify=tk.CENTER
		)
		message_label.pack(pady=(0, 15))
		
		# Separatore
		separator = ttk.Separator(main_frame, orient='horizontal')
		separator.pack(fill=tk.X, pady=(0, 15))
		
		# Pulsante OK
		ok_button = ttk.Button(
			main_frame,
			text="OK - Chiudi",
			command=root.destroy
		)
		ok_button.pack()
		
		# Forza focus sulla finestra
		root.lift()
		root.attributes('-topmost', True)
		root.after(100, lambda: root.attributes('-topmost', False))
		root.focus_force()
		
		# Avvia il loop
		root.mainloop()
		
	except Exception as e:
		print(f"Errore nella creazione finestra errore: {e}")
		# Fallback su console
		print("=" * 50)
		print("⚠️  ERRORE: PROBLEMA CON PERMESSI")
		print("=" * 50)

def signal_handler(signum, frame):
	"""Gestisce i segnali di terminazione (Ctrl+C)"""
	print(f"\n🛑 Ricevuto segnale {signum} - shutdown immediato...")
	
	# Ferma immediatamente tutti i loop
	lb_config.g_enabled = False
	
	# Chiudi immediatamente l'interfaccia desktop senza aspettare
	try:
		import modules.md_desktop_interface.md_desktop_interface as md_desktop_interface
		if hasattr(md_desktop_interface, 'desktop_interface') and md_desktop_interface.desktop_interface:
			print("🖥️  Chiudendo interfaccia desktop...")
			md_desktop_interface.desktop_interface.enabled = False
			# Forza chiusura finestra se esiste
			if md_desktop_interface.desktop_interface.window:
				try:
					md_desktop_interface.desktop_interface.window.quit()
					md_desktop_interface.desktop_interface.window.destroy()
				except:
					pass
	except Exception as e:
		print(f"Errore nella chiusura interfaccia: {e}")
	
	# Pulizia singleton
	try:
		lb_singleton.cleanup_singleton()
	except:
		pass
	
	print("✅ Terminazione completata")
	
	# Exit forzato senza aspettare thread
	import os
	os._exit(0)  # Termina immediatamente senza cleanup thread

def show_desktop_interface():
	"""Callback per mostrare l'interfaccia desktop"""
	try:
		# Ottieni l'istanza del modulo desktop interface
		import modules.md_desktop_interface.md_desktop_interface as md_desktop_interface
		if hasattr(md_desktop_interface, 'desktop_interface') and md_desktop_interface.desktop_interface:
			# Log dello stato attuale per debug
			thread_status = md_desktop_interface.desktop_interface.getThreadsStatus()
			lb_log.info(f"Stato thread prima del comando: {thread_status}")
			
			# Mostra l'interfaccia
			md_desktop_interface.desktop_interface.show_interface()
			lb_log.info("Comando ricevuto: mostra interfaccia desktop")
			
			# Log dello stato dopo il comando
			thread_status_after = md_desktop_interface.desktop_interface.getThreadsStatus()
			lb_log.info(f"Stato thread dopo il comando: {thread_status_after}")
		else:
			lb_log.warning("Modulo desktop interface non disponibile")
	except Exception as e:
		lb_log.error(f"Errore nel mostrare interfaccia desktop: {e}")

# ==== MAINPRGLOOP =============================================
# Configura globale e lo stato del programma.
# Carica moduli esterni e avvia i thread corrispondenti.
def mainprg():
	# Imposta il tempo di attesa tra aggiornamenti (ridotto per risposta più veloce)
	secwait = 0.1  # Cambiato da 0.5 a 0.1 per controlli più frequenti

	# Carica thread per la configurazione in background.
	thr_config = createThread(lb_config.start)

	# Carica thread per il logger in background.
	thr_logger = createThread(lb_log.start)

	import modules.md_database.md_database as md_database
	import modules.md_tunnel_connections.md_tunnel_connections as md_tunnel_connections
	import modules.md_desktop_interface.md_desktop_interface as md_desktop_interface  # NUOVO MODULO
	import applications.app_api as app_api

	APPS = [app_api]

	# AGGIUNTO IL MODULO DESKTOP INTERFACE
	MODULES = [md_weigher, md_tunnel_connections, md_desktop_interface]

	# Carica thread per i moduli esterni.
	modules_thr = {}
	lb_log.info("loading modules...")
	for modulepath in MODULES:
		# Estrae informazioni sul modulo.
		name_module = modulepath.name_module
		lb_log.info("... " + name_module)
		# Inizializza il modulo.
		modulepath.init()  # Inizializzazione del modulo
		# Crea e avvia il thread del modulo.
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

	# Loop principale con controlli di terminazione più frequenti
	while lb_config.g_enabled:
		try:
			# === THREAD Livello 0:
			if not thr_config.is_alive():
				try:
					startThread(thr_config)
				except RuntimeError:
					# Thread già avviato, ricrealo
					thr_config = createThread(lb_config.start)
					startThread(thr_config)
			
			if not thr_logger.is_alive():
				try:
					startThread(thr_logger)
				except RuntimeError:
					# Thread già avviato, ricrealo
					thr_logger = createThread(lb_log.start)
					startThread(thr_logger)

			# === THREAD Livello 1: MODULES
			for module_name in modules_thr.keys():  # Per ogni modulo
				if not lb_config.g_enabled:  # Check di terminazione più frequente
					break
				thread_info = modules_thr[module_name]
				if not thread_info["thread"].is_alive():
					try:
						startThread(thread_info["thread"])
					except RuntimeError:
						# Thread già morto, ricrealo
						new_thread = createThread(thread_info["module"].start)
						modules_thr[module_name]["thread"] = new_thread
						startThread(new_thread)

			# === THREAD Livello 3: APPLICATIONS
			for appname in app_thr.keys():  # Per ogni applicazione
				if not lb_config.g_enabled:  # Check di terminazione più frequente
					break
				thread_info = app_thr[appname]
				if not thread_info["thread"].is_alive():
					try:
						startThread(thread_info["thread"])
					except RuntimeError:
						# Thread già morto, ricrealo
						new_thread = createThread(thread_info["application"].start)
						app_thr[appname]["thread"] = new_thread
						startThread(new_thread)
			
			# Attesa più breve per risposta più veloce
			time.sleep(secwait)
			
		except KeyboardInterrupt:
			# Gestione diretta di Ctrl+C nel loop
			lb_config.g_enabled = False
			break
		except Exception as e:
			lb_log.error(f"Errore nel loop principale: {e}")
			break

	# Chiusura rapida dei thread
	print("🔄 Chiudendo thread...")
	lb_log.info("ending threads:")
	
	# Timeout molto breve per la chiusura dei thread
	shutdown_timeout = 1  # 1 secondo massimo per thread

	# Chiusura moduli con timeout
	for module_name in modules_thr.keys():
		try:
			print(f"  🔹 Chiudendo {module_name}...")
			thread_info = modules_thr[module_name]
			# Non usare closeThread, ferma direttamente
			if hasattr(thread_info["module"], 'enabled'):
				thread_info["module"].enabled = False
			# Aspetta poco tempo
			if thread_info["thread"].is_alive():
				thread_info["thread"].join(timeout=shutdown_timeout)
		except Exception as e:
			print(f"  ❌ Errore chiudendo {module_name}: {e}")

	# Chiusura applicazioni con timeout
	for appname in app_thr.keys():
		try:
			print(f"  🔹 Chiudendo {appname}...")
			thread_info = app_thr[appname]
			if hasattr(thread_info["application"], 'enabled'):
				thread_info["application"].enabled = False
			if thread_info["thread"].is_alive():
				thread_info["thread"].join(timeout=shutdown_timeout)
		except Exception as e:
			print(f"  ❌ Errore chiudendo {appname}: {e}")

	# Chiusura thread sistema con timeout
	for name, thread in [("configuration", thr_config), ("logger", thr_logger)]:
		try:
			if thread.is_alive():
				print(f"  🔹 Chiudendo {name}...")
				thread.join(timeout=shutdown_timeout)
		except Exception as e:
			print(f"  ❌ Errore chiudendo {name}: {e}")
	
	# Pulizia singleton
	try:
		lb_singleton.cleanup_singleton()
	except:
		pass
	
	print("✅ Chiusura completata")
# ==============================================================

# ==== AVVIO PROGRAMMA PRINCIPALE ========================
# Funzione principale del programma.
# Questa funzione gestisce l'avvio e l'esecuzione del programma principale,
# inizializzando i moduli necessari, controllando la configurazione dell'applicazione
# e avviando il ciclo principale di esecuzione (mainprg).
if __name__ == "__main__":
	# Inizializza il singleton manager
	app_name = "BARON"  # Puoi personalizzare il nome
	lb_singleton.init_singleton(app_name)
	
	# Controlla se un'altra istanza è già in esecuzione
	if lb_singleton.is_already_running():
		print(f"Un'istanza di {app_name} è già in esecuzione.")
		print("Tentativo di riaprire l'interfaccia desktop...")
		
		# Prova a notificare l'istanza esistente
		if lb_singleton.notify_existing_instance():
			print("Interfaccia desktop riaperta con successo!")
		else:
			print("Impossibile comunicare con l'istanza esistente.")
		
		sys.exit(0)
	
	# CONTROLLA PRIVILEGI PRIMA DI AVVIARE TUTTO
	if not check_port_permission():
		print("❌ Privilegi insufficienti per la porta configurata")
		show_permission_error()
		sys.exit(1)
	
	# Siamo la prima istanza e abbiamo i privilegi - procedi normalmente
	print(f"Avvio {app_name}...")
	
	# Crea un'istanza della classe GracefulKiller (non definita nel codice fornito)
	killer = GracefulKiller()  # Inizializza l'oggetto per la gestione della terminazione sicura

	# Inizializza il modulo lb_config e imposta la variabile globale g_workpath
	lb_config.init()  # Inizializza il modulo di configurazione

	# Inizializza il modulo lb_log e scrive un messaggio di log
	lb_log.init()  # Inizializza il modulo di logger
	lb_log.info("====================== BARON " + lb_config.g_name + " rel. " + lb_config.g_vers +" =======================")  # Stampa un messaggio di log con la versione

	# Configura gestione segnali per shutdown graceful
	signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
	signal.signal(signal.SIGTERM, signal_handler)  # Terminazione

	# Avvia come istanza principale e imposta il callback per mostrare l'interfaccia
	lb_singleton.start_as_primary_instance(show_desktop_interface)

	try:
		# Controlla se l'applicazione e' abilitata e chiama la funzione mainprg se lo e'
		if lb_config.g_enabled:  # Se l'applicazione e' abilitata
			mainprg()  # Avvia il programma principale
	except PermissionError as e:
		# Cattura errori di permessi durante l'esecuzione
		lb_log.error(f"Errore di permessi durante l'esecuzione: {e}")
		print("❌ Errore di permessi rilevato durante l'esecuzione")
		show_permission_error()
		sys.exit(1)
	except OSError as e:
		# Cattura errori di bind sulla porta
		if "Permission denied" in str(e) or "Address already in use" in str(e):
			lb_log.error(f"Errore porta: {e}")
			print("❌ Errore nell'utilizzo della porta")
			show_permission_error()
			sys.exit(1)
		else:
			raise  # Re-lancia altri errori OSError
	except Exception as e:
		lb_log.error(f"Errore inaspettato: {e}")
		raise

	lb_log.info("exitpoint.")
	print("")
	sys.exit()  # Termina l'esecuzione del programma
# ==============================================================