from fastapi import APIRouter, Depends
import libs.lb_config as lb_config
import modules.md_weigher.md_weigher as md_weigher
from applications.utils.utils_weigher import InstanceNameWeigherDTO, get_query_params_name_node
from applications.router.weigher.dto import DataDTO, DataInExecutionDTO
from applications.router.weigher.types import DataInExecution as DataInExecutionType, Data
from applications.router.weigher.config_weigher import ConfigWeigher
import asyncio
from libs.lb_utils import check_values
from libs.lb_database import get_data_by_id

class DataRouter(ConfigWeigher):
	def __init__(self):
		super().__init__()
		
		self.router_data = APIRouter()
	
		self.router_data.add_api_route('', self.GetDataInExecution, methods=['GET'])
		self.router_data.add_api_route('', self.SetData, methods=['PATCH'])
		self.router_data.add_api_route('', self.DeleteData, methods=['DELETE'])
 
	async def GetDataInExecution(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		return self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)

	async def SetData(self, data_dto: DataDTO, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		if data_dto.id_selected.id:
			await self.DeleteData(instance=instance)
			if data_dto.id_selected.id != -1:
				weighing = get_data_by_id("reservation", data_dto.id_selected.id)
				data_in_execution = DataInExecutionType(**{
					"vehicle": {
						"id": weighing["vehicle"]["id"] if weighing["vehicle"] else None,
						"name": weighing["vehicle"]["name"] if weighing["vehicle"] else None,
						"plate": weighing["vehicle"]["plate"] if weighing["vehicle"] else None
					},
					"typeSocialReason": weighing["typeSocialReason"],
					"social_reason": {
						"id": weighing["social_reason"]["id"] if weighing["social_reason"] else None,
						"name": weighing["social_reason"]["name"] if weighing["social_reason"] else None,
						"cell": weighing["social_reason"]["cell"] if weighing["social_reason"] else None,
						"cfpiva": weighing["social_reason"]["cfpiva"] if weighing["social_reason"] else None
					},
					"vector": {
						"id": weighing["vector"]["id"] if weighing["vector"] else None,
						"name": weighing["vector"]["name"] if weighing["vector"] else None,
						"cell": weighing["vector"]["cell"] if weighing["vector"] else None,
						"cfpiva": weighing["vector"]["cfpiva"] if weighing["vector"] else None
					},
					"material": {
						"id": weighing["material"]["id"] if weighing["material"] else None,
						"name": weighing["material"]["name"] if weighing["material"] else None
					},
					"note": weighing["note"],
				})
				self.setIdSelected(instance_name=instance.instance_name, weigher_name=instance.weigher_name, new_id=data_dto.id_selected.id)
				self.setDataInExecution(instance_name=instance.instance_name, weigher_name=instance.weigher_name, source=data_in_execution)
		elif not data_dto.id_selected.id and not lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"]["id_selected"]["id"]:
			self.setDataInExecution(instance_name=instance.instance_name, weigher_name=instance.weigher_name, source=data_dto.data_in_execution)
		return self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)

	async def DeleteData(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		self.deleteDataInExecution(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
		self.deleteIdSelected(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
		return self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)