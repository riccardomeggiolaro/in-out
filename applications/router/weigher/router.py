from fastapi import APIRouter
from applications.router.weigher.config_weigher import ConfigWeigher

class WeigherRouter:
	def __init__(self):
		self.router = APIRouter()

		command_weigher = ConfigWeigher()

		self.router.include_router(command_weigher.router_action_weigher, prefix='/command-weigher', tags=['actions weigher'])
	
		self.router.include_router(command_weigher.router_data, prefix='/data', tags=['data'])
 
		self.router.include_router(command_weigher.router_config_weigher, prefix='/config-weigher', tags=['config weigher'])
