from fastapi import APIRouter
from applications.router.weigher.command_weigher import CommandWeigher

class WeigherRouter:
	def __init__(self):
		self.router = APIRouter()

		router_command_weigher = CommandWeigher()

		self.router.include_router(router_command_weigher.router_action_weigher, prefix='/command_weigher', tags=['actions weigher'])
	
		self.router.include_router(router_command_weigher.router_config_weigher, prefix='/config_weigher', tags=['config weigher'])