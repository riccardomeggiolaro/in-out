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
import libs.lb_log as lb_log
from modules.md_database.functions.lock_record import lock_record
from modules.md_database.functions.unlock_record_by_attributes import unlock_record_by_attributes
from modules.md_database.functions.get_data_by_id import get_data_by_id
from modules.md_database.functions.unlock_all_record_by_websocket import unlock_all_record_by_websocket
from modules.md_database.functions.unlock_all_record import unlock_all_record
import json
  
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

	async def handle_lock(self, table_name: str, idRecord: int, type: str, websocket_identifier: str, idRequest: int):
		try:
			if table_name not in manager_anagrafics:
				return {"action": "lock", "success": False, "anagrafic": table_name, "error": f"Anagrafic {table_name} does not exist", "idRecord": idRecord, "type": type, "idRequest": idRequest}
			success, locked_record = lock_record(table_name=table_name, idRecord=idRecord, type=type, websocket_identifier=websocket_identifier)
			if success is False:
				return {"action": "lock", "success": False, "anagrafic": table_name, "error": f"Record con id '{idRecord}' nella tabella '{table_name}' bloccato dall'utente '{locked_record.websocket_identifier}", "idRecord": idRecord, "type": type, "idRequest": idRequest}
			data = get_data_by_id(table_name, idRecord)
			return {"action": "lock", "success": True, "anagrafic": table_name, "data": data, "idRecord": idRecord, "type": type, "idRequest": idRequest}
		except Exception as e:
			return {"action": "lock", "success": False, "anagrafic": table_name, "error": str(e), "idRecord": idRecord, "type": type, "idRequest": idRequest}
	
	async def handle_unlock(self, table_name: str, idRecord: int, type: str, websocket_identifier: str, idRequest: int):
		try:
			if table_name not in manager_anagrafics:
				return {"action": "unlock", "success": False, "anagrafic": table_name, "error": f"Anagrafic {table_name} does not exist", "idRecord": idRecord, "type": type, "idRequest": idRequest}
			success = unlock_record_by_attributes(table_name=table_name, idRecord=idRecord, websocket_identifier=websocket_identifier)
			return {"action": "unlock", "success": success, "anagrafic": table_name, "data": {}, "idRecord": idRecord, "type": type, "idRequest": idRequest}
		except Exception as e:
			return {"action": "unlock", "success": False, "anagrafic": table_name, "error": e, "idRecord": idRecord, "type": type, "idRequest": idRequest}
  
	async def websocket_anagrafic(self, anagrafic: str, websocket: WebSocket):
		if anagrafic not in manager_anagrafics:
			raise ValueError(f"Anagrafic {anagrafic} is not exist")
		await manager_anagrafics[anagrafic].connect(websocket)
		websocket_identifier = f"{websocket.client.host}:{websocket.client.port}"
		while websocket in manager_anagrafics[anagrafic].active_connections:
			try:
				data = await asyncio.wait_for(websocket.receive_text(), timeout=5)
				message = json.loads(data)
				# Handle different types of messages
				if message["action"] == "lock":
					response = await self.handle_lock(
         				table_name=message["anagrafic"] if "anagrafic" in message else anagrafic, 
             			idRecord=message["idRecord"], 
                		type=message["type"],
						idRequest=message["idRequest"],
                  		websocket_identifier=websocket_identifier
                    )
					json_response = json.dumps(jsonable_encoder(response))
					await manager_anagrafics[anagrafic].send_personal_message(json_response, websocket)
				elif message["action"] == "unlock":
					response = await self.handle_unlock(
         				table_name=message["anagrafic"] if "anagrafic" in message else anagrafic, 
             			idRecord=message["idRecord"], 
                		type=message["type"], 
						idRequest=message["idRequest"],
                  		websocket_identifier=websocket_identifier
                    )
					json_response = json.dumps(jsonable_encoder(response))
					await manager_anagrafics[anagrafic].send_personal_message(json_response, websocket)        
			except Exception as e:
				await manager_anagrafics[anagrafic].send_personal_message('', websocket)
		unlock_all_record_by_websocket(websocket_identifier=websocket_identifier)