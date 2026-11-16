from pydantic import BaseModel, field_validator


class MessageBrokerDTO(BaseModel):
	"""
	Configurazione della connessione al broker MQTT.

	La connessione è sempre in TLS con certificato client (mTLS). Il certificato
	non si carica a mano: l'in-out lo ottiene da solo dal servizio di registrazione
	del broker (`enroll_port`) e lo rinnova prima della scadenza. Il client ID viene
	generato automaticamente ed è usato anche come CN del certificato e come topic.
	"""
	host: str
	port: int = 8883
	# Porta HTTPS del servizio di registrazione automatica del broker
	enroll_port: int = 8884
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

	@field_validator("port", "enroll_port")
	@classmethod
	def validate_port(cls, v):
		if not 1 <= v <= 65535:
			raise ValueError("Porta non valida")
		return v
