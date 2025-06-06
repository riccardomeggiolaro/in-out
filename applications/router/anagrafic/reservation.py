from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from typing import Dict, Union, Optional
from modules.md_database.md_database import ReservationStatus, LockRecordType
from modules.md_database.interfaces.reservation import Reservation, AddReservationDTO, SetReservationDTO
from modules.md_database.functions.delete_data import delete_data
from modules.md_database.functions.delete_all_data import delete_all_data
from modules.md_database.functions.get_list_reservations import get_list_reservations
from modules.md_database.functions.get_data_by_id import get_data_by_id
from modules.md_database.functions.get_data_by_attributes import get_data_by_attributes
from modules.md_database.functions.delete_last_weighing_of_reservation import delete_last_weighing_of_reservation
from modules.md_database.functions.add_reservation import add_reservation
from modules.md_database.functions.update_reservation import update_reservation
from modules.md_database.functions.update_data import update_data
from modules.md_database.functions.unlock_record_by_id import unlock_record_by_id
from applications.utils.utils import get_query_params
from applications.router.anagrafic.web_sockets import WebSocket
from applications.router.anagrafic.panel_siren.router import PanelSirenRouter
from datetime import datetime
import pandas as pd
from io import BytesIO

class ReservationRouter(WebSocket, PanelSirenRouter):
    def __init__(self):
        super().__init__()
        
        self.router = APIRouter()
        
        self.router.add_api_route('/list', self.getListReservations, methods=['GET'])
        self.router.add_api_route('/export/xlsx', self.exportListReservationsXlsx, methods=['GET'])
        self.router.add_api_route('', self.addReservation, methods=['POST'])
        self.router.add_api_route('/{id}', self.setReservation, methods=['PATCH'])
        self.router.add_api_route('/{id}', self.deleteReservation, methods=['DELETE'])
        self.router.add_api_route('', self.deleteAllReservations, methods=['DELETE'])
        self.router.add_api_route('/last-weighing/{id}', self.deleteLastWeighing, methods=['DELETE'])
        self.router.add_api_route('/call/{id}', self.callReservation, methods=["GET"])
        self.router.add_api_route('/cancel-call/{id}', self.cancelCallReservation, methods=["GET"])
        
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
                "total_rows": total_rows,
                "buffer": self.buffer
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")
        
    async def exportListReservationsXlsx(self, query_params: Dict[str, Union[str, int]] = Depends(get_query_params), limit: Optional[int] = None, offset: Optional[int] = None, fromDate: Optional[datetime] = None, toDate: Optional[datetime] = None):
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
            # 1. Prepariamo il foglio "Prenotazioni"
            reservations_list = []
            weighings_list = []

            for res in data:
                reservations_list.append({
                    "ID": res.id,
                    "Data creazione": res.date_created,
                    "Stato": res.status,
                    "Targa": res.vehicle.plate if res.vehicle else None,
                    "Cliente/Vettore": res.subject.social_reason if res.subject else None,
                    "Numero pesate": res.number_weighings,
                    "Note": res.note
                })

                for idx, w in enumerate(res.weighings, start=1):
                    weighings_list.append({
                        "ID Prenotazione": res.id,
                        "Numero pesata": idx,
                        "Data pesata": w.date,
                        "Peso (kg)": w.weight,
                        "Operatore": w.weigher,
                        "Codice pesata": w.pid
                    })

            # 2. Creiamo DataFrame
            df_reservations = pd.DataFrame(reservations_list)
            df_weighings = pd.DataFrame(weighings_list)

            # 3. Scriviamo su file Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_reservations.to_excel(writer, sheet_name="Prenotazioni", index=False)
                df_weighings.to_excel(writer, sheet_name="Pesate", index=False)

            output.seek(0)
            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=prenotazioni.xlsx"}
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")
       
    async def addReservation(self, body: AddReservationDTO):
        try:
            if not body.vehicle.id and not body.vehicle.plate:
                raise HTTPException(status_code=400, detail="E' necessario l'inserimento di una targa")

            body.subject.id = body.subject.id if body.subject.id not in [None, -1] else None
            body.vector.id = body.vector.id if body.vector.id not in [None, -1] else None
            body.driver.id = body.driver.id if body.driver.id not in [None, -1] else None
            body.vehicle.id = body.vehicle.id if body.vehicle.id not in [None, -1] else None

            data = add_reservation(body)

            get_reservation_data = get_data_by_id("reservation", data["id"])

            reservation = Reservation(**get_reservation_data)
            await self.broadcastAddAnagrafic("reservation", {"reservation": reservation.json()})
            if not body.subject.id and reservation.idSubject:
                await self.broadcastAddAnagrafic("subject", {"subject": reservation.subject.json()})
            if not body.vector.id and reservation.idVector:
                await self.broadcastAddAnagrafic("vector", {"vector": reservation.vector.json()})
            if not body.driver.id and reservation.idDriver:
                await self.broadcastAddAnagrafic("driver", {"driver": reservation.driver.json()})
            if not body.vehicle.id and reservation.idVehicle:
                await self.broadcastAddAnagrafic("vehicle", {"vehicle": reservation.vehicle.json()})
            return reservation
        except Exception as e:
            # Verifica se l'eccezione ha un attributo 'status_code' e usa quello, altrimenti usa 404
            status_code = getattr(e, 'status_code', 400)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)

    async def setReservation(self, request: Request, id: int, body: SetReservationDTO):
        locked_data = None
        try:
            locked_data = get_data_by_attributes('lock_record', {"table_name": "reservation", "idRecord": id, "type": LockRecordType.UPDATE, "user_id": request.state.user.id})
            if not locked_data:
                raise HTTPException(status_code=403, detail=f"You need to block the reservation with id '{id}' before to update that")
            data = update_reservation(id, body)
            get_reservation_data = get_data_by_id("reservation", data["id"])
            reservation = Reservation(**get_reservation_data)
            await self.broadcastUpdateAnagrafic("reservation", {"reservation": reservation.json()})
            if body.subject.id in [None, -1] and reservation.idSubject:
                await self.broadcastAddAnagrafic("subject", {"subject": reservation.subject.json()})
            if body.vector.id in [None, -1] and reservation.idVector:
                await self.broadcastAddAnagrafic("vector", {"vector": reservation.vector.json()})
            if body.driver.id in [None, -1] and reservation.idDriver:
                await self.broadcastAddAnagrafic("driver", {"driver": reservation.driver.json()})
            if body.vehicle.id in [None, -1] and reservation.idVehicle:
                await self.broadcastAddAnagrafic("vehicle", {"vehicle": reservation.vehicle.json()})
            return reservation
        except Exception as e:
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            if status_code == 400:
                locked_data = None
            raise HTTPException(status_code=status_code, detail=detail)
        finally:
            if locked_data:
                unlock_record_by_id(locked_data["id"])

    async def deleteReservation(self, request: Request, id: int):
        locked_data = None
        try:
            locked_data = get_data_by_attributes('lock_record', {"table_name": "reservation", "idRecord": id, "type": LockRecordType.DELETE, "user_id": request.state.user.id})
            if not locked_data:
                raise HTTPException(status_code=403, detail=f"You need to block the reservation with id '{id}' before to update that")
            check_reservation_weighings = get_data_by_id("reservation", id)
            if check_reservation_weighings and len(check_reservation_weighings["weighings"]) > 0:
                raise HTTPException(status_code=400, detail=f"La prenotazione con id '{id}' è assegnata a delle pesate salvate")
            data = delete_data("reservation", id)
            await self.broadcastDeleteAnagrafic("reservation", {"reservation": Reservation(**data).json()})
            return data
        except Exception as e:
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)
        finally:
            if locked_data:
                unlock_record_by_id(locked_data["id"])

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
        
    async def deleteLastWeighing(self, request: Request, id: int):
        locked_data = None
        try:
            locked_data = get_data_by_attributes('lock_record', {"table_name": "reservation", "idRecord": id, "type": LockRecordType.DELETE, "user_id": request.state.user.id})
            if not locked_data:
                raise HTTPException(status_code=403, detail=f"You need to block the reservation with id '{id}' before to delete its last weighing")
            delete_last_weighing_of_reservation(id)
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
        finally:
            if locked_data:
                unlock_record_by_id(locked_data["id"])
        
    async def callReservation(self, request: Request, id: int):
        locked_data = None
        try:
            locked_data = get_data_by_attributes('lock_record', {"table_name": "reservation", "idRecord": id, "type": LockRecordType.CALL, "user_id": request.state.user.id})
            if not locked_data:
                raise HTTPException(status_code=403, detail=f"You need to block the reservation with id '{id}' before to delete its last weighing")
            data = get_data_by_id("reservation", id)
            if data["status"] not in [ReservationStatus.WAITING, ReservationStatus.CALLED]:
                raise HTTPException(status_code=400, detail=f"La targa '{data['vehicle']['plate']}' della prenotazione con id '{id}' ha già effettuato una pesata")
            elif data["vehicle"]["plate"] in self.buffer:
                raise HTTPException(status_code=400, detail=f"La targa '{data['vehicle']['plate']}' della prenotazione con id '{id}' è già presente nel buffer")
            edit_buffer = await self.sendMessagePanel(data["vehicle"]["plate"])
            await self.sendMessageSiren()
            data = update_data("reservation", id, {"status": ReservationStatus.CALLED})
            reservation = Reservation(**data).json()
            await self.broadcastCallAnagrafic("reservation", {"reservation": reservation})
            return edit_buffer
        except Exception as e:
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)
        finally:
            if locked_data:
                unlock_record_by_id(locked_data["id"])
    
    async def cancelCallReservation(self, request: Request, id: int):
        locked_data = None
        try:
            locked_data = get_data_by_attributes('lock_record', {"table_name": "reservation", "idRecord": id, "type": LockRecordType.CANCEL_CALL, "user_id": request.state.user.id})
            if not locked_data:
                raise HTTPException(status_code=403, detail=f"You need to block the reservation with id '{id}' before to delete its last weighing")
            data = get_data_by_id("reservation", id)
            if data["status"] != ReservationStatus.CALLED:
                raise HTTPException(status_code=400, detail="Il mezzo non è ancora stato chiamato")
            elif data["vehicle"]["plate"] not in self.buffer:
                raise HTTPException(status_code=400, detail=f"La targa '{data['vehicle']['plate']}' della prenotazione con id '{id}' non è presente nel buffer")
            undo_buffer = await self.deleteMessagePanel(data["vehicle"]["plate"])
            data = update_data("reservation", id, {"status": ReservationStatus.WAITING})
            reservation = Reservation(**data).json()
            await self.broadcastCallAnagrafic("reservation", {"reservation": reservation})
            return undo_buffer
        except Exception as e:
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)
        finally:
            if locked_data:
                unlock_record_by_id(locked_data["id"])