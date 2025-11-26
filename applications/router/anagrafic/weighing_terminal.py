from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from typing import Dict, Union, Optional
from modules.md_database.md_database import AccessStatus, LockRecordType, TypeAccess
from modules.md_database.interfaces.access import Access, AddAccessDTO, SetAccessDTO
from modules.md_database.interfaces.material import Material
from modules.md_database.interfaces.operator import Operator
from modules.md_database.interfaces.in_out import InOut
from modules.md_database.functions.delete_data import delete_data
from modules.md_database.functions.delete_all_data import delete_all_data
from modules.md_database.functions.get_list_accesses import get_list_accesses
from modules.md_database.functions.get_list_in_out import get_list_in_out
from modules.md_database.functions.get_list_weighings import get_list_weighings
from modules.md_database.functions.get_data_by_id import get_data_by_id
from modules.md_database.functions.get_data_by_attributes import get_data_by_attributes
from modules.md_database.functions.delete_last_weighing_of_access import delete_last_weighing_of_access
from modules.md_database.functions.add_access import add_access
from modules.md_database.functions.update_access import update_access
from modules.md_database.functions.update_data import update_data
from modules.md_database.functions.unlock_record_by_id import unlock_record_by_id
from modules.md_database.functions.get_access_by_id import get_access_by_id
from modules.md_database.functions.get_last_in_out_by_weigher import get_last_in_out_by_weigher
from modules.md_database.functions.get_in_out_by_id import get_in_out_by_id
from modules.md_database.functions.safe_get_attr import safe_get_attr
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
from applications.middleware.writable_user import is_writable_user
import applications.utils.utils as utils
from reportlab.lib.pagesizes import landscape
from modules.md_database.functions.get_list_weighing_from_terminal import get_list_weighing_from_terminal

class WeighingTerminalRouter(WebSocket):
    def __init__(self):
        super().__init__()
        
        self.router = APIRouter()
        
        self.router.add_api_route('/list', self.getListWeighingTerminals, methods=['GET'])
        self.router.add_api_route('/export/xlsx', self.exportListAccessesXlsx, methods=['GET'])
        self.router.add_api_route('/export/pdf', self.exportListAccessesPdf, methods=['GET'])
        self.router.add_api_route('/{id}', self.deleteAccess, methods=['DELETE'], dependencies=[Depends(is_writable_user)])
        
    async def getListWeighingTerminals(self, query_params: Dict[str, Union[str, int]] = Depends(get_query_params), limit: Optional[int] = None, offset: Optional[int] = None, fromDate: Optional[datetime] = None, toDate: Optional[datetime] = None, onlyInOutWithoutWeight2: Optional[bool] = False, onlyInOutWithWeight2: bool = False):
        try:
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

            if "filterDateAccess" in query_params:
                del query_params["filterDateAccess"]

            if "onlyInOutWithWeight2" in query_params:
                del query_params["onlyInOutWithWeight2"]

            if "onlyInOutWithoutWeight2" in query_params:
                del query_params["onlyInOutWithoutWeight2"]
            
            data, total_rows = get_list_weighing_from_terminal(
                filters=query_params, 
                only_in_out_without_weight2=onlyInOutWithoutWeight2,
                only_in_out_with_weight2=onlyInOutWithWeight2,
                fromDate=fromDate, 
                toDate=toDate, 
                limit=limit, 
                offset=offset, 
                order_by=('date_created', 'desc'),
                load_subject=lb_config.g_config["app_api"]["use_anagrafic"]["subject"],
                load_vehicle=lb_config.g_config["app_api"]["use_anagrafic"]["vehicle"],
                load_material=lb_config.g_config["app_api"]["use_anagrafic"]["material"],
                load_note=lb_config.g_config["app_api"]["use_anagrafic"]["note"],
                load_date_weight1=lb_config.g_config["app_api"]["use_anagrafic"]["weight1"]["date"],
                load_pid_weight1=lb_config.g_config["app_api"]["use_anagrafic"]["weight1"]["pid"],
                load_date_weight2=lb_config.g_config["app_api"]["use_anagrafic"]["weight2"]["date"],
                load_pid_weight2=lb_config.g_config["app_api"]["use_anagrafic"]["weight2"]["pid"]
            )

            return {
                "data": data,
                "total_rows": total_rows
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")
        
    async def exportListAccessesXlsx(self, query_params: Dict[str, Union[str, int]] = Depends(get_query_params), limit: Optional[int] = None, offset: Optional[int] = None, fromDate: Optional[datetime] = None, toDate: Optional[datetime] = None, excludeTestWeighing: Optional[bool] = True, onlyInOutWithoutWeight2: Optional[bool] = False, onlyInOutWithWeight2: bool = False):
        try:
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

            if "filterDateAccess" in query_params:
                del query_params["filterDateAccess"]

            if "onlyInOutWithWeight2" in query_params:
                del query_params["onlyInOutWithWeight2"]

            if "onlyInOutWithoutWeight2" in query_params:
                del query_params["onlyInOutWithoutWeight2"]
            
            load_subject = lb_config.g_config["app_api"]["use_anagrafic"]["subject"]
            load_vehicle = lb_config.g_config["app_api"]["use_anagrafic"]["vehicle"]
            load_material = lb_config.g_config["app_api"]["use_anagrafic"]["material"]
            load_note = lb_config.g_config["app_api"]["use_anagrafic"]["note"]
            load_date_weight1 = lb_config.g_config["app_api"]["use_anagrafic"]["weight1"]["date"]
            load_pid_weight1 = lb_config.g_config["app_api"]["use_anagrafic"]["weight1"]["pid"]
            load_date_weight2 = lb_config.g_config["app_api"]["use_anagrafic"]["weight2"]["date"]
            load_pid_weight2 = lb_config.g_config["app_api"]["use_anagrafic"]["weight2"]["pid"]
            
            data, total_rows = get_list_weighing_from_terminal(
                filters=query_params, 
                only_in_out_without_weight2=onlyInOutWithoutWeight2,
                only_in_out_with_weight2=onlyInOutWithWeight2,
                fromDate=fromDate, 
                toDate=toDate, 
                limit=limit, 
                offset=offset, 
                order_by=('date_created', 'desc'),
                load_subject=load_subject,
                load_vehicle=load_vehicle,
                load_material=load_material,
                load_note=load_note,
                load_date_weight1=load_date_weight1,
                load_pid_weight1=load_pid_weight1,
                load_date_weight2=load_date_weight2,
                load_pid_weight2=load_pid_weight2
            )

            # Prepara lista per export
            weighing_terminal_list = []
            for weighing in data:
                # Costruisci il dizionario dinamicamente solo con i campi caricati
                row = {}
                
                if load_vehicle:
                    row["Targa"] = weighing.plate
                
                if load_subject:
                    row["Cliente"] = weighing.customer
                    row["Fornitore"] = weighing.supplier
                
                if load_material:
                    row["Materiale"] = weighing.material

                if load_note and load_date_weight1:
                    row["Note1"] = weighing.notes1
                    
                if load_note and load_date_weight2:
                    row["Note2"] = weighing.notes2
                
                if load_date_weight1:
                    row["Data 1"] = datetime.strftime(weighing.datetime1, "%d-%m-%Y %H:%M") if weighing.datetime1 else None
                
                if load_date_weight2:
                    row["Data 2" if load_pid_weight1 else "Data"] = datetime.strftime(weighing.datetime2, "%d-%m-%Y %H:%M") if weighing.datetime2 else None
                
                if load_pid_weight1:
                    row["Pid 1"] = weighing.pid1
                
                if load_pid_weight2:
                    row["Pid 2" if load_pid_weight1 else "Pid"] = weighing.pid2 if weighing.pid2 else None
                
                row["Peso 1 (kg)" if load_pid_weight1 else "Tara (kg)"] = weighing.weight1
                row["Peso 2 (kg)" if load_pid_weight1 else "Lordo (kg)"] = weighing.weight2
                row["Netto (kg)"] = weighing.net_weight
                
                weighing_terminal_list.append(row)

            # Crea DataFrame e esporta
            df = pd.DataFrame(weighing_terminal_list)
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
            raise e

    async def exportListAccessesPdf(self, query_params: Dict[str, Union[str, int]] = Depends(get_query_params), limit: Optional[int] = None, offset: Optional[int] = None, fromDate: Optional[datetime] = None, toDate: Optional[datetime] = None, onlyInOutWithoutWeight2: Optional[bool] = False, onlyInOutWithWeight2: bool = False):
        try:
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

            if "filterDateAccess" in query_params:
                del query_params["filterDateAccess"]

            if "onlyInOutWithWeight2" in query_params:
                del query_params["onlyInOutWithWeight2"]

            if "onlyInOutWithoutWeight2" in query_params:
                del query_params["onlyInOutWithoutWeight2"]

            load_subject = lb_config.g_config["app_api"]["use_anagrafic"]["subject"]
            load_vehicle = lb_config.g_config["app_api"]["use_anagrafic"]["vehicle"]
            load_material = lb_config.g_config["app_api"]["use_anagrafic"]["material"]
            load_note = lb_config.g_config["app_api"]["use_anagrafic"]["note"]
            load_date_weight1 = lb_config.g_config["app_api"]["use_anagrafic"]["weight1"]["date"]
            load_pid_weight1 = lb_config.g_config["app_api"]["use_anagrafic"]["weight1"]["pid"]
            load_date_weight2 = lb_config.g_config["app_api"]["use_anagrafic"]["weight2"]["date"]
            load_pid_weight2 = lb_config.g_config["app_api"]["use_anagrafic"]["weight2"]["pid"]
            
            data, total_rows = get_list_weighing_from_terminal(
                filters=query_params, 
                only_in_out_without_weight2=onlyInOutWithoutWeight2,
                only_in_out_with_weight2=onlyInOutWithWeight2,
                fromDate=fromDate, 
                toDate=toDate, 
                limit=limit, 
                offset=offset, 
                order_by=('date_created', 'desc'),
                load_subject=load_subject,
                load_vehicle=load_vehicle,
                load_material=load_material,
                load_note=load_note,
                load_date_weight1=load_date_weight1,
                load_pid_weight1=load_pid_weight1,
                load_date_weight2=load_date_weight2,
                load_pid_weight2=load_pid_weight2
            )

            # Create PDF with landscape orientation and smaller margins
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, 
                                pagesize=landscape(A4),  # Orientamento orizzontale
                                leftMargin=15,
                                rightMargin=15,
                                topMargin=15,
                                bottomMargin=15)
            story = []

            # Add title with smaller spacing
            styles = getSampleStyleSheet()
            title = Paragraph("Registrature", styles['Heading2'])
            story.append(title)
            story.append(Spacer(1, 0.2*inch))

            # Define table properties with smaller font
            common_font_size = 6
            header_color = colors.grey

            # Costruisci headers e colonne dinamicamente
            headers = []
            col_widths = []

            extends = ['Peso 1 (kg)', 'Peso 2 (kg)', 'Netto (kg)']
            
            if load_vehicle:
                headers.append('Targa')
                col_widths.append(30)
            
            if load_subject:
                headers.append('Cliente')
                col_widths.append(55)
                headers.append('Fornitore')
                col_widths.append(55)

            if load_material:
                headers.append('Materiale')
                col_widths.append(55)

            if load_note and load_date_weight1:
                headers.append('Note')
                col_widths.append(55)

            if load_note and load_date_weight2:
                headers.append('Note 2')
                col_widths.append(55)
            
            if load_date_weight1:
                headers.append('Data 1')
                col_widths.append(46)
            
            if load_date_weight2:
                headers.append('Data 2' if load_pid_weight1 else 'Data')
                col_widths.append(46)
            
            if load_pid_weight1:
                headers.append('Pid 1')
                col_widths.append(46)
            else:
                extends[0] = 'Tara (kg)'
                extends[1] = 'Lordo (kg)'
            
            if load_pid_weight2:
                headers.append('Pid 2' if load_pid_weight1 else 'Pid')
                col_widths.append(46)
            
            headers.extend(extends)
            col_widths.extend([38, 38, 38])

            # Scala automaticamente le colonne per adattarle alla pagina
            available_width = landscape(A4)[0] - doc.leftMargin - doc.rightMargin
            total_width = sum(col_widths)
            
            if total_width > available_width:
                scale_factor = available_width / total_width
                col_widths = [w * scale_factor for w in col_widths]

            # Create table style with compact formatting
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), header_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), common_font_size),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ])

            # Prepare table data with compact date format
            table_data = [headers]
            for weighing in data:
                row = []
                
                if load_vehicle:
                    row.append(str(weighing.plate if weighing.plate else '')[:6])
                
                if load_subject:
                    row.append(str(weighing.customer if weighing.customer else '')[:18])
                    row.append(str(weighing.supplier if weighing.supplier else '')[:18])
                
                if load_material:
                    row.append(str(weighing.material if weighing.material else '')[:12])

                if load_note and load_date_weight1:
                    row.append(str(weighing.notes1 or '')[:18])
                
                if load_note and load_date_weight2:
                    row.append(str(weighing.notes2 or '')[:18])
                
                if load_date_weight1:
                    date1 = datetime.strftime(weighing.datetime1, "%d-%m-%y %H:%M") if weighing.datetime1 else ''
                    row.append(date1)
                
                if load_date_weight2:
                    date2 = datetime.strftime(weighing.datetime2, "%d-%m-%y %H:%M") if weighing.datetime2 else ''
                    row.append(date2)
                
                if load_pid_weight1:
                    row.append(str(weighing.pid1 if weighing.pid1 else '')[:12])
                
                if load_pid_weight2:
                    row.append(str(weighing.pid2 if weighing.pid2 else '')[:12])
                
                row.append(str(weighing.weight1) if weighing.weight1 is not None else '')
                row.append(str(weighing.weight2) if weighing.weight2 else '')
                row.append(str(weighing.net_weight) if weighing.net_weight is not None else '')
                
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

    async def deleteAccess(self, request: Request, id: int):
        locked_data = None
        try:
            if request:
                locked_data = get_data_by_attributes('lock_record', {"table_name": "access", "idRecord": id, "type": LockRecordType.DELETE, "user_id": request.state.user.id})
                if not locked_data:
                    raise HTTPException(status_code=403, detail=f"You need to block the access with id '{id}' before to update that")
            check_access_weighings = get_data_by_id("access", id)
            if check_access_weighings and len(check_access_weighings["in_out"]) > 0:
                raise HTTPException(status_code=400, detail=f"La prenotazione con id '{id}' è assegnata a delle pesate salvate")
            data = delete_data("access", id)
            await self.broadcastDeleteAnagrafic("access", {"access": Access(**data).json()})

            await broadcastMessageWebSocket({"access": {}})

            return data
        except Exception as e:
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)
        finally:
            if locked_data:
                unlock_record_by_id(locked_data["id"])