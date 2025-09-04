from fastapi import APIRouter, Depends, HTTPException, Request
from applications.utils.utils_weigher import InstanceNameWeigherDTO, get_query_params_name_node
from applications.router.weigher.dto import DataDTO
from applications.router.weigher.types import DataInExecution as DataInExecutionType
from applications.router.weigher.callback_weigher import CallbackWeigher
from modules.md_database.functions.get_reservation_by_id import get_reservation_by_id
from modules.md_database.functions.get_reservation_by_vehicle_id_if_uncompete import get_reservation_by_vehicle_id_if_uncomplete
from modules.md_database.functions.update_reservation import update_reservation
from modules.md_database.interfaces.reservation import SetReservationDTO
from modules.md_database.md_database import ReservationStatus, TypeReservation
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
			reservation = get_reservation_by_id(data_dto.id_selected.id)
			if reservation.status == ReservationStatus.CLOSED:
				raise HTTPException(status_code=400, detail=f"Non puoi selezionare l'accesso con id '{data_dto.id_selected.id}' perchè è già chiuso")
			if len(reservation.in_out) > 0:
				if reservation.in_out[-1].idWeight1 is not None and reservation.in_out[-1].idWeight2 is None:
					weight1 = reservation.in_out[-1].weight1.weight
				elif reservation.in_out[-1].idWeight1 is not None and reservation.in_out[-1].idWeight2 is not None and reservation.number_in_out is not None:
					weight1 = reservation.in_out[-1].weight2.weight
				if reservation.in_out[-1].idMaterial:
					id_material = reservation.in_out[-1].material.id
					description_material = reservation.in_out[-1].material.description
		if tare != "0" and data_dto.id_selected.id not in [-1, None] and weight1:
			raise HTTPException(status_code=400, detail="E' necessario rimuovere la tara per selezionare il mezzo perchè ha già effettuato l'entrata.")
		id_selected = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"]["id_selected"]["id"]
		type_current_reservation = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"]["type"]
		if data_dto.data_in_execution.vehicle.id:
			reservation = get_reservation_by_vehicle_id_if_uncomplete(data_dto.data_in_execution.vehicle.id)
			if reservation:
				checked = False
				if id_selected is None and reservation["number_in_out"] is None and reservation["status"] != ReservationStatus.CLOSED:
					if len(reservation["in_out"]) == 0:
						data_dto.id_selected.id = reservation["id"]
						checked = True
					elif len(reservation["in_out"]) > 0 and reservation["in_out"][-1].idWeight2 is not None:
						data_dto.id_selected.id = reservation["id"]
						checked = True
				if checked is False:
					raise HTTPException(status_code=400, detail=f"E' presente una prenotazione con la targa '{data_dto.data_in_execution.vehicle.plate}' ancora da chiudere")
		updated = None
		if id_selected:
			if type_current_reservation != TypeReservation.MANUALLY.name and data_dto.id_selected.id is None:
				raise HTTPException(status_code=400, detail=f"Non puoi modificare i dati di un accesso di tipo '{TypeReservation[type_current_reservation].value}'")
			body = SetReservationDTO(**data_dto.data_in_execution.dict())
			reservation = get_reservation_by_id(id_selected)
			idInOut = None
			if reservation and len(reservation.in_out) > 0:
				idInOut = reservation.in_out[-1].id
			updated = update_reservation(id_selected, body, idInOut)
			if data_dto.id_selected.id != -1:
				data = json.dumps({"id": id_selected})
				await self.broadcastUpdateAnagrafic("reservation", {"reservation": data})
		if data_dto.id_selected.id:
			await self.DeleteData(instance=instance)
			if data_dto.id_selected.id != -1:
				reservation = get_reservation_by_id(data_dto.id_selected.id)
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
						"tare": reservation.vehicle.tare if reservation.vehicle else None
					},
					"material": {
						"id": id_material,
						"description": description_material
					},
					"note": reservation.note,
					"document_reference": reservation.document_reference,
					"badge": reservation.badge,
				})
				self.setIdSelected(instance_name=instance.instance_name, weigher_name=instance.weigher_name, new_id=data_dto.id_selected.id, weight1=weight1)
				self.setDataInExecution(instance_name=instance.instance_name, weigher_name=instance.weigher_name, source=data_in_execution, idReservation=data_dto.id_selected.id)
				lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"]["type"] = reservation.type.name
				lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"]["number_in_out"] = reservation.number_in_out
				lb_config.saveconfig()
		else:
			# FUNZIONE UTILE PER GLI AGGIORNAMENTI RAPIDI DEI DATI IN ESECUZIONE DALLA DASHBAORD
			if request and updated:
				await self.DeleteData(instance=instance)
				lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"]["type"] = reservation.type.name
				lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"]["number_in_out"] = reservation.number_in_out
				lb_config.saveconfig()
			else:
				self.setDataInExecution(instance_name=instance.instance_name, weigher_name=instance.weigher_name, source=data_dto.data_in_execution)
		data = self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
		tare = data["data_in_execution"]["vehicle"]["tare"]
		import libs.lb_log as lb_log
		lb_log.warning(f"WEIGHT1: {data['id_selected']['weight1']}")
		lb_log.warning(f"TARE: {tare}")
		if data["id_selected"]["weight1"] is None and tare is not None:
			r =	md_weigher.module_weigher.setModope(instance_name=instance.instance_name, weigher_name=instance.weigher_name, modope="PRESETTARE", presettare=tare)
			lb_log.warning(r)
		return data

	async def DeleteData(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		self.deleteDataInExecution(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
		self.deleteIdSelected(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
		lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"]["type"] = TypeReservation.MANUALLY.name
		lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["data"]["number_in_out"] = 1
		lb_config.saveconfig()
		return self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)