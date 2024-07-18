from pydantic import BaseModel
import inspect

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
		if num_params == 1:
			return True
	return False

# controlla se la callback è eseguibile, se si la esegue
def callCallback(callback):
    if callable(callback):
        callback()