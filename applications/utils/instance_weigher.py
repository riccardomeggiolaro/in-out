from pydantic import BaseModel
from typing import Optional
from applications.utils.web_socket import ConnectionManager

class InstanceNameDTO(BaseModel):
	name: str

class InstanceNameNodeDTO(InstanceNameDTO):
	node: Optional[str] = None

class NodeConnectionManager:
	def __init__(self):
		self.manager_realtime = ConnectionManager()
		self.manager_diagnostic = ConnectionManager()
		self.manager_execution = ConnectionManager()