from fastapi import APIRouter
from applications.router.weigher.command_weigher import CommandWeigherRouter
from applications.router.weigher.cams import CamsRouter
from applications.router.weigher.rele import ReleRouter

class WeigherRouter:
	def __init__(self):
		self.router = APIRouter()

		command_weigher = CommandWeigherRouter()

		cams = CamsRouter()
  
		rele = ReleRouter()

		self.router.include_router(command_weigher.router_action_weigher, prefix='/command-weigher', tags=['actions weigher'])
	
		self.router.include_router(cams.router_cams, prefix='/cams', tags=['cams'])		

		self.router.include_router(rele.router_rele, prefix='/rele', tags=['rele'])
 
		self.router.include_router(command_weigher.router_data, prefix='/data', tags=['data'])
 
		self.router.include_router(command_weigher.router_config_weigher, prefix='/config-weigher', tags=['config weigher'])