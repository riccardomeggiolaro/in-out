from fastapi import APIRouter
from applications.router.weigher.command_weigher import CommandWeigherRouter
from applications.router.weigher.cams import CamsRouter
from applications.router.weigher.events import EventsRouter

class WeigherRouter:
	def __init__(self):
		self.router = APIRouter()

		command_weigher = CommandWeigherRouter()

		cams = CamsRouter()
  
		events = EventsRouter()

		self.router.include_router(command_weigher.router_action_weigher, prefix='/command_weigher', tags=['actions weigher'])
	
		self.router.include_router(cams.router_cams, prefix='/cams', tags=['cams'])		

		self.router.include_router(events.router_events, prefix='/events', tags=['events'])
 
		self.router.include_router(command_weigher.router_data_in_execution, prefix='/data_in_execution', tags=['data in execution'])
 
		self.router.include_router(command_weigher.router_config_weigher, prefix='/config_weigher', tags=['config weigher'])