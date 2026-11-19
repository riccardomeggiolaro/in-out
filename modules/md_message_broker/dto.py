import re

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
	# Terminale SSH dal pannello del broker (attraverso la connessione MQTT, vedi remote_ssh.py)
	remote_ssh: bool = True
	# Utente con cui si apre il terminale (la chiave del broker va nel suo authorized_keys).
	# Su Windows "root" vuol dire: l'utente con cui gira l'in-out.
	ssh_user: str = "root"
	# Porta del sshd locale
	ssh_port: int = 22

	@field_validator("host")
	@classmethod
	def validate_host(cls, v):
		v = (v or "").strip()
		if not v:
			raise ValueError("Host obbligatorio")
		return v

	@field_validator("ssh_user")
	@classmethod
	def validate_ssh_user(cls, v):
		v = (v or "").strip() or "root"
		# Linux: nomi POSIX; Windows: anche maiuscole, spazi e DOMINIO\utente
		if not re.match(r"^[A-Za-z0-9_][A-Za-z0-9_. \\@-]{0,63}$", v):
			raise ValueError("Utente SSH non valido")
		return v

	@field_validator("port", "enroll_port", "ssh_port")
	@classmethod
	def validate_port(cls, v):
		if not 1 <= v <= 65535:
			raise ValueError("Porta non valida")
		return v
