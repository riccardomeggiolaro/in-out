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

class AccessRouter(PanelSirenRouter):
    def __init__(self):
        super().__init__()
        
        self.router = APIRouter()
        
        self.router.add_api_route('/list', self.getListAccesses, methods=['GET'])
        self.router.add_api_route('/in-out/list', self.getListInOut, methods=['GET'])
        self.router.add_api_route('/in-out/pdf/{id}', self.pdfInOut, methods=['GET'])
        self.router.add_api_route('/in-out/print-last', self.printLastInOut, methods=['GET'])
        self.router.add_api_route('/weighing/list', self.getListWeighing, methods=['GET'])
        self.router.add_api_route('/export/xlsx', self.exportListAccessesXlsx, methods=['GET'])
        self.router.add_api_route('/export/pdf', self.exportListAccessesPdf, methods=['GET'])
        self.router.add_api_route('', self.addAccess, methods=['POST'], dependencies=[Depends(is_writable_user)])
        self.router.add_api_route('/{id}', self.setAccess, methods=['PATCH'], dependencies=[Depends(is_writable_user)])
        self.router.add_api_route('/close/{id}', self.closeAccess, methods=['GET'], dependencies=[Depends(is_writable_user)])
        self.router.add_api_route('/{id}', self.deleteAccess, methods=['DELETE'], dependencies=[Depends(is_writable_user)])
        self.router.add_api_route('', self.deleteAllAccesses, methods=['DELETE'], dependencies=[Depends(is_writable_user)])
        self.router.add_api_route('/last-weighing/{id}', self.deleteLastWeighing, methods=['DELETE'], dependencies=[Depends(is_writable_user)])
        self.router.add_api_route('/call/{id}', self.callAccess, methods=["GET"])
        self.router.add_api_route('/cancel-call/{id}', self.cancelCallAccess, methods=["GET"])
        
    async def getListAccesses(self, query_params: Dict[str, Union[str, int]] = Depends(get_query_params), limit: Optional[int] = None, offset: Optional[int] = None, fromDate: Optional[datetime] = None, toDate: Optional[datetime] = None, excludeTestWeighing = False, permanent: Optional[bool] = None, permanentIfWeight1: bool = None, excludeManuallyAccess: bool = False):
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
            if "permanentIfWeight1" in query_params:
                del query_params["permanentIfWeight1"]
            if "excludeManuallyAccess" in query_params:
                del query_params["excludeManuallyAccess"]
            data, total_rows = get_list_accesses(
                                    query_params,
                                    not_closed,
                                    fromDate,
                                    toDate,
                                    limit,
                                    offset,
                                    ('date_created', 'desc'),
                                    excludeTestWeighing,
                                    permanent,
                                    True,
                                    permanentIfWeight1,
                                    exclude_manually_access=excludeManuallyAccess,
                                    load_subject=lb_config.g_config["app_api"]["use_anagrafic"]["subject"],
                                    load_vector=lb_config.g_config["app_api"]["use_anagrafic"]["vector"],
                                    load_driver=lb_config.g_config["app_api"]["use_anagrafic"]["driver"],
                                    load_vehicle=lb_config.g_config["app_api"]["use_anagrafic"]["vehicle"],
                                    load_operator=lb_config.g_config["app_api"]["use_anagrafic"]["operator"],
                                    load_material=lb_config.g_config["app_api"]["use_anagrafic"]["material"],
                                    load_weighing_pictures=lb_config.g_config["app_api"]["use_anagrafic"]["weighing_pictures"],
                                    load_note=lb_config.g_config["app_api"]["use_anagrafic"]["note"],
                                    load_document_reference=lb_config.g_config["app_api"]["use_anagrafic"]["document_reference"],
                                    load_date_weight1=lb_config.g_config["app_api"]["use_anagrafic"]["weight1"]["date"],
                                    load_pid_weight1=lb_config.g_config["app_api"]["use_anagrafic"]["weight1"]["pid"],
                                    load_date_weight2=lb_config.g_config["app_api"]["use_anagrafic"]["weight2"]["date"],
                                    load_pid_weight2=lb_config.g_config["app_api"]["use_anagrafic"]["weight2"]["pid"]
                                )
            return {
                "data": data,
                "total_rows": total_rows,
                "buffer": self.buffer
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")
        
    async def getListInOut(self, query_params: Dict[str, Union[str, int]] = Depends(get_query_params), limit: Optional[int] = None, offset: Optional[int] = None, fromDate: Optional[datetime] = None, toDate: Optional[datetime] = None, excludeTestWeighing = False, onlyInOutWithWeight2: bool = False, onlyInOutWithoutWeight2: bool = False):
        try:
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

            if "onlyInOutWithWeight2" in query_params:
                del query_params["onlyInOutWithWeight2"]

            if "onlyInOutWithoutWeight2" in query_params:
                del query_params["onlyInOutWithoutWeight2"]
                
            # Call get_list_in_out with prepared query_params
            data, total_rows = get_list_in_out(
                filters=query_params,
                not_closed=False,
                only_in_out_with_weight2=onlyInOutWithWeight2,
                only_in_out_without_weight2=onlyInOutWithoutWeight2,
                fromDate=fromDate,
                toDate=toDate,
                limit=limit,
                offset=offset,
                order_by=('id', 'desc'),
                excludeTestWeighing=excludeTestWeighing,
                get_is_last=True,
                load_subject=lb_config.g_config["app_api"]["use_anagrafic"]["subject"],
                load_vector=lb_config.g_config["app_api"]["use_anagrafic"]["vector"],
                load_driver=lb_config.g_config["app_api"]["use_anagrafic"]["driver"],
                load_vehicle=lb_config.g_config["app_api"]["use_anagrafic"]["vehicle"],
                load_operator=lb_config.g_config["app_api"]["use_anagrafic"]["operator"],
                load_material=lb_config.g_config["app_api"]["use_anagrafic"]["material"],
                load_weighing_pictures=lb_config.g_config["app_api"]["use_anagrafic"]["weighing_pictures"],
                load_note=lb_config.g_config["app_api"]["use_anagrafic"]["note"],
                load_document_reference=lb_config.g_config["app_api"]["use_anagrafic"]["document_reference"],
                load_date_weight1=lb_config.g_config["app_api"]["use_anagrafic"]["weight1"]["date"],
                load_pid_weight1=lb_config.g_config["app_api"]["use_anagrafic"]["weight1"]["pid"],
                load_date_weight2=lb_config.g_config["app_api"]["use_anagrafic"]["weight2"]["date"],
                load_pid_weight2=lb_config.g_config["app_api"]["use_anagrafic"]["weight2"]["pid"]
            )
            
            return {
                "data": data,
                "total_rows": total_rows,
                "buffer": self.buffer
            }
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")

    async def pdfInOut(self, id: int):
        in_out = get_in_out_by_id(id)
        report_dir = utils.base_path_applications / lb_config.g_config["app_api"]["path_content"] / "report"
        is_generic = in_out.access.type == TypeAccess.TEST if in_out.access else False
        name_file, variables, report = get_data_variables(in_out, is_generic=is_generic)
        html = generate_html_report(report_dir, report, v=variables.dict())
        pdf = printer.generate_pdf_from_html(html_content=html)
        return StreamingResponse(
            BytesIO(pdf),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={name_file}"}
        )

    async def printLastInOut(self, instance: InstanceNameWeigherDTO = Depends(get_query_params_name_node)):
        path_pdf = lb_config.g_config["app_api"]["path_pdf"]
        report_dir = utils.base_path_applications / lb_config.g_config["app_api"]["path_content"] / "report"
        printer_name = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["printer_name"]
        number_of_prints = lb_config.g_config["app_api"]["weighers"][instance.instance_name]["nodes"][instance.weigher_name]["number_of_prints"]
        in_out = get_last_in_out_by_weigher(weigher_name=instance.weigher_name)
        if not in_out:
            raise HTTPException(status_code=404, detail="Pesata non esistente")
        is_generic = in_out.access.type == TypeAccess.TEST if in_out.access else False
        name_file, variables, report = get_data_variables(in_out, is_generic=is_generic)
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
        
    async def exportListAccessesXlsx(self, query_params: Dict[str, Union[str, int]] = Depends(get_query_params), 
                                    limit: Optional[int] = None, offset: Optional[int] = None,
                                    fromDate: Optional[datetime] = None, toDate: Optional[datetime] = None,
                                    excludeTestWeighing: bool = False, filterDateAccess: bool = False, onlyInOutWithWeight2: bool = False,
                                    onlyInOutWithoutWeight2: bool = False):
        try:
            not_closed = False
            filters = query_params.copy()

            if "access.status" in filters and filters["access.status"] == "NOT_CLOSED":
                not_closed = True
                del filters["access.status"]
            
            if "limit" in filters:
                del filters["limit"]
            if "offset" in filters:
                del filters["offset"]
                
            if fromDate is not None:
                del filters["fromDate"]
                
            if toDate is not None:
                toDate = toDate.replace(hour=23, minute=59, second=59, microsecond=999999)
                del filters["toDate"]

            if "excludeTestWeighing" in filters:
                del filters["excludeTestWeighing"]

            if "filterDateAccess" in query_params:
                del filters["filterDateAccess"]

            if "onlyInOutWithWeight2" in filters:
                del filters["onlyInOutWithWeight2"]

            if "onlyInOutWithoutWeight2" in filters:
                del filters["onlyInOutWithoutWeight2"]
            
            # Leggi configurazioni
            load_subject = lb_config.g_config["app_api"]["use_anagrafic"]["subject"]
            load_vector = lb_config.g_config["app_api"]["use_anagrafic"]["vector"]
            load_driver = lb_config.g_config["app_api"]["use_anagrafic"]["driver"]
            load_vehicle = lb_config.g_config["app_api"]["use_anagrafic"]["vehicle"]
            load_operator = lb_config.g_config["app_api"]["use_anagrafic"]["operator"]
            load_material = lb_config.g_config["app_api"]["use_anagrafic"]["material"]
            load_weighing_pictures = lb_config.g_config["app_api"]["use_anagrafic"]["weighing_pictures"]
            load_note = lb_config.g_config["app_api"]["use_anagrafic"]["note"]
            load_document_reference = lb_config.g_config["app_api"]["use_anagrafic"]["document_reference"]
            load_date_weight1 = lb_config.g_config["app_api"]["use_anagrafic"]["weight1"]["date"]
            load_pid_weight1 = lb_config.g_config["app_api"]["use_anagrafic"]["weight1"]["pid"]
            load_date_weight2 = lb_config.g_config["app_api"]["use_anagrafic"]["weight2"]["date"]
            load_pid_weight2 = lb_config.g_config["app_api"]["use_anagrafic"]["weight2"]["pid"]
                
            data, total_rows = get_list_in_out(
                filters=filters,
                not_closed=not_closed,
                only_in_out_with_weight2=onlyInOutWithWeight2,
                only_in_out_without_weight2=onlyInOutWithoutWeight2,
                fromDate=fromDate,
                toDate=toDate,
                limit=limit,
                offset=offset,
                order_by=('access.date_created', 'desc'),
                excludeTestWeighing=excludeTestWeighing,
                filterDateAccess=filterDateAccess,
                load_subject=load_subject,
                load_vector=load_vector,
                load_driver=load_driver,
                load_vehicle=load_vehicle,
                load_operator=load_operator,
                load_material=load_material,
                load_weighing_pictures=load_weighing_pictures,
                load_note=load_note,
                load_document_reference=load_document_reference,
                load_date_weight1=load_date_weight1,
                load_pid_weight1=load_pid_weight1,
                load_date_weight2=load_date_weight2,
                load_pid_weight2=load_pid_weight2
            )

            # Prepara lista per export
            in_out_list = []
            for inout in data:
                weight1 = inout.weight1.weight if inout.weight1 else None
                if weight1 is None and inout.weight2 and inout.weight2.tare > 0:
                    weight1 = inout.weight2.tare
                
                # Costruisci il dizionario dinamicamente solo con i campi caricati
                row = {}
                
                if load_vehicle:
                    row["Targa"] = inout.access.vehicle.plate if inout.access.vehicle else None
                
                if load_subject:
                    row["Cliente/Fornitore"] = inout.access.subject.social_reason if inout.access.subject else None
                
                if load_vector:
                    row["Vettore"] = inout.access.vector.social_reason if inout.access.vector else None
                
                if load_note:
                    row["Note"] = inout.access.note
                
                if load_document_reference:
                    row["Referenza documento"] = inout.access.document_reference
                
                if load_material:
                    row["Materiale"] = inout.material.description if inout.material else None

                if load_operator:
                    if inout.weight2 and inout.weight2.operator:
                        row["Operatore"] = inout.weight2.operator.description
                    elif inout.weight1 and inout.weight1.operator:
                        row["Operatore"] = inout.weight1.operator.description
                    else:
                        row["Operatore"] = ""              
                
                if load_date_weight1:
                    row["Data 1"] = datetime.strftime(inout.weight1.date, "%d-%m-%Y") if inout.weight1 else None
                    row["Ora 1"] = datetime.strftime(inout.weight1.date, "%H:%M") if inout.weight1 else None
                                    
                if load_date_weight2:
                    row["Data 2" if load_date_weight1 else "Data"] = datetime.strftime(inout.weight2.date, "%d-%m-%Y") if inout.weight2 else None
                    row["Ora 2" if load_date_weight1 else "Ora"] = datetime.strftime(inout.weight2.date, "%H:%M") if inout.weight2 else None
                
                if load_pid_weight1:
                    row["Pid 1"] = inout.weight1.pid if inout.weight1 else None
                
                if load_pid_weight2:
                    row["Pid 2" if load_pid_weight1 else "Pid"] = inout.weight2.pid if inout.weight2 else None
                
                row["Peso 1 (kg)" if load_pid_weight1 else "Tara (kg)"] = weight1
                row["Peso 2 (kg)" if load_pid_weight1 else "Lordo (kg)"] = inout.weight2.weight if inout.weight2 else None
                row["Netto (kg)"] = inout.net_weight if inout.net_weight is not None else None
                
                in_out_list.append(row)

            # Calcola totali per materiale
            material_totals = {}
            if load_material:
                for inout in data:
                    material_name = inout.material.description if inout.material and inout.material.description else "Non specificato"
                    net = inout.net_weight if inout.net_weight is not None else 0
                    if material_name in material_totals:
                        material_totals[material_name] += net
                    else:
                        material_totals[material_name] = net

            # Crea DataFrame e esporta
            df = pd.DataFrame(in_out_list)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name="Accessi", index=False)

                if load_material and material_totals:
                    workbook = writer.book
                    worksheet = writer.sheets["Accessi"]
                    bold_format = workbook.add_format({'bold': True})

                    start_row = len(in_out_list) + 2
                    worksheet.write(start_row, 0, "Totali per materiale", bold_format)
                    start_row += 1
                    worksheet.write(start_row, 0, "Materiale", bold_format)
                    worksheet.write(start_row, 1, "Netto (kg)", bold_format)
                    start_row += 1
                    for material_name, total_kg in sorted(material_totals.items(), key=lambda x: (x[0] == "Non specificato", x[0])):
                        worksheet.write(start_row, 0, material_name)
                        worksheet.write(start_row, 1, total_kg)
                        start_row += 1

            output.seek(0)
            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=pesate.xlsx"}
            )
        except Exception as e:
            raise e

    async def exportListAccessesPdf(self, query_params: Dict[str, Union[str, int]] = Depends(get_query_params), 
                                    limit: Optional[int] = None, offset: Optional[int] = None,
                                    fromDate: Optional[datetime] = None, toDate: Optional[datetime] = None,
                                    excludeTestWeighing: bool = False, filterDateAccess: bool = False, onlyInOutWithWeight2: bool = False,
                                    onlyInOutWithoutWeight2: bool = False):
        try:
            not_closed = False
            filters = query_params.copy()

            if "access.status" in filters and filters["access.status"] == "NOT_CLOSED":
                not_closed = True
                del filters["access.status"]
            
            if "limit" in filters:
                del filters["limit"]
            if "offset" in filters:
                del filters["offset"]
                
            if fromDate is not None:
                del filters["fromDate"]
                
            if toDate is not None:
                toDate = toDate.replace(hour=23, minute=59, second=59, microsecond=999999)
                del filters["toDate"]

            if "excludeTestWeighing" in filters:
                del filters["excludeTestWeighing"]

            if "filterDateAccess" in query_params:
                del filters["filterDateAccess"]

            if "onlyInOutWithWeight2" in filters:
                del filters["onlyInOutWithWeight2"]

            if "onlyInOutWithoutWeight2" in filters:
                del filters["onlyInOutWithoutWeight2"]

            # Leggi configurazioni
            load_subject = lb_config.g_config["app_api"]["use_anagrafic"]["subject"]
            load_vector = lb_config.g_config["app_api"]["use_anagrafic"]["vector"]
            load_driver = lb_config.g_config["app_api"]["use_anagrafic"]["driver"]
            load_vehicle = lb_config.g_config["app_api"]["use_anagrafic"]["vehicle"]
            load_operator = lb_config.g_config["app_api"]["use_anagrafic"]["operator"]
            load_material = lb_config.g_config["app_api"]["use_anagrafic"]["material"]
            load_weighing_pictures = lb_config.g_config["app_api"]["use_anagrafic"]["weighing_pictures"]
            load_note = lb_config.g_config["app_api"]["use_anagrafic"]["note"]
            load_document_reference = lb_config.g_config["app_api"]["use_anagrafic"]["document_reference"]
            load_date_weight1 = lb_config.g_config["app_api"]["use_anagrafic"]["weight1"]["date"]
            load_pid_weight1 = lb_config.g_config["app_api"]["use_anagrafic"]["weight1"]["pid"]
            load_date_weight2 = lb_config.g_config["app_api"]["use_anagrafic"]["weight2"]["date"]
            load_pid_weight2 = lb_config.g_config["app_api"]["use_anagrafic"]["weight2"]["pid"]

            data, total_rows = get_list_in_out(
                filters=filters,
                not_closed=not_closed,
                only_in_out_with_weight2=onlyInOutWithWeight2,
                only_in_out_without_weight2=onlyInOutWithoutWeight2,
                fromDate=fromDate,
                toDate=toDate,
                limit=limit,
                offset=offset,
                order_by=('access.date_created', 'desc'),
                excludeTestWeighing=excludeTestWeighing,
                filterDateAccess=filterDateAccess,
                load_subject=load_subject,
                load_vector=load_vector,
                load_driver=load_driver,
                load_vehicle=load_vehicle,
                load_operator=load_operator,
                load_material=load_material,
                load_weighing_pictures=load_weighing_pictures,
                load_note=load_note,
                load_document_reference=load_document_reference,
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
            title = Paragraph("Accessi", styles['Heading2'])
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
                headers.append('Cliente/Forn.')
                col_widths.append(55)
            
            if load_vector:
                headers.append('Vettore')
                col_widths.append(55)
            
            if load_note:
                headers.append('Note')
                col_widths.append(55)
            
            if load_document_reference:
                headers.append('Ref.Doc')
                col_widths.append(46)
            
            if load_material:
                headers.append('Materiale')
                col_widths.append(46)
            
            if load_operator:
                headers.append('Operatore')
                col_widths.append(46)
            
            if load_date_weight1:
                headers.append('Data 1')
                headers.append('Ora 1')
                col_widths.append(46)
            
            if load_date_weight2:
                headers.append('Data 2' if load_pid_weight1 else 'Data')
                headers.append('Ora 2' if load_pid_weight1 else 'Ora')
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
            for inout in data:
                weight1 = inout.weight1.weight if inout.weight1 else None
                if weight1 is None and inout.weight2 and inout.weight2.tare > 0:
                    weight1 = inout.weight2.tare

                row = []
                
                if load_vehicle:
                    row.append(str(inout.access.vehicle.plate if inout.access.vehicle else '')[:6])
                
                if load_subject:
                    row.append(str(inout.access.subject.social_reason if inout.access.subject else '')[:18])
                
                if load_vector:
                    row.append(str(inout.access.vector.social_reason if inout.access.vector else '')[:18])
                
                if load_note:
                    row.append(str(inout.access.note or '')[:18])
                
                if load_document_reference:
                    row.append(str(inout.access.document_reference or '')[:12])
                
                if load_material:
                    row.append(str(inout.material.description if inout.material else '')[:12])

                if load_operator:
                    if inout.weight2 and inout.weight2.operator:
                        row.append(str(inout.weight2.operator.description)[:12])
                    elif inout.weight1 and inout.weight1.operator:
                        row.append(str(inout.weight1.operator.description)[:12])
                    else:
                        row.append('')
                
                if load_date_weight1:
                    date1 = datetime.strftime(inout.weight1.date, "%d-%m-%y") if inout.weight1 else ''
                    time1 = datetime.strftime(inout.weight1.date, "%H:%M") if inout.weight1 else ''
                    row.append(date1)
                    row.append(time1)
                
                if load_date_weight2:
                    date2 = datetime.strftime(inout.weight2.date, "%d-%m-%y") if inout.weight2 else ''
                    time2 = datetime.strftime(inout.weight2.date, "%H:%M") if inout.weight2 else ''
                    row.append(date2)
                    row.append(time2)
                
                if load_pid_weight1:
                    row.append(str(inout.weight1.pid if inout.weight1 else '')[:12])
                
                if load_pid_weight2:
                    row.append(str(inout.weight2.pid if inout.weight2 else '')[:12])
                
                row.append(str(weight1) if weight1 is not None else '')
                row.append(str(inout.weight2.weight) if inout.weight2 else '')
                row.append(str(inout.net_weight) if inout.net_weight is not None else '')
                
                table_data.append(row)

            # Create and style table
            t = Table(table_data, colWidths=col_widths, repeatRows=1)
            t.setStyle(table_style)
            story.append(t)

            # Aggiungi totali per materiale
            if load_material:
                material_totals = {}
                for inout in data:
                    material_name = inout.material.description if inout.material and inout.material.description else "Non specificato"
                    net = inout.net_weight if inout.net_weight is not None else 0
                    if material_name in material_totals:
                        material_totals[material_name] += net
                    else:
                        material_totals[material_name] = net

                if material_totals:
                    story.append(Spacer(1, 0.3*inch))
                    story.append(Paragraph("Totali per materiale", styles['Heading3']))
                    story.append(Spacer(1, 0.1*inch))

                    totals_data = [['Materiale', 'Netto (kg)']]
                    for material_name, total_kg in sorted(material_totals.items(), key=lambda x: (x[0] == "Non specificato", x[0])):
                        totals_data.append([material_name, str(total_kg)])

                    totals_table = Table(totals_data, colWidths=[200, 100])
                    totals_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), header_color),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), common_font_size),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))
                    story.append(totals_table)

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

    async def addAccess(self, request: Request, body: AddAccessDTO, status: Optional[AccessStatus] = None):
        try:
            if request and not body.vehicle.id and not body.vehicle.plate:
                raise HTTPException(status_code=400, detail="E' necessario l'inserimento di una targa")
            elif request is not None:
                status = None

            body.subject.id = body.subject.id if body.subject.id not in [None, -1] else None
            body.vector.id = body.vector.id if body.vector.id not in [None, -1] else None
            body.driver.id = body.driver.id if body.driver.id not in [None, -1] else None
            body.vehicle.id = body.vehicle.id if body.vehicle.id not in [None, -1] else None

            data = add_access(body, status)

            get_access_data = get_data_by_id("access", data["id"])

            access = Access(**get_access_data)
            await self.broadcastAddAnagrafic("access", {"access": access.json()})
            if not body.subject.id and access.idSubject:
                await self.broadcastAddAnagrafic("subject", {"subject": access.subject.json()})
            if not body.vector.id and access.idVector:
                await self.broadcastAddAnagrafic("vector", {"vector": access.vector.json()})
            if not body.driver.id and access.idDriver:
                await self.broadcastAddAnagrafic("driver", {"driver": access.driver.json()})
            if not body.vehicle.id and access.idVehicle:
                await self.broadcastAddAnagrafic("vehicle", {"vehicle": access.vehicle.json()})

            await broadcastMessageWebSocket({"access": {}})

            return access
        except Exception as e:
            # Verifica se l'eccezione ha un attributo 'status_code' e usa quello, altrimenti usa 404
            status_code = getattr(e, 'status_code', 400)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)

    async def setAccess(self, request: Request, id: int, body: SetAccessDTO, idInOut: Optional[int] = None):
        locked_data = None
        try:
            if request:
                locked_data = get_data_by_attributes('lock_record', {"table_name": "access", "idRecord": id, "type": LockRecordType.UPDATE, "user_id": request.state.user.id})
                if not locked_data:
                    raise HTTPException(status_code=403, detail=f"You need to block the access with id '{id}' before to update that")
            data = update_access(id, body, idInOut)
            get_access_data = get_data_by_id("access", data["id"])
            access = Access(**get_access_data)
            in_out = None
            if idInOut:
                in_out = get_in_out_by_id(idInOut)
            await self.broadcastUpdateAnagrafic("access", {"access": access.json()})
            if body.subject.id in [None, -1] and access.idSubject:
                await self.broadcastAddAnagrafic("subject", {"subject": access.subject.json()})
            if body.vector.id in [None, -1] and access.idVector:
                await self.broadcastAddAnagrafic("vector", {"vector": access.vector.json()})
            if body.driver.id in [None, -1] and access.idDriver:
                await self.broadcastAddAnagrafic("driver", {"driver": access.driver.json()})
            if body.vehicle.id in [None, -1] and access.idVehicle:
                await self.broadcastAddAnagrafic("vehicle", {"vehicle": access.vehicle.json()})
            if in_out and body.material.id in [None, -1] and in_out.idMaterial:
                material = Material(**in_out.material.__dict__)
                await self.broadcastAddAnagrafic("material", {"material": material.json()})
            if in_out and body.operator1.id in [None, -1] and in_out.weight1 and in_out.weight1.idOperator:
                operator = Operator(**in_out.weight1.operator.__dict__)
                await self.broadcastAddAnagrafic("operator", {"operator": operator.json()})
            if in_out and body.operator2.id in [None, -1] and in_out.weight2 and in_out.weight2.idOperator:
                operator = Operator(**in_out.weight2.operator.__dict__)
                await self.broadcastAddAnagrafic("operator", {"operator": operator.json()})

            await broadcastMessageWebSocket({"access": {}})

            return access
        except Exception as e:
            status_code = getattr(e, 'status_code', 400)
            detail = getattr(e, 'detail', str(e))
            if status_code == 400:
                locked_data = None
            raise HTTPException(status_code=status_code, detail=detail)
        finally:
            if locked_data:
                unlock_record_by_id(locked_data["id"])

    async def closeAccess(self, request: Request, id: int):
        try:
            locked_data = get_data_by_attributes('lock_record', {"table_name": "access", "idRecord": id, "type": LockRecordType.UPDATE, "user_id": request.state.user.id})
            if not locked_data:
                raise HTTPException(status_code=403, detail=f"You need to block the access with id '{id}' before to update that")
            get_access_data = get_data_by_id("access", id)
            if get_access_data["status"] == AccessStatus.CLOSED:
                raise HTTPException(status_code=400, detail=f"La prenotazione con id '{id}' è già chiusa")
            elif len(get_access_data["in_out"]) == 0:
                raise HTTPException(status_code=400, detail=f"La prenotazione con id '{id}' non ha effettuato nessuna pesata")
            elif len(get_access_data["in_out"]) > 0 and get_access_data["in_out"][-1]["idWeight2"] is None:
                raise HTTPException(status_code=400, detail=f"L'ultima pesata della prenotazione con id '{id}' non è completa")
            data_to_update = {"status": AccessStatus.CLOSED}
            if get_access_data["number_in_out"] is not None:
                data_to_update["number_in_out"] = len(get_access_data["in_out"])
            data = update_data("access", id, data_to_update)
            access = Access(**data).json()
            await self.broadcastUpdateAnagrafic("access", {"access": access})
            return access
        except Exception as e:
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)
        finally:
            if locked_data:
                unlock_record_by_id(locked_data["id"])

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

    async def deleteAllAccesses(self):
        try:
            deleted_count = delete_all_data("access")
            await self.broadcastDeleteAnagrafic("access", None)

            await broadcastMessageWebSocket({"access": {}})

            return {
                "deleted_count": deleted_count,
            }
        except Exception as e:
            status_code = getattr(e, 'status_code', 500)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)
        
    async def deleteLastWeighing(self, request: Request, id: int, deleteAccessIfislastInOut: Optional[bool] = True):
        locked_data = None
        try:
            locked_data = get_data_by_attributes('lock_record', {"table_name": "access", "idRecord": id, "type": LockRecordType.DELETE, "user_id": request.state.user.id})
            if not locked_data:
                raise HTTPException(status_code=403, detail=f"You need to block the access with id '{id}' before to delete its last weighing")
            weighingId = delete_last_weighing_of_access(id)
            update_data("weighing", weighingId, {"idOperator": -1})
            data = get_access_by_id(id)
            if data:
                number_in_out_executed = len(data.in_out)
                if number_in_out_executed > 0:
                    data = update_data("access", id, {"status": AccessStatus.ENTERED})
                else:
                    if deleteAccessIfislastInOut and data.type != TypeAccess.RESERVATION:
                        data = delete_data("access", id)
                    else:
                        data = update_data("access", id, {"status": AccessStatus.WAITING})
                access = Access(**data).json()
                await self.broadcastDeleteAnagrafic("access", {"weighing": access})

                await broadcastMessageWebSocket({"access": {}})

                return access
            # else:
            #     await self.broadcastDeleteAnagrafic("access", {"weighing": access})
            return None
        except Exception as e:
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)
        finally:
            if locked_data:
                unlock_record_by_id(locked_data["id"])
        
    async def callAccess(self, request: Request, id: int):
        locked_data = None
        try:
            locked_data = get_data_by_attributes('lock_record', {"table_name": "access", "idRecord": id, "type": LockRecordType.CALL, "user_id": request.state.user.id})
            if not locked_data:
                raise HTTPException(status_code=403, detail=f"You need to block the access with id '{id}' before to delete its last weighing")
            data = get_data_by_id("access", id)
            if data["status"] == AccessStatus.CLOSED:
                raise HTTPException(status_code=400, detail=f"La prenotazione con id '{id}' è già stata chiusa")
            elif data["vehicle"]["plate"] in self.buffer:
                raise HTTPException(status_code=400, detail=f"La targa '{data['vehicle']['plate']}' della prenotazione con id '{id}' è già presente nel buffer")
            edit_buffer = await self.sendMessagePanel(data["vehicle"]["plate"], True)
            try:
                await self.sendMessageSiren()
            except Exception as e:
                pass
            access = Access(**data).json()
            broadcast_data = {"access": access}
            if "panel_error" in edit_buffer:
                broadcast_data["panel_error"] = edit_buffer["panel_error"]
            await self.broadcastCallAnagrafic("access", broadcast_data)
            return edit_buffer
        except Exception as e:
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)
        finally:
            if locked_data:
                unlock_record_by_id(locked_data["id"])
    
    async def cancelCallAccess(self, request: Request, id: int):
        locked_data = None
        try:
            locked_data = get_data_by_attributes('lock_record', {"table_name": "access", "idRecord": id, "type": LockRecordType.CANCEL_CALL, "user_id": request.state.user.id})
            if not locked_data:
                raise HTTPException(status_code=403, detail=f"You need to block the access with id '{id}' before to delete its last weighing")
            data = get_data_by_id("access", id)
            if data["vehicle"]["plate"] not in self.buffer:
                raise HTTPException(status_code=400, detail=f"La targa '{data['vehicle']['plate']}' della prenotazione con id '{id}' non è presente nel buffer")
            undo_buffer = await self.deleteMessagePanel(data["vehicle"]["plate"])
            access = Access(**data).json()
            broadcast_data = {"access": access}
            if "panel_error" in undo_buffer:
                broadcast_data["panel_error"] = undo_buffer["panel_error"]
            await self.broadcastCallAnagrafic("access", broadcast_data)
            return undo_buffer
        except Exception as e:
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)
        finally:
            if locked_data:
                unlock_record_by_id(locked_data["id"])
