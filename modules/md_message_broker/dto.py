from pydantic import BaseModel, field_validator
from typing import Literal


class MessageBrokerDTO(BaseModel):
	"""
	Configurazione della connessione al broker MQTT.

	La connessione è sempre in TLS con autenticazione tramite certificato client
	(mTLS): i file CA, certificato e chiave vengono caricati a parte e salvati
	nella cartella dei certificati del modulo. Il client ID viene generato
	automaticamente ed è usato anche come topic di pubblicazione.
	"""
	host: str
	port: int = 8883
	qos: Literal[0, 1, 2] = 1
	retain: bool = False
	keepalive: int = 60
	# Se True non verifica che il nome host corrisponda al certificato del broker
	tls_insecure: bool = False
	# Timeout (secondi) per la conferma di consegna (PUBACK/PUBCOMP) da parte del broker
	publish_timeout: int = 30
	# Contenuto del messaggio
	include_images: bool = True
	include_pdf: bool = True
	include_csv: bool = True

	@field_validator("host")
	@classmethod
	def validate_host(cls, v):
		v = (v or "").strip()
		if not v:
			raise ValueError("Host obbligatorio")
		return v

	@field_validator("port")
	@classmethod
	def validate_port(cls, v):
		if not 1 <= v <= 65535:
			raise ValueError("Porta non valida")
		return v
