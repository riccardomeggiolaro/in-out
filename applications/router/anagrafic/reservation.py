from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Response, WebSocket as StringWebSocket
from typing import Dict, Union, Optional
from modules.md_database.md_database import upload_file_datas_required_columns, ReservationStatus
from modules.md_database.dtos.reservation import Reservation, AddReservationDTO, SetReservationDTO
from modules.md_database.dtos.subject import Subject
from modules.md_database.dtos.vector import Vector
from modules.md_database.dtos.driver import Driver
from modules.md_database.dtos.vehicle import Vehicle
from modules.md_database.dtos.material import Material
from modules.md_database.functions.filter_data import filter_data
from modules.md_database.functions.add_data import add_data
from modules.md_database.functions.delete_data import delete_data
from modules.md_database.functions.update_data import update_data
from modules.md_database.functions.delete_all_data import delete_all_data
from modules.md_database.functions.load_datas_into_db import load_datas_into_db
from modules.md_database.functions.get_list_reservations import get_list_reservations
from modules.md_database.functions.get_data_by_id import get_data_by_id
from modules.md_database.functions.get_data_by_attribute import get_data_by_attribute
from modules.md_database.functions.get_data_by_attributes import get_data_by_attributes
from modules.md_database.functions.get_reservation_by_plate_if_uncomplete import get_reservation_by_plate_if_incomplete
from modules.md_database.functions.delete_last_weighing_of_reservation import delete_last_weighing_of_reservation
import pandas as pd
import numpy as np
from applications.utils.utils import get_query_params, has_non_none_value
from applications.router.anagrafic.web_sockets import WebSocket
from datetime import datetime
from libs.lb_folders import get_image_from_folder
import libs.lb_config as lb_config

class ReservationRouter(WebSocket):
    def __init__(self):
        self.router = APIRouter()
        
        self.router.add_api_route('/list', self.getListReservations, methods=['GET'])
        self.router.add_api_route('', self.addReservation, methods=['POST'])
        self.router.add_api_route('/{id}', self.setReservation, methods=['PATCH'])
        self.router.add_api_route('/{id}', self.deleteReservation, methods=['DELETE'])
        self.router.add_api_route('', self.deleteAllReservations, methods=['DELETE'])
        self.router.add_api_route('/last-weighing/{id}', self.deleteLastWeighing, methods=['DELETE'])

    async def getListReservations(self, query_params: Dict[str, Union[str, int]] = Depends(get_query_params), limit: Optional[int] = None, offset: Optional[int] = None, fromDate: Optional[datetime] = None, toDate: Optional[datetime] = None):
        try:
            not_closed = False
            if "status" in query_params and query_params["status"] == "NOT_CLOSED":
                not_closed = True                
                del query_params["status"]
            if fromDate is not None:
                del query_params["fromDate"]
            if toDate is not None:
                del query_params["toDate"]
                toDate = toDate.replace(hour=23, minute=59, second=59, microsecond=999999)
            if limit is not None:
                del query_params["limit"]
            if offset is not None:
                del query_params["offset"]
            data, total_rows = get_list_reservations(query_params, not_closed, fromDate, toDate, limit, offset, ('date_created', 'desc'))
            return {
                "data": data,
                "total_rows": total_rows
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")

    async def addReservation(self, body: AddReservationDTO):
        try:
            if not body.vehicle.plate:
                raise HTTPException(status_code=400, detail="E' necessario l'inserimento di una targa")
            if get_reservation_by_plate_if_incomplete(body.vehicle.plate):
                raise HTTPException(status_code=400, detail=f"E' presente una prenotazione con la targa '{body.vehicle.plate}' ancora da chiudere")
            
            body.subject.id = body.subject.id if body.subject.id not in [None, -1] else None
            body.vector.id = body.vector.id if body.vector.id not in [None, -1] else None
            body.driver.id = body.driver.id if body.driver.id not in [None, -1] else None
            body.vehicle.id = body.vehicle.id if body.vehicle.id not in [None, -1] else None
            reservation_to_add = {
                "typeSubject": body.typeSubject,
                "idSubject": body.subject.id,
                "idVector": body.vector.id,
                "idDriver": body.driver.id,
                "idVehicle": body.vehicle.id,
                "idMaterial": None,
                "number_weighings": body.number_weighings,
                "note": body.note,
                "status": ReservationStatus.WAITING,
                "document_reference": body.document_reference
            }
            if body.subject.id in [None, -1] and body.subject.social_reason and get_data_by_attribute("subject", "social_reason", body.subject.social_reason):
                raise HTTPException(status_code=400, detail=f"Soggetto con ragione sociale '{body.subject.social_reason}' già esistente")
            if body.subject.id in [None, -1] and body.subject.cfpiva and get_data_by_attribute("subject", "cfpiva", body.subject.cfpiva):
                raise HTTPException(status_code=400, detail=f"Soggetto con CF/P.Iva '{body.subject.cfpiva}' già esistente")
            if body.vector.id in [None, -1] and body.vector.social_reason and get_data_by_attribute("vector", "social_reason", body.vector.social_reason):
                raise HTTPException(status_code=400, detail=f"Vettore con ragione sociale '{body.vector.social_reason}' già esistente")
            if body.vector.id in [None, -1] and body.vector.cfpiva and get_data_by_attribute("vector", "cfpiva", body.vector.cfpiva):
                raise HTTPException(status_code=400, detail=f"Vettore con CF/P.Iva '{body.vector.cfpiva}' già esistente")
            if body.driver.id in [None, -1] and body.driver.social_reason:
                del body.driver.id
                if get_data_by_attributes("driver", body.driver.dict()):
                    raise HTTPException(status_code=400, detail=f"Autista già registrato")
            if body.vehicle.id in [None, -1] and body.vehicle.plate and get_data_by_attribute("vehicle", "plate", body.vehicle.plate):
                raise HTTPException(status_code=400, detail=f"Veicolo con targa '{body.vehicle.plate}' già esistente")
            if not reservation_to_add["idSubject"] and has_non_none_value(body.subject.dict()):
                data = add_data("subject", body.subject.dict())
                subject = Subject(**data)
                await self.broadcastAddAnagrafic("subject", {"subject": subject.json()})
                reservation_to_add["idSubject"] = subject.id
            if not reservation_to_add["idVector"] and has_non_none_value(body.vector.dict()):
                data = add_data("vector", body.vector.dict())
                vector = Vector(**data)
                await self.broadcastAddAnagrafic("vector", {"vector": vector.json()})
                reservation_to_add["idVector"] = vector.id
            if not reservation_to_add["idDriver"] and has_non_none_value(body.driver.dict()):
                data = add_data("driver", body.driver.dict())
                driver = Driver(**data)
                await self.broadcastAddAnagrafic("driver", {"driver": driver.json()})
                reservation_to_add["idDriver"] = driver.id
            if not reservation_to_add["idVehicle"] and has_non_none_value(body.vehicle.dict()):
                data = add_data("vehicle", body.vehicle.dict())
                vehicle = Vehicle(**data)
                await self.broadcastAddAnagrafic("vehicle", {"vehicle": vehicle.json()})
                reservation_to_add["idVehicle"] = vehicle.id
            data = add_data("reservation", reservation_to_add)
            reservation = Reservation(**data).json()
            await self.broadcastAddAnagrafic("reservation", {"reservation": reservation})
            return reservation
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")

    async def setReservation(self, id: int, body: SetReservationDTO, websocket: StringWebSocket = None):
        if websocket and websocket not in manager_anagrafics["reservation"].active_connections:
            raise HTTPException(status_code=400, detail="Websocket need to be registered in the list of active connections")            
        reservation_to_update = {
            "typeSubject": body.typeSubject,
            "idSubject": body.subject.id,
            "idVector": body.vector.id,
            "idDriver": body.driver.id,
            "idVehicle": body.vehicle.id,
            "idMaterial": None,
            "number_weighings": body.number_weighings,
            "note": body.note,
            "status": None,
            "document_reference": body.document_reference
        }
        import libs.lb_log as lb_log
        if reservation_to_update["idVehicle"] == -1 and not body.vehicle.plate:
            raise HTTPException(status_code=400, detail="Il campo targa deve essere compilato")
        lb_log.warning(reservation_to_update["idVehicle"])
        lb_log.warning(body.vehicle.plate)
        just_exist_reservation = None
        if body.vehicle.plate:
            just_exist_reservation = get_reservation_by_plate_if_incomplete(body.vehicle.plate)
        if just_exist_reservation and just_exist_reservation.id != id:
            lb_log.warning("just exist")
            raise HTTPException(status_code=400, detail=f"E' presente una prenotazione con la targa '{body.vehicle.plate}' ancora da chiudere")
        else:
            lb_log.warning("not just exist")
            just_exist_reservation = get_data_by_id("reservation", id)
        lb_log.warning(just_exist_reservation)
        len_weighings = len(just_exist_reservation["weighings"])
        lb_log.warning(f"weighings: {len_weighings}")
        if just_exist_reservation["idVehicle"] is not None and reservation_to_update["idVehicle"] is not None:
            if len_weighings > 0 and reservation_to_update["idVehicle"] != just_exist_reservation["idVehicle"]:
                raise HTTPException(status_code=400, detail="Non è possibile modificare la targa dopo che è stata effettuata la prima pesata")
        if reservation_to_update["number_weighings"]:
            if reservation_to_update["number_weighings"] < len_weighings:
                raise HTTPException(status_code=400, detail=f"Il numero di pesate ({body.number_weighings}) non può essere inferiore alle pesate effettuate ({len_weighings})")
            if reservation_to_update["number_weighings"] == len_weighings:
                reservation_to_update["status"] = ReservationStatus.CLOSED
            elif reservation_to_update["number_weighings"] > len_weighings and just_exist_reservation["status"] == ReservationStatus.CLOSED:
                reservation_to_update["status"] = ReservationStatus.ENTERED
        if body.subject.id in [None, -1] and body.subject.social_reason and get_data_by_attribute("subject", "social_reason", body.subject.social_reason):
            raise HTTPException(status_code=400, detail=f"Soggetto con ragione sociale '{body.subject.social_reason}' già esistente")
        if body.subject.id in [None, -1] and body.subject.cfpiva and get_data_by_attribute("subject", "cfpiva", body.subject.cfpiva):
            raise HTTPException(status_code=400, detail=f"Soggetto con CF/P.Iva '{body.subject.cfpiva}' già esistente")
        if body.vector.id in [None, -1] and body.vector.social_reason and get_data_by_attribute("vector", "social_reason", body.vector.social_reason):
            raise HTTPException(status_code=400, detail=f"Vettore con ragione sociale '{body.vector.social_reason}' già esistente")
        if body.vector.id in [None, -1] and body.vector.cfpiva and get_data_by_attribute("vector", "cfpiva", body.vector.cfpiva):
            raise HTTPException(status_code=400, detail=f"Vettore con CF/P.Iva '{body.vector.cfpiva}' già esistente")
        if body.driver.id in [None, -1] and body.driver.social_reason:
            lb_log.warning("ijbwefo3bob")
            del body.driver.id
            if get_data_by_attributes("driver", body.driver.dict()):
                raise HTTPException(status_code=400, detail=f"Autista già registrato")
        if body.vehicle.id in [None, -1] and body.vehicle.plate and get_data_by_attribute("vehicle", "plate", body.vehicle.plate):
            raise HTTPException(status_code=400, detail=f"Veicolo con targa '{body.vehicle.plate}' già esistente")
        del body.subject.id
        if reservation_to_update["idSubject"] in [None, -1] and has_non_none_value(body.subject.dict()):
            data = add_data("subject", body.subject.dict())
            subject = Subject(**data)
            await self.broadcastAddAnagrafic("subject", {"subject": subject.json()})
            reservation_to_update["idSubject"] = subject.id
        del body.vector.id
        if reservation_to_update["idVector"] in [None, -1] and has_non_none_value(body.vector.dict()):
            data = add_data("vector", body.vector.dict())
            vector = Vector(**data)
            await self.broadcastAddAnagrafic("vector", {"vector": vector.json()})
            reservation_to_update["idVector"] = vector.id
        del body.driver.id
        if reservation_to_update["idDriver"] in [None, -1] and has_non_none_value(body.driver.dict()):
            lb_log.warning(body.driver)
            data = add_data("driver", body.driver.dict())
            driver = Driver(**data)
            await self.broadcastAddAnagrafic("driver", {"driver": driver.json()})
            reservation_to_update["idDriver"] = driver.id
        del body.vehicle.id
        if reservation_to_update["idVehicle"] in [None, -1] and has_non_none_value(body.vehicle.dict()):
            data = add_data("vehicle", body.vehicle.dict())
            vehicle = Vehicle(**data)
            await self.broadcastAddAnagrafic("vehicle", {"vehicle": vehicle.json()})
            reservation_to_update["idVehicle"] = vehicle.id
        data = update_data("reservation", id, reservation_to_update)
        reservation = Reservation(**data).json()
        await self.broadcastUpdateAnagrafic("reservation", {"reservation": reservation})
        return reservation

    async def deleteReservation(self, id: int, websocket: StringWebSocket = None):
        try:
            if websocket and websocket not in manager_anagrafics["subject"].active_connections:
                raise HTTPException(status_code=400, detail="Websocket need to be registered in the list of active connections")
            data = delete_data("reservation", id)
            await self.broadcastDeleteAnagrafic("reservation", {"reservation": Reservation(**data).json()})
            return data
        except Exception as e:
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)

    async def deleteAllReservations(self):
        try:
            deleted_count = delete_all_data("reservation")
            await self.broadcastDeleteAnagrafic("reservation", None)
            return {
                "deleted_count": deleted_count,
            }
        except Exception as e:
            status_code = getattr(e, 'status_code', 500)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)
        
    async def deleteLastWeighing(self, id: int, websocket: StringWebSocket = None):
        try:
            if websocket and websocket not in manager_anagrafics["reservation"].active_connections:
                raise HTTPException(status_code=400, detail="Websocket need to be registered in the list of active connections")
            weighing_deleted = delete_last_weighing_of_reservation(id)
            data = get_data_by_id("reservation", id)
            number_weighings_executed = len(data["weighings"])
            if number_weighings_executed < data["number_weighings"] and number_weighings_executed > 0:
                data = update_data("reservation", id, {"status": ReservationStatus.ENTERED})
            elif number_weighings_executed < data["number_weighings"] and number_weighings_executed == 0:
                data = update_data("reservation", id, {"status": ReservationStatus.WAITING})
            reservation = Reservation(**data).json()
            await self.broadcastDeleteAnagrafic("reservation", {"weighing": reservation})
            return reservation
        except Exception as e:
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)