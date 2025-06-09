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
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

class ReservationRouter(WebSocket, PanelSirenRouter):
    def __init__(self):
        super().__init__()
        
        self.router = APIRouter()
        
        self.router.add_api_route('/list', self.getListReservations, methods=['GET'])
        self.router.add_api_route('/export/xlsx', self.exportListReservationsXlsx, methods=['GET'])
        self.router.add_api_route('/export/pdf', self.exportListReservationsPdf, methods=['GET'])
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
                    "Data creazione": datetime.strftime(res.date_created, "%d-%m-%Y %M:%H"),
                    "Stato": res.status.value,
                    "Numero pesate": f"{len(res.weighings)}/{res.number_weighings}",
                    "Targa": res.vehicle.plate if res.vehicle else None,
                    "Cliente/Fornitore": res.subject.social_reason if res.subject else None,
                    "Vettore": res.vector.social_reason if res.vector else None,
                    "Note": res.note,
                    "Referenza documento": res.document_reference
                })

                for idx, w in enumerate(res.weighings, start=1):
                    weighings_list.append({
                        "ID Accesso": res.id,
                        "Data pesata": datetime.strftime(w.date, "%d-%m-%Y %M:%H"),
                        "Pesa": w.weigher,
                        "Peso (kg)": w.weight,
                        "Codice pesata": w.pid,
                        "Tipo": w.type.value
                    })

            # 2. Creiamo DataFrame
            df_reservations = pd.DataFrame(reservations_list)
            df_weighings = pd.DataFrame(weighings_list)

            # 3. Scriviamo su file Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_reservations.to_excel(writer, sheet_name="Accessi", index=False)
                df_weighings.to_excel(writer, sheet_name="Pesate", index=False)

            output.seek(0)
            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=prenotazioni.xlsx"}
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")

    async def exportListReservationsPdf(self, query_params: Dict[str, Union[str, int]] = Depends(get_query_params), 
                                    limit: Optional[int] = None, offset: Optional[int] = None, 
                                    fromDate: Optional[datetime] = None, toDate: Optional[datetime] = None):
        try:
            # Get data using the same logic as before
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
                
            data, total_rows = get_list_reservations(query_params, not_closed, fromDate, toDate, 
                                                limit, offset, ('date_created', 'desc'))

            # Create PDF buffer
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=30, rightMargin=30)
            story = []

            # Calculate available width
            page_width = A4[0] - 60  # Total width minus left and right margins
            
            # Add title
            styles = getSampleStyleSheet()
            title = Paragraph("Lista Accessi e Pesate", styles['Heading1'])
            story.append(title)
            story.append(Spacer(1, 0.5*inch))

            # Define common style properties
            common_font_size = 8  # Reduced font size for better fit
            header_color = colors.grey
            subheader_color = colors.lightgrey

            # Define table header for reservations
            headers = ['ID', 'Data', 'Stato', 'Targa', 'Cliente/Fornitore', 'Vettore', 'Note', 'Ref. Doc.']
            
            # Calculate dynamic column widths with max-width constraints
            # Define max widths for each column (in points)
            max_widths = [25, 90, 45, 60, 120, 120, 100, 80]  # Total: 700 points
            
            # Scale widths to fit page if needed
            total_max_width = sum(max_widths)
            if total_max_width > page_width:
                scale_factor = page_width / total_max_width
                col_widths = [w * scale_factor for w in max_widths]
            else:
                col_widths = max_widths

            # Function to wrap text to fit in cell
            def wrap_text(text, max_width, font_size=common_font_size):
                if not text:
                    return ""
                # Estimate characters per line based on width and font size
                # Increased multiplier for better estimation
                chars_per_line = int(max_width / (font_size * 0.5))  # More generous estimation
                if len(str(text)) <= chars_per_line:
                    return str(text)
                
                # Break long text into multiple lines
                words = str(text).split()
                lines = []
                current_line = ""
                
                for word in words:
                    test_line = current_line + " " + word if current_line else word
                    # More accurate width calculation
                    if len(test_line) <= chars_per_line:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word
                
                if current_line:
                    lines.append(current_line)
                
                return "\n".join(lines)

            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), header_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), common_font_size),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                # Enable text wrapping
                ('WORDWRAP', (0, 0), (-1, -1), 'WORD'),
                ('SPLITLONGWORDS', (0, 0), (-1, -1), True),
            ])

            for res in data:
                # Create reservation row with wrapped text
                reservation_row = [
                    str(res.id),
                    datetime.strftime(res.date_created, '%d-%m-%Y %H:%M'),  # Kept in single line
                    res.status.value,
                    wrap_text(res.vehicle.plate if res.vehicle else "", col_widths[3]),
                    wrap_text(res.subject.social_reason if res.subject else "", col_widths[4]),
                    wrap_text(res.vector.social_reason if res.vector else "", col_widths[5]),
                    wrap_text(res.note if res.note else "", col_widths[6]),
                    wrap_text(res.document_reference if res.document_reference else "", col_widths[7])
                ]
                
                table_data = [headers, reservation_row]
                t = Table(table_data, colWidths=col_widths, repeatRows=1)
                t.setStyle(table_style)
                story.append(t)
                
                # Add weighings as a sub-table if there are any
                if res.weighings:
                    weighing_headers = ['Data pesata', 'Pesa', 'Peso (kg)', 'Tipo']
                    weighing_data = [weighing_headers]
                    
                    # Calculate weighing table column widths
                    weighing_col_widths = [75, 35, 53, 35]  # Total: 360 points
                    weighing_total = sum(weighing_col_widths)
                    if weighing_total > page_width:
                        weighing_scale = page_width / weighing_total
                        weighing_col_widths = [w * weighing_scale for w in weighing_col_widths]
                    
                    weighing_style = TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), subheader_color),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), common_font_size),
                        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('WORDWRAP', (0, 0), (-1, -1), 'WORD'),
                        ('SPLITLONGWORDS', (0, 0), (-1, -1), True),
                    ])
                    
                    for w in res.weighings:
                        weighing_row = [
                            datetime.strftime(w.date, '%d-%m-%Y %H:%M'),  # Kept in single line
                            wrap_text(str(w.weigher), weighing_col_widths[1]),
                            str(w.weight),
                            w.type.value
                        ]
                        weighing_data.append(weighing_row)
                    
                    w_table = Table(weighing_data, colWidths=weighing_col_widths, repeatRows=1)
                    w_table.setStyle(weighing_style)
                    story.append(Spacer(1, 0.1*inch))
                    story.append(w_table)
                
                story.append(Spacer(1, 0.2*inch))

            # Build PDF
            doc.build(story)
            buffer.seek(0)

            return StreamingResponse(
                buffer,
                media_type="application/pdf",
                headers={"Content-Disposition": "attachment; filename=prenotazioni.pdf"}
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