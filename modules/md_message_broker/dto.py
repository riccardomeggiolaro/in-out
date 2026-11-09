from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, Literal


class MessageBrokerDTO(BaseModel):
	"""Configurazione della connessione al broker MQTT."""
	host: str
	port: Optional[int] = None
	username: Optional[str] = None
	password: Optional[str] = None
	client_id: Optional[str] = None
	# Topic su cui pubblicare. Segnaposto disponibili: {instance_name}, {weigher_name}, {event_type}
	topic: str = "in-out/weighings"
	qos: Literal[0, 1, 2] = 1
	retain: bool = False
	keepalive: int = 60
	tls: bool = False
	ca_cert: Optional[str] = None
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
			raise ValueError("host is required")
		return v

	@model_validator(mode="after")
	def set_default_port(self):
		if self.port is None:
			self.port = 8883 if self.tls else 1883
		return self
