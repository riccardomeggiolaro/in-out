from fastapi import APIRouter, WebSocket
from applications.router.anagrafic.material import MaterialRouter
from applications.router.anagrafic.subject import SubjectRouter
from applications.router.anagrafic.vector import VectorRouter
from applications.router.anagrafic.driver import DriverRouter
from applications.router.anagrafic.vehicle import VehicleRouter
from applications.router.anagrafic.reservation import ReservationRouter
from applications.router.anagrafic.manager_anagrafics import manager_anagrafics
import asyncio
import libs.lb_log as lb_log
  
class AnagraficRouter:
	def __init__(self):
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

	async def websocket_anagrafic(self, anagrafic: str, websocket: WebSocket):
		if anagrafic not in manager_anagrafics:
			raise ValueError(f"Anagrafic {anagrafic} is not exist")
		await manager_anagrafics[anagrafic].connect(websocket)
		while websocket in manager_anagrafics[anagrafic].active_connections:
			await asyncio.sleep(5)
			await manager_anagrafics[anagrafic].send_personal_message('', websocket)