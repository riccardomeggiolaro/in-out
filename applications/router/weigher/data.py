from fastapi import APIRouter, Depends, HTTPException, Request
from applications.utils.utils_weigher import InstanceNameWeigherDTO, get_query_params_name_node
from applications.router.weigher.dto import DataDTO
from applications.router.weigher.types import DataInExecution as DataInExecutionType
from applications.router.weigher.callback_weigher import CallbackWeigher
from applications.router.weigher.manager_weighers_data import weighers_data
from modules.md_database.functions.get_access_by_id import get_access_by_id
from modules.md_database.functions.get_access_by_vehicle_id_if_uncompete import get_access_by_vehicle_id_if_uncomplete
from modules.md_database.functions.update_access import update_access
from modules.md_database.interfaces.access import SetAccessDTO
from modules.md_database.md_database import AccessStatus, TypeAccess
import libs.lb_config as lb_config
import json
import modules.md_weigher.md_weigher as md_weigher
import asyncio

class DataRouter(CallbackWeigher):
	def __init__(self):
		super().__init__()

		for instance_name, instance in lb_config.g_config["app_api"]["weighers"].items():
			for weigher_name, weigher in instance["nodes"].items():
				instanceNameWeigher = InstanceNameWeigherDTO(**{"instance_name": instance_name, "weigher_name": weigher_name})
				asyncio.run(self.DeleteData(instanceNameWeigher))
		
		self.router_data = APIRouter()
	
		self.router_data.add_api_route('', self.GetDataInExecution, methods=['GET'])
		self.router_data.add_api_route('', self.SetData, methods=['PATCH'])
		self.router_data.add_api_route('', self.DeleteData, methods=['DELETE'])
 
	async def GetDataInExecution(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		return self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)

	async def SetData(self, request: Request, data_dto: DataDTO, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		if request is not None and request.state.user.level == 1:
			continues = True
			if data_dto.data_in_execution.vehicle.plate and not data_dto.data_in_execution.vehicle.id:
				continues = False
			if data_dto.data_in_execution.subject.social_reason and not data_dto.data_in_execution.subject.id:
				continues = False
			if data_dto.data_in_execution.vector.social_reason and not data_dto.data_in_execution.vector.id:
				continues = False
			if data_dto.data_in_execution.driver.social_reason and not data_dto.data_in_execution.driver.id:
				continues = False
			if not continues:
				raise HTTPException(status_code=400, detail="Puoi utilizzare solo i dati registrati nelle anagrafiche per effettuare le pesate")
		tare = md_weigher.module_weigher.getRealtime(instance_name=instance.instance_name, weigher_name=instance.weigher_name).tare
		weight1 = None
		id_material = None
		description_material = None
		if data_dto.id_selected.id not in [-1, None]:
			access = get_access_by_id(data_dto.id_selected.id)
			if access.status == AccessStatus.CLOSED:
				raise HTTPException(status_code=400, detail=f"Non puoi selezionare l'accesso con id '{data_dto.id_selected.id}' perchè è già chiuso")
			if len(access.in_out) > 0:
				if access.in_out[-1].idWeight1 is not None and access.in_out[-1].idWeight2 is None:
					weight1 = access.in_out[-1].weight1.weight
				elif access.in_out[-1].idWeight1 is not None and access.in_out[-1].idWeight2 is not None and access.number_in_out is not None:
					weight1 = access.in_out[-1].weight2.weight
				if access.in_out[-1].idMaterial:
					id_material = access.in_out[-1].material.id
					description_material = access.in_out[-1].material.description
		if tare != "0" and data_dto.id_selected.id not in [-1, None] and weight1:
			raise HTTPException(status_code=400, detail="E' necessario rimuovere la tara per selezionare il mezzo perchè ha già effettuato l'entrata.")
		id_selected = weighers_data[instance.instance_name][instance.weigher_name]["data"]["id_selected"]["id"]
		type_current_access = weighers_data[instance.instance_name][instance.weigher_name]["data"]["type"]
		if data_dto.data_in_execution.vehicle.id:
			access = get_access_by_vehicle_id_if_uncomplete(data_dto.data_in_execution.vehicle.id)
			if access:
				checked = False
				if id_selected is None and access["number_in_out"] is None and access["status"] != AccessStatus.CLOSED:
					if len(access["in_out"]) == 0:
						data_dto.id_selected.id = access["id"]
						checked = True
					elif len(access["in_out"]) > 0 and access["in_out"][-1].idWeight2 is not None:
						data_dto.id_selected.id = access["id"]
						checked = True
				if checked is False:
					raise HTTPException(status_code=400, detail=f"E' presente una prenotazione con la targa '{data_dto.data_in_execution.vehicle.plate}' ancora da chiudere")
		updated = None
		if id_selected:
			if type_current_access != TypeAccess.MANUALLY.name and data_dto.id_selected.id is None:
				raise HTTPException(status_code=400, detail=f"Non puoi modificare i dati di un accesso di tipo '{TypeAccess[type_current_access].value}'")
			body = SetAccessDTO(**data_dto.data_in_execution.dict())
			access = get_access_by_id(id_selected)
			idInOut = None
			if access and len(access.in_out) > 0:
				idInOut = access.in_out[-1].id
			updated = update_access(id_selected, body, idInOut)
			if data_dto.id_selected.id != -1:
				data = json.dumps({"id": id_selected})
				await self.broadcastUpdateAnagrafic("access", {"access": data})
		if data_dto.id_selected.id:
			await self.DeleteData(instance=instance)
			if data_dto.id_selected.id != -1:
				access = get_access_by_id(data_dto.id_selected.id)
				data_in_execution = DataInExecutionType(**{
					"typeSubject": access.typeSubject.name,
					"subject": {
						"id": access.subject.id if access.subject else None,
						"social_reason": access.subject.social_reason if access.subject else None,
						"telephone": access.subject.telephone if access.subject else None,
						"cfpiva": access.subject.cfpiva if access.subject else None
					},
					"vector": {
						"id": access.vector.id if access.vector else None,
						"social_reason": access.vector.social_reason if access.vector else None,
						"telephone": access.vector.telephone if access.vector else None,
						"cfpiva": access.vector.cfpiva if access.vector else None
					},
					"driver": {
						"id": access.driver.id if access.driver else None,
						"social_reason": access.driver.social_reason if access.driver else None,
						"telephone": access.driver.telephone if access.driver else None,
					},
					"vehicle": {
						"id": access.vehicle.id if access.vehicle else None,
						"plate": access.vehicle.plate if access.vehicle else None,
						"description": access.vehicle.description if access.vehicle else None,
						"tare": access.vehicle.tare if access.vehicle else None
					},
					"material": {
						"id": id_material,
						"description": description_material
					},
					"note": access.note,
					"document_reference": access.document_reference,
					"badge": access.badge,
				})
				self.setIdSelected(instance_name=instance.instance_name, weigher_name=instance.weigher_name, new_id=data_dto.id_selected.id, weight1=weight1)
				self.setDataInExecution(instance_name=instance.instance_name, weigher_name=instance.weigher_name, source=data_in_execution, idAccess=data_dto.id_selected.id)
				weighers_data[instance.instance_name][instance.weigher_name]["data"]["type"] = access.type.name
				weighers_data[instance.instance_name][instance.weigher_name]["data"]["number_in_out"] = access.number_in_out
		else:
			# FUNZIONE UTILE PER GLI AGGIORNAMENTI RAPIDI DEI DATI IN ESECUZIONE DALLA DASHBAORD
			if request and updated:
				await self.DeleteData(instance=instance)
				weighers_data[instance.instance_name][instance.weigher_name]["data"]["type"] = access.type.name
				weighers_data[instance.instance_name][instance.weigher_name]["data"]["number_in_out"] = access.number_in_out
			else:
				self.setDataInExecution(instance_name=instance.instance_name, weigher_name=instance.weigher_name, source=data_dto.data_in_execution)
		data = self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
		tare = data["data_in_execution"]["vehicle"]["tare"]
		if data["id_selected"]["weight1"] is None and tare is not None:
			r =	md_weigher.module_weigher.setModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name, modope="PRESETTARE", presettare=tare)
		return data

	async def DeleteData(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		self.deleteDataInExecution(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
		self.deleteIdSelected(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
		weighers_data[instance.instance_name][instance.weigher_name]["data"]["type"] = TypeAccess.MANUALLY.name
		weighers_data[instance.instance_name][instance.weigher_name]["data"]["number_in_out"] = 1
		return self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)