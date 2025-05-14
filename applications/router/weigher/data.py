from fastapi import APIRouter, Depends
import libs.lb_config as lb_config
import modules.md_weigher.md_weigher as md_weigher
from applications.utils.utils_weigher import InstanceNameWeigherDTO, get_query_params_name_node
from applications.router.weigher.dto import DataDTO, DataInExecutionDTO
from applications.router.weigher.types import DataInExecution as DataInExecutionType, Data
from applications.router.weigher.config_weigher import ConfigWeigher
import asyncio
from libs.lb_utils import check_values
from modules.md_database.functions.get_data_by_id import get_data_by_id

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
					"typeSubject": weighing["typeSubject"],
					"subject": {
						"id": weighing["subject"]["id"] if weighing["subject"] else None,
						"social_reason": weighing["subject"]["social_reason"] if weighing["subject"] else None,
						"telephone": weighing["subject"]["telephone"] if weighing["subject"] else None,
						"cfpiva": weighing["subject"]["cfpiva"] if weighing["subject"] else None
					},
					"vector": {
						"id": weighing["vector"]["id"] if weighing["vector"] else None,
						"social_reason": weighing["vector"]["social_reason"] if weighing["vector"] else None,
						"telephone": weighing["vector"]["telephone"] if weighing["vector"] else None,
						"cfpiva": weighing["vector"]["cfpiva"] if weighing["vector"] else None
					},
					"driver": {
						"id": weighing["driver"]["id"] if weighing["driver"] else None,
						"social_reason": weighing["driver"]["social_reason"] if weighing["driver"] else None,
						"telephone": weighing["driver"]["telephone"] if weighing["driver"] else None,
					},
					"vehicle": {
						"id": weighing["vehicle"]["id"] if weighing["vehicle"] else None,
						"plate": weighing["vehicle"]["plate"] if weighing["vehicle"] else None,
						"description": weighing["vehicle"]["description"] if weighing["vehicle"] else None,
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