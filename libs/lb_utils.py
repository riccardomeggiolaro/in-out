from pydantic import BaseModel
import inspect
import signal
import libs.lb_config as lb_config
import libs.lb_log as lb_log
import threading
import datetime

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

def createThread(function, args=(), stop=None):
	if callable(function):
		return threading.Thread(target=function, args=args, daemon=True)

def startThread(thread):
	if not thread.is_alive():
		thread.start()
		
def closeThread(thread, path=None):
	if thread.is_alive():
		if path:
			path.stop()
	if thread.is_alive():
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

def sum_number(num1, num2):
	# Funzione per determinare se un numero ha decimali
	def convert(numero):
		if '.' in numero or ',' in numero:
			return float(numero)  # Se ci sono decimali, lo converte in float
		else:
			return int(numero)  # Se non ci sono decimali, lo converte in int

	# Converto i numeri
	num1 = convert(num1)
	num2 = convert(num2)
	
	# Ritorno la somma dei numeri
	return num1 + num2

def is_number(s):
	try:
		float(s)  # Converte sia interi che numeri decimali
		return True
	except ValueError:
		return False
	
def has_values_besides_id(dictionary):
	"""
	Verifica se un dizionario contiene almeno un campo con un valore (diverso da None, '', [], {}, 0)
	oltre al campo 'id'.
	
	Restituisce True se c'è almeno un campo con valore significativo, False altrimenti.
	"""
	
	for key, value in dictionary.items():
		# Salta il campo 'id'
		if key == 'id':
			continue
		
		# Controlla se il valore è significativo (non vuoto/nullo)
		if value is not None and value != '' and value != [] and value != {} and value != 0:
			return True
	
	# Se arrivi qui, non ci sono campi con valori significativi oltre 'id'
	return False

def check_values(obj):
    """
    Funzione che verifica se un oggetto (dizionario o DTO) ha almeno un valore diverso da "" o None,
    considerando anche sotto-dizionari o sotto-DTO annidati.
    """
    if isinstance(obj, dict):  # Se l'oggetto è un dizionario (potrebbe essere un DTO)
        for key, value in obj.items():
            if isinstance(value, dict):  # Se il valore è un altro dizionario (sotto-dizionario)
                if check_values(value):  # Chiamata ricorsiva per esplorare il sotto-dizionario
                    return True
            elif isinstance(value, object):  # Se il valore è un oggetto (potrebbe essere un DTO)
                return value
                if check_values(value.dict()):  # Se è un oggetto, controlla i suoi attributi come un dizionario
                    return True
            elif value != "" and value is not None:  # Se il valore non è "" o None
                return True
    return False

def current_month():
    return datetime.datetime.now().strftime("%B").lower()