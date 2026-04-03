from fastapi import APIRouter
import libs.lb_config as lb_config
import modules.md_rfid.md_rfid as md_rfid
from modules.md_rfid.globals import protocolsClasses
from modules.md_rfid.dto import RfidConfigurationDTO, RfidConnectionDTO

class RfidRouter:
	def __init__(self):
		self.router = APIRouter()

		# Inizializza le istanze dalla configurazione
		rfid_config = lb_config.g_config.get("app_api", {}).get("rfid", {})
		if rfid_config:
			md_rfid.module_rfid.initialize_from_config(rfid_config)

		self.router.add_api_route("/protocols", self.GetProtocols, methods=["GET"])
		self.router.add_api_route("", self.GetAllInstances, methods=["GET"])
		self.router.add_api_route("", self.CreateInstance, methods=["POST"])
		self.router.add_api_route("/{name}", self.GetInstance, methods=["GET"])
		self.router.add_api_route("/{name}", self.DeleteInstance, methods=["DELETE"])
		self.router.add_api_route("/{name}/connection", self.SetConnection, methods=["PATCH"])
		self.router.add_api_route("/{name}/connection", self.DeleteConnection, methods=["DELETE"])

	async def GetProtocols(self):
		"""Restituisce i protocolli RFID disponibili."""
		return list(protocolsClasses.keys())

	async def GetAllInstances(self):
		"""Restituisce tutte le istanze RFID configurate."""
		return md_rfid.module_rfid.get_all_instances()

	async def CreateInstance(self, configuration: RfidConfigurationDTO):
		"""Crea una nuova istanza RFID."""
		return md_rfid.module_rfid.create_instance(configuration)

	async def GetInstance(self, name: str):
		"""Restituisce una singola istanza RFID."""
		return md_rfid.module_rfid.get_instance(name)

	async def DeleteInstance(self, name: str):
		"""Elimina un'istanza RFID."""
		return md_rfid.module_rfid.delete_instance(name)

	async def SetConnection(self, name: str, connection: RfidConnectionDTO):
		"""Aggiorna la connessione seriale di un'istanza."""
		return md_rfid.module_rfid.set_instance_connection(name, connection)

	async def DeleteConnection(self, name: str):
		"""Disconnette la seriale di un'istanza."""
		return md_rfid.module_rfid.delete_instance_connection(name)
