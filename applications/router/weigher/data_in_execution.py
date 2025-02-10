from fastapi import APIRouter, Depends
import libs.lb_config as lb_config
import modules.md_weigher.md_weigher as md_weigher
from applications.utils.utils_weigher import InstanceNameWeigherDTO, get_query_params_name_node
from applications.router.weigher.dto import DataDTO, DataInExecutionDTO
from applications.router.weigher.types import DataInExecution as DataInExecutionType, Data
from applications.router.weigher.config_weigher import ConfigWeigher
import asyncio

class DataInExecutionRouter(ConfigWeigher):
	def __init__(self):
		super().__init__()
		
		self.router_data_in_execution = APIRouter()
	
		self.router_data_in_execution.add_api_route('/data_in_execution', self.GetDataInExecution, methods=['GET'])
		self.router_data_in_execution.add_api_route('/data_in_execution', self.SetDataInExecution, methods=['PATCH'])
		self.router_data_in_execution.add_api_route('/data_in_execution', self.DeleteDataInExecution, methods=['DELETE'])
 
	async def GetDataInExecution(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		return self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)

	async def SetDataInExecution(self, data_dto: DataDTO, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		self.setDataInExecution(instance_name=instance.instance_name, weigher_name=instance.weigher_name, source=data_dto.data_in_execution)
		if data_dto.id_selected.id is not None:
			self.setIdSelected(instance_name=instance.instance_name, weigher_name=instance.weigher_name, new_id=data_dto.id_selected.id)
		return self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)

	async def DeleteDataInExecution(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		self.deleteDataInExecution(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
		self.deleteIdSelected(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
		return self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)