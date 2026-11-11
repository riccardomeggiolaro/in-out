from typing import Optional
from pydantic import BaseModel, field_validator


class MessageBrokerDTO(BaseModel):
	"""
	Configurazione della connessione al broker MQTT.

	La connessione è sempre in TLS. L'autenticazione può avvenire con:
	- username/password (es. EMQX Serverless, HiveMQ Cloud, ...)
	- certificato client (mTLS)
	- entrambi.
	I file TLS (CA facoltativo, certificato e chiave client facoltativi) vengono
	caricati a parte e salvati nella cartella dei certificati del modulo; senza CA
	si usano i certificati di sistema. Il client ID viene generato
	automaticamente ed è usato anche come topic di pubblicazione.
	"""
	host: str
	port: int = 8883
	username: Optional[str] = None
	password: Optional[str] = None
	keepalive: int = 60
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

	@field_validator("username")
	@classmethod
	def validate_username(cls, v):
		v = (v or "").strip()
		return v or None

	@field_validator("port")
	@classmethod
	def validate_port(cls, v):
		if not 1 <= v <= 65535:
			raise ValueError("Porta non valida")
		return v
