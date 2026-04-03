from fastapi import APIRouter
from modules.md_rfid.globals import protocolsClasses

class RfidRouter:
	def __init__(self):
		self.router = APIRouter()
		self.router.add_api_route("/protocols", self.GetProtocols, methods=["GET"])

	async def GetProtocols(self):
		"""Restituisce i protocolli RFID disponibili."""
		return list(protocolsClasses.keys())
