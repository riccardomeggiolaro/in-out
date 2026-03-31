from fastapi import APIRouter, Depends, HTTPException, Request
from applications.utils.utils_weigher import InstanceNameWeigherDTO, get_query_params_name_node
from applications.router.weigher.dto import DataDTO
from applications.router.weigher.types import DataInExecution as DataInExecutionType
from applications.router.weigher.callback_weigher import CallbackWeigher
from applications.router.weigher.manager_weighers_data import weighers_data
from modules.md_database.functions.get_access_by_id import get_access_by_id
from modules.md_database.functions.get_access_by_vehicle_id_if_uncompete import get_access_by_vehicle_id_if_uncomplete
from modules.md_database.functions.get_access_by_plate_if_uncomplete import get_access_by_plate_if_uncomplete
from modules.md_database.functions.get_data_by_attributes import get_data_by_attributes
from modules.md_database.functions.update_access import update_access
from modules.md_database.functions.update_data import update_data
from modules.md_database.interfaces.access import SetAccessDTO
from modules.md_database.md_database import AccessStatus, TypeAccess, TypeSubjectEnum
import libs.lb_config as lb_config
import json
import modules.md_weigher.md_weigher as md_weigher
import asyncio
from typing import Optional

class DataRouter(CallbackWeigher):
	def __init__(self):
		super().__init__()

		for instance_name, instance in lb_config.g_config["app_api"]["weighers"].items():
			for weigher_name, weigher in instance["nodes"].items():
				instanceNameWeigher = InstanceNameWeigherDTO(**{"instance_name": instance_name, "weigher_name": weigher_name})
				asyncio.run(self.DeleteData(instanceNameWeigher))
		
		self.router_data = APIRouter()
	
		self.router_data.add_api_route('', self.GetData, methods=['GET'])
		self.router_data.add_api_route('', self.SetData, methods=['PATCH'])
		self.router_data.add_api_route('', self.DeleteData, methods=['DELETE'])
 
	async def GetData(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
		return self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)

	async def SetData(self, request: Request, data_dto: DataDTO, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node), need_to_confirm: Optional[bool] = False, auto_select: Optional[bool] = False, keep_selected: Optional[bool] = False):
		if auto_select:
			# Auto-select anagrafiche by name/plate if they exist
			if data_dto.data_in_execution.vehicle.plate and not data_dto.data_in_execution.vehicle.id:
				vehicle = get_data_by_attributes("vehicle", {"plate": data_dto.data_in_execution.vehicle.plate.upper()})
				if vehicle:
					data_dto.data_in_execution.vehicle.id = vehicle["id"]
			if data_dto.data_in_execution.subject.social_reason and not data_dto.data_in_execution.subject.id:
				subject = get_data_by_attributes("subject", {"social_reason": data_dto.data_in_execution.subject.social_reason})
				if subject:
					data_dto.data_in_execution.subject.id = subject["id"]
			if data_dto.data_in_execution.vector.social_reason and not data_dto.data_in_execution.vector.id:
				vector = get_data_by_attributes("vector", {"social_reason": data_dto.data_in_execution.vector.social_reason})
				if vector:
					data_dto.data_in_execution.vector.id = vector["id"]
			if data_dto.data_in_execution.driver.social_reason and not data_dto.data_in_execution.driver.id:
				driver = get_data_by_attributes("driver", {"social_reason": data_dto.data_in_execution.driver.social_reason})
				if driver:
					data_dto.data_in_execution.driver.id = driver["id"]
		if request is not None:
			if request.state.user.level == 1:
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
			if data_dto.id_selected.id == weighers_data[instance.instance_name][instance.weigher_name]["data"]["id_selected"]["id"]:
				need_to_confirm = weighers_data[instance.instance_name][instance.weigher_name]["data"]["id_selected"]["need_to_confirm"]
			else:
				need_to_confirm = False
		tare = md_weigher.module_weigher.getRealtime(instance_name=instance.instance_name, weigher_name=instance.weigher_name).tare
		weight1 = None
		# In_out-level data (priority over access)
		io_data = {
			"material": {"id": None, "description": None},
			"subject": {"id": None, "social_reason": None, "telephone": None, "cfpiva": None},
			"vector": {"id": None, "social_reason": None, "telephone": None, "cfpiva": None},
			"driver": {"id": None, "social_reason": None, "telephone": None},
			"typeSubject": None,
			"note": None,
			"document_reference": None,
		}
		io_data_from_in_out = False
		if data_dto.id_selected.id not in [-1, None]:
			access = get_access_by_id(data_dto.id_selected.id)
			if access.status == AccessStatus.CLOSED:
				raise HTTPException(status_code=400, detail=f"Non puoi selezionare l'accesso con id '{data_dto.id_selected.id}' perchè è già chiuso")
			last_in_out_open = False
			if len(access.in_out) > 0:
				if access.in_out[-1].idWeight1 is not None and access.in_out[-1].idWeight2 is None:
					weight1 = access.in_out[-1].weight1.weight
				elif access.in_out[-1].idWeight1 is not None and access.in_out[-1].idWeight2 is not None and access.number_in_out is not None:
					weight1 = access.in_out[-1].weight2.weight
				# in_out data has precedence (even if empty) only if in_out is still open
				if access.in_out[-1].net_weight is None:
					last_in_out_open = True
					io_data_from_in_out = True
					lio = access.in_out[-1]
					if lio.idMaterial and lio.material:
						io_data["material"] = {"id": lio.material.id, "description": lio.material.description}
					if lio.idSubject and lio.subject:
						io_data["subject"] = {"id": lio.subject.id, "social_reason": lio.subject.social_reason, "telephone": lio.subject.telephone, "cfpiva": lio.subject.cfpiva}
					if lio.idVector and lio.vector:
						io_data["vector"] = {"id": lio.vector.id, "social_reason": lio.vector.social_reason, "telephone": lio.vector.telephone, "cfpiva": lio.vector.cfpiva}
					if lio.idDriver and lio.driver:
						io_data["driver"] = {"id": lio.driver.id, "social_reason": lio.driver.social_reason, "telephone": lio.driver.telephone}
					if lio.typeSubject:
						io_data["typeSubject"] = lio.typeSubject.name if hasattr(lio.typeSubject, 'name') else lio.typeSubject
					io_data["note"] = lio.note
					io_data["document_reference"] = lio.document_reference
			if not last_in_out_open:
				# No in_out or last in_out is closed — use access/reservation data
				if access.idMaterial and access.material:
					io_data["material"] = {"id": access.material.id, "description": access.material.description}
				if access.idSubject and access.subject:
					io_data["subject"] = {"id": access.subject.id, "social_reason": access.subject.social_reason, "telephone": access.subject.telephone, "cfpiva": access.subject.cfpiva}
				if access.idVector and access.vector:
					io_data["vector"] = {"id": access.vector.id, "social_reason": access.vector.social_reason, "telephone": access.vector.telephone, "cfpiva": access.vector.cfpiva}
				if access.idDriver and access.driver:
					io_data["driver"] = {"id": access.driver.id, "social_reason": access.driver.social_reason, "telephone": access.driver.telephone}
				if access.typeSubject:
					io_data["typeSubject"] = access.typeSubject.name if hasattr(access.typeSubject, 'name') else access.typeSubject
				io_data["note"] = access.note
				io_data["document_reference"] = access.document_reference
		if tare != "0" and data_dto.id_selected.id not in [-1, None] and weight1:
			raise HTTPException(status_code=400, detail="E' necessario rimuovere la tara per selezionare il mezzo perchè ha già effettuato l'entrata.")
		id_selected = weighers_data[instance.instance_name][instance.weigher_name]["data"]["id_selected"]["id"]
		type_current_access = weighers_data[instance.instance_name][instance.weigher_name]["data"]["type"]
		# Preserve current id_selected when keep_selected is true
		if keep_selected and id_selected and data_dto.id_selected.id is None:
			data_dto.id_selected.id = id_selected
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
					if auto_select:
						data_dto.id_selected.id = access["id"]
					else:
						raise HTTPException(status_code=400, detail=f"E' presente una prenotazione con la targa '{data_dto.data_in_execution.vehicle.plate}' ancora da chiudere")
		elif data_dto.data_in_execution.vehicle.plate and not data_dto.data_in_execution.vehicle.id:
			access = get_access_by_plate_if_uncomplete(data_dto.data_in_execution.vehicle.plate.upper())
			if access:
				checked = False
				if id_selected is None and access["number_in_out"] is None and access.get("status") != AccessStatus.CLOSED:
					if len(access["in_out"]) == 0:
						data_dto.id_selected.id = access["id"]
						data_dto.data_in_execution.vehicle.id = access["idVehicle"]
						checked = True
					elif len(access["in_out"]) > 0 and access["in_out"][-1].idWeight2 is not None:
						data_dto.id_selected.id = access["id"]
						data_dto.data_in_execution.vehicle.id = access["idVehicle"]
						checked = True
				if checked is False:
					if auto_select:
						data_dto.id_selected.id = access["id"]
						data_dto.data_in_execution.vehicle.id = access["idVehicle"]
					else:
						raise HTTPException(status_code=400, detail=f"E' presente una prenotazione con la targa '{data_dto.data_in_execution.vehicle.plate}' ancora da chiudere")
		# Recalculate weight1 and io_data if an access was selected after the initial check
		if data_dto.id_selected.id not in [-1, None] and weight1 is None:
			access_for_weight = get_access_by_id(data_dto.id_selected.id)
			if access_for_weight and len(access_for_weight.in_out) > 0:
				if access_for_weight.in_out[-1].idWeight1 is not None and access_for_weight.in_out[-1].idWeight2 is None:
					weight1 = access_for_weight.in_out[-1].weight1.weight
				elif access_for_weight.in_out[-1].idWeight1 is not None and access_for_weight.in_out[-1].idWeight2 is not None and access_for_weight.number_in_out is not None:
					weight1 = access_for_weight.in_out[-1].weight2.weight
				if access_for_weight.in_out[-1].net_weight is None:
					io_data_from_in_out = True
					lio = access_for_weight.in_out[-1]
					if lio.idMaterial and lio.material:
						io_data["material"] = {"id": lio.material.id, "description": lio.material.description}
					if lio.idSubject and lio.subject:
						io_data["subject"] = {"id": lio.subject.id, "social_reason": lio.subject.social_reason, "telephone": lio.subject.telephone, "cfpiva": lio.subject.cfpiva}
					if lio.idVector and lio.vector:
						io_data["vector"] = {"id": lio.vector.id, "social_reason": lio.vector.social_reason, "telephone": lio.vector.telephone, "cfpiva": lio.vector.cfpiva}
					if lio.idDriver and lio.driver:
						io_data["driver"] = {"id": lio.driver.id, "social_reason": lio.driver.social_reason, "telephone": lio.driver.telephone}
			elif access_for_weight:
				if access_for_weight.idMaterial and access_for_weight.material:
					io_data["material"] = {"id": access_for_weight.material.id, "description": access_for_weight.material.description}
				if access_for_weight.idSubject and access_for_weight.subject:
					io_data["subject"] = {"id": access_for_weight.subject.id, "social_reason": access_for_weight.subject.social_reason, "telephone": access_for_weight.subject.telephone, "cfpiva": access_for_weight.subject.cfpiva}
				if access_for_weight.idVector and access_for_weight.vector:
					io_data["vector"] = {"id": access_for_weight.vector.id, "social_reason": access_for_weight.vector.social_reason, "telephone": access_for_weight.vector.telephone, "cfpiva": access_for_weight.vector.cfpiva}
				if access_for_weight.idDriver and access_for_weight.driver:
					io_data["driver"] = {"id": access_for_weight.driver.id, "social_reason": access_for_weight.driver.social_reason, "telephone": access_for_weight.driver.telephone}
		updated = None
		if id_selected:
			if type_current_access != TypeAccess.MANUALLY.name and (data_dto.id_selected.id is None or keep_selected):
				# Non-manual access: update data_in_execution in memory
				access = get_access_by_id(id_selected)
				die = weighers_data[instance.instance_name][instance.weigher_name]["data"]["data_in_execution"]
				if data_dto.data_in_execution.subject.id or data_dto.data_in_execution.subject.social_reason:
					die["subject"]["id"] = data_dto.data_in_execution.subject.id
					die["subject"]["social_reason"] = data_dto.data_in_execution.subject.social_reason
					if data_dto.data_in_execution.typeSubject:
						die["typeSubject"] = data_dto.data_in_execution.typeSubject
				if data_dto.data_in_execution.vector.id or data_dto.data_in_execution.vector.social_reason:
					die["vector"]["id"] = data_dto.data_in_execution.vector.id
					die["vector"]["social_reason"] = data_dto.data_in_execution.vector.social_reason
				if data_dto.data_in_execution.driver.id or data_dto.data_in_execution.driver.social_reason:
					die["driver"]["id"] = data_dto.data_in_execution.driver.id
					die["driver"]["social_reason"] = data_dto.data_in_execution.driver.social_reason
				if data_dto.data_in_execution.material.id or data_dto.data_in_execution.material.description:
					die["material"]["id"] = data_dto.data_in_execution.material.id
					die["material"]["description"] = data_dto.data_in_execution.material.description
				if data_dto.data_in_execution.note is not None:
					die["note"] = data_dto.data_in_execution.note if data_dto.data_in_execution.note != "" else None
				if data_dto.data_in_execution.document_reference is not None:
					die["document_reference"] = data_dto.data_in_execution.document_reference if data_dto.data_in_execution.document_reference != "" else None
				broadcast_data = json.dumps({"id": id_selected})
				await self.broadcastUpdateAnagrafic("access", {"access": broadcast_data})
				self.Callback_DataInExecution(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
				data = self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
				return data
			elif type_current_access == TypeAccess.MANUALLY.name and data_dto.id_selected.id is None and not data_dto.data_in_execution.vehicle.id and not data_dto.data_in_execution.vehicle.plate:
				# Manual access: update data without deselecting
				access = get_access_by_id(id_selected)
				has_open_in_out = access and len(access.in_out) > 0 and access.in_out[-1].idWeight1 is not None and access.in_out[-1].idWeight2 is None
				if not has_open_in_out:
					# No open in_out: save to access record in DB
					update_access(id_selected, SetAccessDTO(**data_dto.data_in_execution.dict()), None)
				# Always update in-memory (DB save for in_out happens at weighing time)
				self.setDataInExecution(instance_name=instance.instance_name, weigher_name=instance.weigher_name, source=data_dto.data_in_execution)
				broadcast_data = json.dumps({"id": id_selected})
				await self.broadcastUpdateAnagrafic("access", {"access": broadcast_data})
				data = self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
				return data
			body = SetAccessDTO(**data_dto.data_in_execution.dict())
			access = get_access_by_id(id_selected)
			idInOut = None
			if access and len(access.in_out) > 0:
				idInOut = access.in_out[-1].id
			updated = update_access(id_selected, body, idInOut)
			# Refresh io_data from the updated access/in_out after save
			updated_access = get_access_by_id(id_selected)
			if updated_access:
				refreshed = False
				if len(updated_access.in_out) > 0 and updated_access.in_out[-1].net_weight is None:
					refreshed = True
					lio = updated_access.in_out[-1]
					io_data["material"] = {"id": lio.material.id, "description": lio.material.description} if lio.idMaterial and lio.material else {"id": None, "description": None}
					io_data["subject"] = {"id": lio.subject.id, "social_reason": lio.subject.social_reason, "telephone": lio.subject.telephone, "cfpiva": lio.subject.cfpiva} if lio.idSubject and lio.subject else {"id": None, "social_reason": None, "telephone": None, "cfpiva": None}
					io_data["vector"] = {"id": lio.vector.id, "social_reason": lio.vector.social_reason, "telephone": lio.vector.telephone, "cfpiva": lio.vector.cfpiva} if lio.idVector and lio.vector else {"id": None, "social_reason": None, "telephone": None, "cfpiva": None}
					io_data["driver"] = {"id": lio.driver.id, "social_reason": lio.driver.social_reason, "telephone": lio.driver.telephone} if lio.idDriver and lio.driver else {"id": None, "social_reason": None, "telephone": None}
					io_data_from_in_out = True
				if not refreshed:
					io_data["material"] = {"id": updated_access.material.id, "description": updated_access.material.description} if updated_access.idMaterial and updated_access.material else {"id": None, "description": None}
					io_data["subject"] = {"id": updated_access.subject.id, "social_reason": updated_access.subject.social_reason, "telephone": updated_access.subject.telephone, "cfpiva": updated_access.subject.cfpiva} if updated_access.idSubject and updated_access.subject else {"id": None, "social_reason": None, "telephone": None, "cfpiva": None}
					io_data["vector"] = {"id": updated_access.vector.id, "social_reason": updated_access.vector.social_reason, "telephone": updated_access.vector.telephone, "cfpiva": updated_access.vector.cfpiva} if updated_access.idVector and updated_access.vector else {"id": None, "social_reason": None, "telephone": None, "cfpiva": None}
					io_data["driver"] = {"id": updated_access.driver.id, "social_reason": updated_access.driver.social_reason, "telephone": updated_access.driver.telephone} if updated_access.idDriver and updated_access.driver else {"id": None, "social_reason": None, "telephone": None}
			if data_dto.id_selected.id != -1:
				data = json.dumps({"id": id_selected})
				await self.broadcastUpdateAnagrafic("access", {"access": data})
		if data_dto.id_selected.id:
			await self.DeleteData(instance=instance)
			if data_dto.id_selected.id != -1:
				access = get_access_by_id(data_dto.id_selected.id)
				data_in_execution = DataInExecutionType(**{
					"typeSubject": io_data["typeSubject"] or (access.typeSubject.name if access.typeSubject else "CUSTOMER"),
					"subject": io_data["subject"] if io_data["subject"]["id"] else {
						"id": access.subject.id if access.subject else None,
						"social_reason": access.subject.social_reason if access.subject else None,
						"telephone": access.subject.telephone if access.subject else None,
						"cfpiva": access.subject.cfpiva if access.subject else None
					},
					"vector": io_data["vector"] if io_data["vector"]["id"] else {
						"id": access.vector.id if access.vector else None,
						"social_reason": access.vector.social_reason if access.vector else None,
						"telephone": access.vector.telephone if access.vector else None,
						"cfpiva": access.vector.cfpiva if access.vector else None
					},
					"driver": io_data["driver"] if io_data["driver"]["id"] else {
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
					"material": io_data["material"] if io_data["material"]["id"] else {
						"id": access.material.id if access.material else None,
						"description": access.material.description if access.material else None
					},
					"note": io_data["note"] if (io_data_from_in_out and io_data["note"]) else (access.note or io_data["note"]),
					"document_reference": io_data["document_reference"] if (io_data_from_in_out and io_data["document_reference"]) else (access.document_reference or io_data["document_reference"]),
					"badge": access.badge,
				})
				self.setIdSelected(instance_name=instance.instance_name, weigher_name=instance.weigher_name, new_id=data_dto.id_selected.id, weight1=weight1, need_to_confirm=need_to_confirm)
				self.setDataInExecution(instance_name=instance.instance_name, weigher_name=instance.weigher_name, source=data_in_execution, idAccess=data_dto.id_selected.id)
				weighers_data[instance.instance_name][instance.weigher_name]["data"]["type"] = access.type.name
				weighers_data[instance.instance_name][instance.weigher_name]["data"]["number_in_out"] = access.number_in_out
				die = weighers_data[instance.instance_name][instance.weigher_name]["data"]["data_in_execution"]
				weighers_data[instance.instance_name][instance.weigher_name]["data"]["reservation_has_vehicle"] = die["vehicle"]["id"] is not None
				weighers_data[instance.instance_name][instance.weigher_name]["data"]["reservation_has_material"] = die["material"]["id"] is not None
				weighers_data[instance.instance_name][instance.weigher_name]["data"]["reservation_has_subject"] = die["subject"]["id"] is not None
				weighers_data[instance.instance_name][instance.weigher_name]["data"]["reservation_has_vector"] = die["vector"]["id"] is not None
				weighers_data[instance.instance_name][instance.weigher_name]["data"]["reservation_has_driver"] = die["driver"]["id"] is not None
				weighers_data[instance.instance_name][instance.weigher_name]["data"]["reservation_has_note"] = die.get("note") is not None and die.get("note") != ""
				weighers_data[instance.instance_name][instance.weigher_name]["data"]["reservation_has_document_reference"] = die.get("document_reference") is not None and die.get("document_reference") != ""
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
		self.deleteData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)
		return self.getData(instance_name=instance.instance_name, weigher_name=instance.weigher_name)