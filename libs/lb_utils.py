from pydantic import BaseModel
import inspect
import signal
import libs.lb_config as lb_config
import libs.lb_log as lb_log
import threading

# Definizione di CustomBaseModel che estende BaseModel di Pydantic.
class CustomBaseModel(BaseModel):
	# Configurazione delle opzioni del modello.
    class Config:
        # Disabilita la protezione degli spazi dei nomi predefiniti di Pydantic,
        # permettendo l'uso di nomi di campi personalizzati senza avvisi di conflitto.
        protected_namespaces = ()

        # I seguenti prefissi e attributi non possono essere utilizzati come nomi di campi
        # a meno che non si disabiliti la protezione degli spazi dei nomi:
        # - model_: utilizzato internamente da Pydantic
        # - __fields__: informazioni sui campi del modello
        # - __config__: configurazione del modello
        # - __validators__: validatori del modello
        # - __pre_root_validators__: validatori eseguiti prima della validazione del modello radice
        # - __post_root_validators__: validatori eseguiti dopo la validazione del modello radice
        
# controlla se il formato della callback è giusto, ovvero se è richiamabile e se ha 1 solo parametro
def checkCallbackFormat(callback):
	if callable(callback):
		signature = inspect.signature(callback)
		num_params = len(signature.parameters)
		if num_params == 3:
			return True
	return False

# controlla se la callback è eseguibile, se si la esegue
def callCallback(callback):
    if callable(callback):
        callback()

def createThread(function, stop=None):
    if callable(function):
        return threading.Thread(target=function, daemon=True)

def startThread(thread):
    if not thread.is_alive():
        thread.start()
        
def closeThread(thread, path=None):
    if thread.is_alive():
        if path:
            path.stop()
    thread.join()

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