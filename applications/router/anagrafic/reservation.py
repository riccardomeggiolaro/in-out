from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from typing import Dict, Union, Optional
from modules.md_database.md_database import ReservationStatus, LockRecordType, TypeReservation
from modules.md_database.interfaces.reservation import Reservation, AddReservationDTO, SetReservationDTO
from modules.md_database.functions.delete_data import delete_data
from modules.md_database.functions.delete_all_data import delete_all_data
from modules.md_database.functions.get_list_reservations import get_list_reservations
from modules.md_database.functions.get_list_in_out import get_list_in_out
from modules.md_database.functions.get_list_weighings import get_list_weighings
from modules.md_database.functions.get_data_by_id import get_data_by_id
from modules.md_database.functions.get_data_by_attributes import get_data_by_attributes
from modules.md_database.functions.delete_last_weighing_of_reservation import delete_last_weighing_of_reservation
from modules.md_database.functions.add_reservation import add_reservation
from modules.md_database.functions.update_reservation import update_reservation
from modules.md_database.functions.update_data import update_data
from modules.md_database.functions.unlock_record_by_id import unlock_record_by_id
from modules.md_database.functions.get_reservation_by_id import get_reservation_by_id
from modules.md_database.functions.get_last_in_out_by_weigher import get_last_in_out_by_weigher
from modules.md_database.functions.get_in_out_by_id import get_last_in_out_by_id
from applications.utils.utils import get_query_params
from applications.utils.utils_weigher import get_query_params_name_node, InstanceNameWeigherDTO
from applications.utils.utils_report import find_file_in_directory
from applications.router.anagrafic.web_sockets import WebSocket
from applications.router.anagrafic.panel_siren.router import PanelSirenRouter
from applications.router.weigher.manager_weighers_data import broadcastMessageWebSocket
from datetime import datetime
import pandas as pd
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import libs.lb_config as lb_config
from libs.lb_printer import printer
from applications.utils.utils_report import get_data_variables, generate_html_report, save_file_dir

class ReservationRouter(WebSocket, PanelSirenRouter):
    def __init__(self):
        super().__init__()
        
        self.router = APIRouter()
        
        self.router.add_api_route('/list', self.getListReservations, methods=['GET'])
        self.router.add_api_route('/in-out/list', self.getListInOut, methods=['GET'])
        self.router.add_api_route('/in-out/pdf/{id}', self.pdfInOut, methods=['GET'])
        self.router.add_api_route('/in-out/print-last', self.printLastInOut, methods=['GET'])
        self.router.add_api_route('/weighing/list', self.getListWeighing, methods=['GET'])
        self.router.add_api_route('/export/xlsx', self.exportListReservationsXlsx, methods=['GET'])
        self.router.add_api_route('/export/pdf', self.exportListReservationsPdf, methods=['GET'])
        self.router.add_api_route('', self.addReservation, methods=['POST'])
        self.router.add_api_route('/{id}', self.setReservation, methods=['PATCH'])
        self.router.add_api_route('/{id}', self.deleteReservation, methods=['DELETE'])
        self.router.add_api_route('', self.deleteAllReservations, methods=['DELETE'])
        self.router.add_api_route('/last-weighing/{id}', self.deleteLastWeighing, methods=['DELETE'])
        self.router.add_api_route('/call/{id}', self.callReservation, methods=["GET"])
        self.router.add_api_route('/cancel-call/{id}', self.cancelCallReservation, methods=["GET"])
        
    async def getListReservations(self, query_params: Dict[str, Union[str, int]] = Depends(get_query_params), limit: Optional[int] = None, offset: Optional[int] = None, fromDate: Optional[datetime] = None, toDate: Optional[datetime] = None, excludeTestWeighing = False, permanent: Optional[bool] = None):
        try:
            not_closed = False
            if "status" in query_params and query_params["status"] == "NOT_CLOSED":
                not_closed = True                
                del query_params["status"]
            if fromDate is not None:
                del query_params["fromDate"]
            if toDate is not None:
                toDate = toDate.replace(hour=23, minute=59, second=59, microsecond=999999)
                del query_params["toDate"]
            if limit is not None:
                del query_params["limit"]
            if offset is not None:
                del query_params["offset"]
            if "excludeTestWeighing" in query_params:
                del query_params["excludeTestWeighing"]
            if "permanent" in query_params:
                del query_params["permanent"]
            data, total_rows = get_list_reservations(query_params, not_closed, fromDate, toDate, limit, offset, ('date_created', 'desc'), excludeTestWeighing, permanent, True)
            return {
                "data": data,
                "total_rows": total_rows,
                "buffer": self.buffer
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")
        
    async def getListInOut(self, query_params: Dict[str, Union[str, int]] = Depends(get_query_params), limit: Optional[int] = None, offset: Optional[int] = None, fromDate: Optional[datetime] = None, toDate: Optional[datetime] = None, excludeTestWeighing = False):
        try:
            not_closed = False
            
            # Handle status filter
            if "status" in query_params and query_params["status"] == "NOT_CLOSED":
                not_closed = True                
                del query_params["status"]
                
            # Handle limit and offset
            if "limit" in query_params:
                del query_params["limit"]
            if "offset" in query_params:
                del query_params["offset"]
                
            # Handle date query_params for weights
            if fromDate is not None:
                del query_params["fromDate"]
                
            if toDate is not None:
                toDate = toDate.replace(hour=23, minute=59, second=59, microsecond=999999)
                del query_params["toDate"]

            if "excludeTestWeighing" in query_params:
                del query_params["excludeTestWeighing"]
                
            # Call get_list_in_out with prepared query_params
            data, total_rows = get_list_in_out(
                filters=query_params,
                not_closed=not_closed,
                fromDate=fromDate,
                toDate=toDate,
                limit=limit,
                offset=offset,
                order_by=('id', 'desc'),
                excludeTestWeighing=excludeTestWeighing,
                get_is_last=True
            )
            
            return {
                "data": data,
                "total_rows": total_rows,
                "buffer": self.buffer
            }
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")

    async def pdfInOut(self, id: int):
        in_out = get_last_in_out_by_id(id)
        report_dir = lb_config.g_config["app_api"]["path_report"]
        name_file, variables, report = get_data_variables(in_out)
        html = generate_html_report(report_dir, report, v=variables.dict())
        pdf = printer.generate_pdf_from_html(html_content=html)
        return StreamingResponse(
            BytesIO(pdf),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={name_file}"}
        )

    async def printLastInOut(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
        path_pdf = lb_config.g_config["app_api"]["path_pdf"]
        report_dir = lb_config.g_config["app_api"]["path_report"]
        printer_name = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["printer_name"]
        number_of_prints = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["number_of_prints"]
        in_out = get_last_in_out_by_weigher(weigher_name=instance.weigher_name)
        if not in_out:
            raise HTTPException(status_code=404, detail="Pesata non esistente")
        name_file, variables, report = get_data_variables(in_out)
        file = find_file_in_directory(path_pdf, name_file)
        if not file:
            html = generate_html_report(report_dir, report, v=variables.dict())
            pdf = printer.generate_pdf_from_html(html_content=html)
            save_file_dir(path_pdf, name_file, pdf)
            file = find_file_in_directory(path_pdf, name_file)
        job_id, message1, message2 = printer.print_pdf(file, printer_name, number_of_prints)
        if not job_id:
            raise HTTPException(status_code=404, detail=f"{message1} {message2}")
        return { "message": message2 }
    
    async def getListWeighing(self, query_params: Dict[str, Union[str, Union[str, int]]] = Depends(get_query_params), weigher_name: Optional[str] = None, limit: Optional[int] = None, offset: Optional[int] = None, fromDate: Optional[datetime] = None, toDate: Optional[datetime] = None):
        try:
            # Handle weigher_name
            if "weigher_name" in query_params:
                del query_params["weigher_name"]

            # Handle limit and offset
            if "limit" in query_params:
                del query_params["limit"]
            if "offset" in query_params:
                del query_params["offset"]
                
            # Handle date query_params for weights
            if fromDate is not None:
                del query_params["fromDate"]
                
            if toDate is not None:
                toDate = toDate.replace(hour=23, minute=59, second=59, microsecond=999999)
                del query_params["toDate"]

            # Call get_list_in_out with prepared query_params
            data, total_rows = get_list_weighings(
                filters=query_params,
                weigher_name=weigher_name,
                fromDate=fromDate,
                toDate=toDate,
                limit=limit,
                offset=offset,
                order_by=('id', 'desc'),
            )
            
            return {
                "data": data,
                "total_rows": total_rows,
                "buffer": self.buffer
            }
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")
        
    async def exportListReservationsXlsx(self, query_params: Dict[str, Union[str, int]] = Depends(get_query_params), 
                                   limit: Optional[int] = None, offset: Optional[int] = None,
                                   fromDate: Optional[datetime] = None, toDate: Optional[datetime] = None,
                                   excludeTestWeighing: bool = False, filterDateReservation: bool = False):
        try:
            not_closed = False
            filters = query_params.copy()
            
            # Handle status filter
            if "status" in filters and filters["status"] == "NOT_CLOSED":
                not_closed = True                
                del filters["status"]
                
            # Handle limit and offset
            if "limit" in filters:
                del filters["limit"]
            if "offset" in filters:
                del filters["offset"]
                
            # Handle date filters
            if fromDate is not None:
                del filters["fromDate"]
                
            if toDate is not None:
                toDate = toDate.replace(hour=23, minute=59, second=59, microsecond=999999)
                del filters["toDate"]

            if "excludeTestWeighing" in query_params:
                del filters["excludeTestWeighing"]

            if "filterDateReservation" in query_params:
                del filters["filterDateReservation"]

            data, total_rows = get_list_in_out(
                filters=filters,
                not_closed=not_closed,
                fromDate=fromDate,
                toDate=toDate,
                limit=limit,
                offset=offset,
                order_by=('reservation.date_created', 'desc'),
                excludeTestWeighing=excludeTestWeighing,
                filterDateReservation=filterDateReservation
            )

            # Prepara lista per export
            in_out_list = []
            for inout in data:
                weight1 = inout.weight1.weight if inout.weight1 else None
                if weight1 is None and inout.weight2 and inout.weight2.tare > 0:
                    weight1 = inout.weight2.tare
                in_out_list.append({
                    "Targa": inout.reservation.vehicle.plate if inout.reservation.vehicle else None,
                    "Cliente/Fornitore": inout.reservation.subject.social_reason if inout.reservation.subject else None,
                    "Vettore": inout.reservation.vector.social_reason if inout.reservation.vector else None,
                    "Note": inout.reservation.note,
                    "Referenza documento": inout.reservation.document_reference,
                    "Materiale": inout.material.description if inout.material else None,
                    "Data 1": datetime.strftime(inout.weight1.date, "%d-%m-%Y %H:%M") if inout.weight1 else None,
                    "Data 2": datetime.strftime(inout.weight2.date, "%d-%m-%Y %H:%M") if inout.weight2 else None,
                    "Pid 1": inout.weight1.pid if inout.weight1 else None,
                    "Pid 2": inout.weight2.pid if inout.weight2 else None,
                    "Peso 1 (kg)": weight1,
                    "Peso 2 (kg)": inout.weight2.weight if inout.weight2 else None,
                    "Netto (kg)": inout.net_weight if inout.net_weight is not None else None
                })

            # Crea DataFrame e esporta
            df = pd.DataFrame(in_out_list)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name="Pesate", index=False)

            output.seek(0)
            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=pesate.xlsx"}
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")

    async def exportListReservationsPdf(self, query_params: Dict[str, Union[str, int]] = Depends(get_query_params), 
                                      limit: Optional[int] = None, offset: Optional[int] = None,
                                      fromDate: Optional[datetime] = None, toDate: Optional[datetime] = None,
                                      excludeTestWeighing: bool = False, filterDateReservation: bool = False):
        try:
            not_closed = False
            filters = query_params.copy()
            
            # Handle status filter
            if "status" in filters and filters["status"] == "NOT_CLOSED":
                not_closed = True                
                del filters["status"]
                
            # Handle limit and offset
            if "limit" in filters:
                del filters["limit"]
            if "offset" in filters:
                del filters["offset"]
                
            # Handle date filters
            if fromDate is not None:
                del filters["fromDate"]
                
            if toDate is not None:
                toDate = toDate.replace(hour=23, minute=59, second=59, microsecond=999999)
                del filters["toDate"]

            # Prima di chiamare get_list_in_out
            if "excludeTestWeighing" in filters:
                del filters["excludeTestWeighing"]

            if "filterDateReservation" in query_params:
                del filters["filterDateReservation"]

            data, total_rows = get_list_in_out(
                filters=filters,
                not_closed=not_closed,
                fromDate=fromDate,
                toDate=toDate,
                limit=limit,
                offset=offset,
                order_by=('reservation.date_created', 'desc'),
                excludeTestWeighing=excludeTestWeighing,
                filterDateReservation=filterDateReservation
            )

            # Create PDF with smaller margins
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, 
                                  pagesize=A4, 
                                  leftMargin=15,  # Reduced margins
                                  rightMargin=15,
                                  topMargin=15,
                                  bottomMargin=15)
            story = []

            # Add title with smaller spacing
            styles = getSampleStyleSheet()
            title = Paragraph("Lista Pesate", styles['Heading2'])  # Smaller heading
            story.append(title)
            story.append(Spacer(1, 0.2*inch))  # Reduced spacing

            # Define table properties with smaller font
            common_font_size = 6  # Reduced font size
            header_color = colors.grey

            # Define headers and column widths
            headers = ['Targa', 'Cliente/Forn.', 'Vettore', 'Note', 'Ref.Doc', 'Materiale',
                      'Data 1', 'Data 2', 'Pid 1', 'Pid 2', 'Peso 1 (kg)', 'Peso 2 (kg)', 'Netto (kg)']
            
            # Updated widths to accommodate the new material column (reduced some widths to maintain A4 fit)
            col_widths = [30, 55, 55, 55, 46, 46, 46, 46, 46, 46, 38, 38, 38]  

            # Create table style with compact formatting
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), header_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), common_font_size),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),  # Reduced padding
                ('TOPPADDING', (0, 0), (-1, -1), 4),     # Reduced padding
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  # Thinner grid
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ])

            # Prepare table data with compact date format
            table_data = [headers]
            for inout in data:
                weight1 = inout.weight1.weight if inout.weight1 else None
                if weight1 is None and inout.weight2 and inout.weight2.tare > 0:
                    weight1 = inout.weight2.tare

                # Use shorter date format
                date1 = datetime.strftime(inout.weight1.date, "%d-%m-%y %H:%M") if inout.weight1 else None
                date2 = datetime.strftime(inout.weight2.date, "%d-%m-%y %H:%M") if inout.weight2 else None

                # Update row data to include material
                row = [
                    str(inout.reservation.vehicle.plate if inout.reservation.vehicle else '')[:6],      # Targa (32)
                    str(inout.reservation.subject.social_reason if inout.reservation.subject else '')[:18],  # Cliente (50)
                    str(inout.reservation.vector.social_reason if inout.reservation.vector else '')[:18],    # Vettore (50)
                    str(inout.reservation.note or '')[:18],                                             # Note (50)
                    str(inout.reservation.document_reference or '')[:12],                               # Ref.Doc (45)
                    str(inout.material.description if inout.material else '')[:12],               # Materiale (45)
                    date1,                                                                              # Data 1 (47)
                    date2,                                                                              # Data 2 (47)
                    str(inout.weight1.pid if inout.weight1 else '')[:12],                              # P1 (43)
                    str(inout.weight2.pid if inout.weight2 else '')[:12],                              # P2 (43)
                    str(weight1) if weight1 is not None else '',                                        # Peso 1 (28)
                    str(inout.weight2.weight) if inout.weight2 else '',                                # Peso 2 (28)
                    str(inout.net_weight) if inout.net_weight is not None else ''                      # Netto (28)
                ]
                table_data.append(row)

            # Create and style table
            t = Table(table_data, colWidths=col_widths, repeatRows=1)
            t.setStyle(table_style)
            story.append(t)

            # Build PDF
            doc.build(story)
            buffer.seek(0)

            return StreamingResponse(
                buffer,
                media_type="application/pdf",
                headers={"Content-Disposition": "attachment; filename=pesate.pdf"}
            )
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")

    async def addReservation(self, request: Request, body: AddReservationDTO):
        try:
            if request and not body.vehicle.id and not body.vehicle.plate:
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

            await broadcastMessageWebSocket({"reservation": {}})

            return reservation
        except Exception as e:
            # Verifica se l'eccezione ha un attributo 'status_code' e usa quello, altrimenti usa 404
            status_code = getattr(e, 'status_code', 400)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)

    async def setReservation(self, request: Request, id: int, body: SetReservationDTO, idInOut: Optional[int] = None):
        locked_data = None
        try:
            if request:
                locked_data = get_data_by_attributes('lock_record', {"table_name": "reservation", "idRecord": id, "type": LockRecordType.UPDATE, "user_id": request.state.user.id})
                if not locked_data:
                    raise HTTPException(status_code=403, detail=f"You need to block the reservation with id '{id}' before to update that")
            data = update_reservation(id, body, idInOut)
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

            await broadcastMessageWebSocket({"reservation": {}})

            return reservation
        except Exception as e:
            status_code = getattr(e, 'status_code', 400)
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
            if request:
                locked_data = get_data_by_attributes('lock_record', {"table_name": "reservation", "idRecord": id, "type": LockRecordType.DELETE, "user_id": request.state.user.id})
                if not locked_data:
                    raise HTTPException(status_code=403, detail=f"You need to block the reservation with id '{id}' before to update that")
            check_reservation_weighings = get_data_by_id("reservation", id)
            if check_reservation_weighings and len(check_reservation_weighings["in_out"]) > 0:
                raise HTTPException(status_code=400, detail=f"La prenotazione con id '{id}' è assegnata a delle pesate salvate")
            data = delete_data("reservation", id)
            await self.broadcastDeleteAnagrafic("reservation", {"reservation": Reservation(**data).json()})

            await broadcastMessageWebSocket({"reservation": {}})

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

            await broadcastMessageWebSocket({"reservation": {}})

            return {
                "deleted_count": deleted_count,
            }
        except Exception as e:
            status_code = getattr(e, 'status_code', 500)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)
        
    async def deleteLastWeighing(self, request: Request, id: int, deleteReservationIfislastInOut: Optional[bool] = False):
        locked_data = None
        try:
            locked_data = get_data_by_attributes('lock_record', {"table_name": "reservation", "idRecord": id, "type": LockRecordType.DELETE, "user_id": request.state.user.id})
            if not locked_data:
                raise HTTPException(status_code=403, detail=f"You need to block the reservation with id '{id}' before to delete its last weighing")
            delete_last_weighing_of_reservation(id)
            data = get_reservation_by_id(id)
            if data:
                number_in_out_executed = len(data.in_out)
                if number_in_out_executed > 0:
                    data = update_data("reservation", id, {"status": ReservationStatus.ENTERED})
                else:
                    if deleteReservationIfislastInOut and lb_config.g_config["app_api"]["use_reservation"] == False and data.type != TypeReservation.RESERVATION:
                        data = delete_data("reservation", id)
                    else:
                        data = update_data("reservation", id, {"status": ReservationStatus.WAITING})
                reservation = Reservation(**data).json()
                await self.broadcastDeleteAnagrafic("reservation", {"weighing": reservation})

                await broadcastMessageWebSocket({"reservation": {}})

                return reservation
            # else:
            #     await self.broadcastDeleteAnagrafic("reservation", {"weighing": reservation})
            return None
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
