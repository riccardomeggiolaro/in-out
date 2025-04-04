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

		self.router.add_api_websocket_route('/{anagrafic}', self.websocket_anagrafic)

	async def handle_select(self, anagrafic: str, record_id: int, websocket: WebSocket, websocket_identifier: str):
		try:
			if anagrafic not in manager_anagrafics:
				return {"error": f"Anagrafic {anagrafic} does not exist"}			
			if websocket not in manager_anagrafics[anagrafic].active_connections:
				return {"error": "WebSocket not registered in active connections"}
			success, locked_record = lock_record(name_table=anagrafic, id_record=record_id, web_socket=websocket_identifier)
			if success is False:
				return {"error": f"Record con id '{record_id}' nella tabella '{anagrafic}' bloccato dall'utente '{locked_record.websocket}'"}
			data = get_data_by_id(anagrafic, record_id)
			return {"type": "select_response", "success": True, "data": data}
		except Exception as e:
			return {"type": "select_response", "success": False, "error": e}
	
	async def handle_deselect(self, anagrafic: str, record_id: int, websocket: WebSocket, websocket_identifier: str):
		try:
			if anagrafic not in manager_anagrafics:
				return {"error": f"Anagrafic {anagrafic} does not exist"}
			if websocket not in manager_anagrafics[anagrafic].active_connections:
				return {"error": "WebSocket not registered in active connections"}
			data = unlock_record_by_attributes(name_table=anagrafic, record_id=record_id, web_socket=websocket_identifier)
			return {
				"type": "deselect_response",
				"success": data,
				"anagrafic": anagrafic,
				"record_id": record_id,
			}
		except Exception as e:
			return {"type": "deselect_response", "success": False, "error": e}
  
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
				if message["type"] == "select":
					response = await self.handle_select(anagrafic, message["id"], websocket, websocket_identifier)
					json_response = json.dumps(jsonable_encoder(response))
					await manager_anagrafics[anagrafic].send_personal_message(json_response, websocket)
				elif message["type"] == "deselect":
					response = await self.handle_deselect(anagrafic, message["id"], websocket, websocket_identifier)
					json_response = json.dumps(jsonable_encoder(response))
					await manager_anagrafics[anagrafic].send_personal_message(json_response, websocket)        
			except Exception as e:
				await manager_anagrafics[anagrafic].send_personal_message('', websocket)
		unlock_all_record_by_websocket(web_socket=websocket_identifier)