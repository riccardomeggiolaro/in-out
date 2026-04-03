from pydantic import BaseModel, validator
from typing import Optional
from modules.md_rfid.globals import protocolsClasses

class RfidConnectionDTO(BaseModel):
	serial_port_name: str
	baudrate: int = 9600
	timeout: int = 1

class RfidSetupDTO(BaseModel):
	pass

class RfidConfigurationDTO(BaseModel):
	name: str
	protocol: str
	connection: Optional[RfidConnectionDTO] = None
	setup: Optional[RfidSetupDTO] = None

	@validator("name", pre=True, always=True)
	def check_name_no_spaces(cls, v):
		if v and " " in v:
			raise ValueError("Il nome non può contenere spazi")
		return v

	@validator("protocol", pre=True, always=True)
	def check_protocol(cls, v):
		if v not in protocolsClasses:
			raise ValueError(f"Protocollo '{v}' non disponibile. Disponibili: {list(protocolsClasses.keys())}")
		return v
