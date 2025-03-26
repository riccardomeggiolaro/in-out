from fastapi import APIRouter
from applications.router.anagrafic.material import MaterialRouter

class AnagraficRouter:
	def __init__(self):
		self.router = APIRouter(prefix='/anagrafic')

		material = MaterialRouter()

		self.router.include_router(material.router, prefix='/material', tags=['material'])