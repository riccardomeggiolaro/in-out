from fastapi import APIRouter, Depends
import libs.lb_config as lb_config
from applications.utils.utils_weigher import InstanceNameWeigherDTO, get_query_params_name_node
from applications.router.weigher.dto import DataDTO
from applications.router.weigher.types import DataInExecution as DataInExecutionType
from applications.router.weigher.config_weigher import ConfigWeigher
from modules.md_database.functions.get_data_by_id import get_data_by_id
from modules.md_database.functions.get_reservation_by_id import get_reservation_by_id
from modules.md_database.functions.select_reservation_if_uncomplete import select_reservation_if_uncomplete

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
				select_reservation_if_uncomplete(data_dto.id_selected.id)
				reservation = get_reservation_by_id(data_dto.id_selected.id)
				id_material = None
				description_material = None
				if len(reservation.in_out) > 0 and reservation.in_out[-1].idMaterial:
					id_material = reservation.in_out[-1].material.id
					description_material = reservation.in_out[-1].material.description
				data_in_execution = DataInExecutionType(**{
					"typeSubject": reservation.typeSubject.name,
					"subject": {
						"id": reservation.subject.id if reservation.subject else None,
						"social_reason": reservation.subject.social_reason if reservation.subject else None,
						"telephone": reservation.subject.telephone if reservation.subject else None,
						"cfpiva": reservation.subject.cfpiva if reservation.subject else None
					},
					"vector": {
						"id": reservation.vector.id if reservation.vector else None,
						"social_reason": reservation.vector.social_reason if reservation.vector else None,
						"telephone": reservation.vector.telephone if reservation.vector else None,
						"cfpiva": reservation.vector.cfpiva if reservation.vector else None
					},
					"driver": {
						"id": reservation.driver.id if reservation.driver else None,
						"social_reason": reservation.driver.social_reason if reservation.driver else None,
						"telephone": reservation.driver.telephone if reservation.driver else None,
					},
					"vehicle": {
						"id": reservation.vehicle.id if reservation.vehicle else None,
						"plate": reservation.vehicle.plate if reservation.vehicle else None,
						"description": reservation.vehicle.description if reservation.vehicle else None,
					},
					"material": {
						"id": id_material,
						"description": description_material
					},
					"note": reservation.note,
					"document_reference": reservation.document_reference
				})
				self.setIdSelected(instance_name=instance.instance_name, weigher_name=instance.weigher_name, new_id=data_dto.id_selected.id)
				self.setDataInExecution(instance_name=instance.instance_name, weigher_name=instance.weigher_name, source=data_in_execution)
		else:
			self.setDataInExecution(instance_name=instance.instance_name, weigher_name=instance.weigher_name, source=data_dto.data_in_execution)
		return self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)

	async def DeleteData(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		self.deleteDataInExecution(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
		self.deleteIdSelected(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
		return self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)