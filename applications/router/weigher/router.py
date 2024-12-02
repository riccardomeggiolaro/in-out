from fastapi import APIRouter
from applications.router.weigher.weigher import Weigher
from applications.router.weigher.historic_data import HistoricData
from applications.router.weigher.data_in_execution import DataInExecution

class WeigherRouter:
	def __init__(self):
		self.router = APIRouter()

		router_weigher = Weigher()
		router_data_in_execution = DataInExecution()
		router_historic_data = HistoricData()

		self.router.include_router(router_weigher.router_action_weigher, prefix='/actions_weigher', tags=['actions weigher'])
	
		self.router.include_router(router_weigher.router_config_weigher, prefix='/config_weigher', tags=['config weigher'])
 
		self.router.include_router(router_data_in_execution.router, prefix='/data_in_execution', tags=['data in execution'])

		self.router.include_router(router_historic_data.router, prefix='/historic_data', tags=['historic data'])