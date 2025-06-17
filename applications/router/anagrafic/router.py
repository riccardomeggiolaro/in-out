from fastapi import APIRouter, WebSocket, HTTPException
from fastapi.encoders import jsonable_encoder
from applications.router.anagrafic.material import MaterialRouter
from applications.router.anagrafic.subject import SubjectRouter
from applications.router.anagrafic.vector import VectorRouter
from applications.router.anagrafic.driver import DriverRouter
from applications.router.anagrafic.vehicle import VehicleRouter
from applications.router.anagrafic.reservation import ReservationRouter
from applications.router.anagrafic.manager_anagrafics import manager_anagrafics
import asyncio
from modules.md_database.functions.lock_record import lock_record
from modules.md_database.functions.unlock_record_by_attributes import unlock_record_by_attributes
from modules.md_database.functions.get_data_by_id import get_data_by_id
from modules.md_database.functions.unlock_all_record_by_websocket import unlock_all_record_by_websocket
from modules.md_database.functions.unlock_all_record import unlock_all_record
import json
from applications.middleware.auth import get_user
from applications.utils.utils import just_locked_message
  
class AnagraficRouter:
	def __init__(self):
		unlock_all_record()

		self.router = APIRouter(prefix='/anagrafic')

		subject = SubjectRouter()
		vector = VectorRouter()
		driver = DriverRouter()
		vehicle = VehicleRouter()
		material = MaterialRouter()
		reservation = ReservationRouter()

		self.router.include_router(subject.router, prefix='/subject', tags=['subject'])
		self.router.include_router(vector.router, prefix='/vector', tags=['vector'])
		self.router.include_router(driver.router, prefix='/driver', tags=['driver'])
		self.router.include_router(vehicle.router, prefix='/vehicle', tags=['vehicle'])
		self.router.include_router(material.router, prefix='/material', tags=['material'])
		self.router.include_router(reservation.router, prefix='/reservation', tags=['reservation'])
		self.router.include_router(reservation.panel_siren_router, prefix='', tags=['panel siren'])

		self.router.add_api_websocket_route('/{anagrafic}', self.websocket_anagrafic)

	async def handle_lock(self, table_name: str, idRecord: int, type: str, websocket_identifier: str, user_id: int, idRequest: int):
		try:
			if table_name not in manager_anagrafics:
				return {"action": "lock", "success": False, "anagrafic": table_name, "error": f"Anagrafic {table_name} does not exist", "idRecord": idRecord, "type": type, "idRequest": idRequest}
			success, locked_record, error = lock_record(table_name=table_name, idRecord=idRecord, type=type, websocket_identifier=websocket_identifier, user_id=user_id, weigher_name=None)
			if success is False:
				message = just_locked_message(locked_record.type.name, table_name, locked_record.user.username if locked_record.user else None, locked_record.weigher_name)
				return {"action": "lock", "success": False, "anagrafic": table_name, "error": message, "idRecord": idRecord, "type": type, "idRequest": idRequest}
			data = get_data_by_id(table_name, idRecord)
			return {"action": "lock", "success": True, "anagrafic": table_name, "data": data, "idRecord": idRecord, "type": type, "idRequest": idRequest}
		except Exception as e:
			return {"action": "lock", "success": False, "anagrafic": table_name, "error": str(e), "idRecord": idRecord, "type": type, "idRequest": idRequest}
	
	async def handle_unlock(self, table_name: str, idRecord: int, type: str, websocket_identifier: str, idRequest: int):
		try:
			if table_name not in manager_anagrafics:
				return {"action": "unlock", "success": False, "anagrafic": table_name, "error": f"Anagrafic {table_name} does not exist", "idRecord": idRecord, "type": type, "idRequest": idRequest}
			success = unlock_record_by_attributes(table_name=table_name, idRecord=idRecord, websocket_identifier=websocket_identifier, weigher_name=None)
			return {"action": "unlock", "success": success, "anagrafic": table_name, "data": {}, "idRecord": idRecord, "type": type, "idRequest": idRequest}
		except Exception as e:
			return {"action": "unlock", "success": False, "anagrafic": table_name, "error": e, "idRecord": idRecord, "type": type, "idRequest": idRequest}
  
	def get_user_from_websocket(self, websocket: WebSocket):
		# Extract token from the websocket query parameters or headers
		if not "token" in websocket.query_params:
			raise HTTPException(status_code=401, detail="Token not provided")
		return get_user(websocket.query_params["token"])
  
	async def websocket_anagrafic(self, anagrafic: str, websocket: WebSocket):
		user = self.get_user_from_websocket(websocket)

		if anagrafic not in manager_anagrafics:
			raise ValueError(f"Anagrafic {anagrafic} does not exist")

		await manager_anagrafics[anagrafic].connect(websocket)
		websocket_identifier = f"{websocket.client.host}:{websocket.client.port}"
		import libs.lb_log as lb_log

		while websocket in manager_anagrafics[anagrafic].active_connections:
			try:
				# Aspetta un messaggio dal WebSocket con un timeout
				data = await asyncio.wait_for(websocket.receive_text(), timeout=5)
				message = json.loads(data)

				# Gestisci i messaggi ricevuti
				if message["action"] == "lock":
					response = await self.handle_lock(
						table_name=message["anagrafic"] if "anagrafic" in message else anagrafic,
						idRecord=message["idRecord"],
						type=message["type"],
						idRequest=message["idRequest"],
						websocket_identifier=websocket_identifier,
						user_id=user.id,
					)
					json_response = json.dumps(jsonable_encoder(response))
					await manager_anagrafics[anagrafic].send_personal_message(json_response, websocket)
				elif message["action"] == "unlock":
					response = await self.handle_unlock(
						table_name=message["anagrafic"] if "anagrafic" in message else anagrafic,
						idRecord=message["idRecord"],
						type=message["type"],
						idRequest=message["idRequest"],
						websocket_identifier=websocket_identifier,
					)
					json_response = json.dumps(jsonable_encoder(response))
					await manager_anagrafics[anagrafic].send_personal_message(json_response, websocket)

			except asyncio.TimeoutError:
				# Timeout scaduto, continua ad aspettare nuovi messaggi
				# lb_log.warning(f"Timeout while waiting for message from {websocket_identifier}")
				continue

			except json.JSONDecodeError as e:
				# Messaggio non valido ricevuto
				lb_log.error(f"Invalid JSON received from {websocket_identifier}: {str(e)}")
				await manager_anagrafics[anagrafic].send_personal_message(
					json.dumps({"error": "Invalid message format"}), websocket
				)

			except Exception as e:
				# Gestione di altri errori
				lb_log.error(f"Unexpected error: {str(e)}")
				await manager_anagrafics[anagrafic].send_personal_message(
					json.dumps({"error": "Internal server error"}), websocket
				)

		# Sblocca tutti i record associati al WebSocket quando la connessione termina
		unlock_all_record_by_websocket(websocket_identifier=websocket_identifier)