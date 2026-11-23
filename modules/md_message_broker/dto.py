import ipaddress
import re
from typing import Optional

from pydantic import BaseModel, field_validator

# Porte usate quando non sono indicate: un broker con dominio pubblico ha la porta
# unica 443 (MQTT e registrazione smistati per ALPN); in rete locale (IP o nome
# senza dominio) il broker usa le porte dedicate.
DOMAIN_PORT = 443
LAN_MQTT_PORT = 8883
LAN_ENROLL_PORT = 8884


def is_domain(host: str) -> bool:
	"""True per un nome di dominio (es. mqtt.esempio.it), False per IP o nomi locali."""
	host = (host or "").strip().strip("[]")
	try:
		ipaddress.ip_address(host)
		return False
	except ValueError:
		pass
	return "." in host and not host.lower().endswith((".local", ".lan", ".localdomain"))


class MessageBrokerDTO(BaseModel):
	"""
	Configurazione della connessione al broker MQTT.

	La connessione è sempre in TLS con certificato client (mTLS). Il certificato
	non si carica a mano: l'in-out lo ottiene da solo dal servizio di registrazione
	del broker (`registration_port`) e lo rinnova prima della scadenza. Il client ID viene
	generato automaticamente ed è usato anche come CN del certificato e come topic.
	"""
	host: str
	# Porte facoltative: vuote = 443 con un dominio, 8883/8884 con un IP (vedi mqtt_port)
	port: Optional[int] = None
	# Porta HTTPS del servizio di registrazione automatica del broker
	enroll_port: Optional[int] = None
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
		if v is not None and not 1 <= v <= 65535:
			raise ValueError("Porta non valida")
		return v

	@property
	def mqtt_port(self) -> int:
		"""Porta MQTT effettiva."""
		if self.port:
			return self.port
		return DOMAIN_PORT if is_domain(self.host) else LAN_MQTT_PORT

	@property
	def registration_port(self) -> int:
		"""Porta effettiva del servizio di registrazione."""
		if self.enroll_port:
			return self.enroll_port
		return DOMAIN_PORT if is_domain(self.host) else LAN_ENROLL_PORT
