from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
import libs.lb_system as lb_system
from modules.md_database.functions.get_data_by_attribute import get_data_by_attribute
from applications.utils.utils_auth import create_access_token
import libs.lb_config as lb_config
from fastapi.responses import FileResponse
import os
from libs.lb_printer import printer
from applications.utils.utils_report import generate_html_report
from io import BytesIO
import shutil
from pathlib import Path
from collections import defaultdict

class GenericRouter:
    def __init__(self):
        self.router = APIRouter()

        # Aggiungi le rotte
        self.router.add_api_route('/list/serial-ports', self.getSerialPorts)
        self.router.add_api_route('/list/default-reports', self.listDefualtReports)
        self.router.add_api_route('/report-in', self.saveReportIn, methods=['POST'])
        self.router.add_api_route('/report-in', self.getReportIn)
        self.router.add_api_route('/report-in/preview', self.getReportInPreview)
        self.router.add_api_route('/report-out', self.saveReportOut, methods=['POST'])
        self.router.add_api_route('/report-out', self.getReportOut)
        self.router.add_api_route('/report-out/preview', self.getReportOutPreview)

    async def getSerialPorts(self):
        """Restituisce una lista delle porte seriali disponibili e il tempo impiegato per ottenerla."""
        import time
        start_time = time.time()
        try:
            status, data = lb_system.list_serial_port()
            elapsed = time.time() - start_time
            if status:
                return {"list_serial_ports": data, "elapsed_seconds": elapsed}
            else:
                raise HTTPException(status_code=400, detail="Unable to retrieve serial ports")
        except Exception as e:
            elapsed = time.time() - start_time
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)} (elapsed: {elapsed:.3f}s)")

    def listDefualtReports(self):
        """
        Restituisce una struttura ad albero con percorsi relativi delle cartelle
        """
        directory = lb_config.g_config['app_api']['path_report'] + "/default-report/"
        files_tree = defaultdict(list)
        
        try:
            directory_path = Path(directory)
            
            if not directory_path.exists():
                print(f"Directory non trovata: {directory}")
                return {}
            
            if not directory_path.is_dir():
                print(f"Il percorso non è una directory: {directory}")
                return {}
            
            # Ottieni tutti i file ricorsivamente
            for file_path in directory_path.rglob('*'):
                if file_path.is_file():
                    # Ottieni il percorso relativo della cartella
                    relative_path = file_path.relative_to(directory_path)
                    if relative_path.parent == Path('.'):
                        folder_key = 'root'
                    else:
                        folder_key = str(relative_path.parent)
                    
                    files_tree[folder_key].append(file_path.name)
                    
        except PermissionError:
            print(f"Permessi insufficienti per accedere a: {directory}")
        except Exception as e:
            print(f"Errore durante la scansione della directory: {e}")
        
        return dict(files_tree)
        
    async def saveReportIn(self, file: UploadFile = File(None)):
        path = lb_config.g_config['app_api']['path_report']
        name_report_in = lb_config.g_config["app_api"]["report_in"]
        if file and file.filename == lb_config.g_config["app_api"]["report_out"]:
            raise HTTPException(status_code=400, detail="File with this name just exists")
        try:
            if name_report_in is not None:
                full_path = os.path.join(path, name_report_in)
                # Elimina il file se esiste
                if os.path.exists(full_path):
                    os.remove(full_path)
                    lb_config.g_config["app_api"]["report_in"] = None
                    lb_config.saveconfig()
                if file is None:
                    return {"message": "Report eliminato correttamente"}
            if file is not None:
                # Controlla che sia un file HTML
                if not file.filename.lower().endswith('.html'):
                    raise HTTPException(status_code=400, detail="Il file deve essere in formato .html")
                if file.content_type not in ["text/html", "application/octet-stream"]:
                    raise HTTPException(status_code=400, detail="Il file deve essere di tipo text/html")
                lb_config.g_config["app_api"]["report_in"] = file.filename
                lb_config.saveconfig()
                name_report_in = lb_config.g_config["app_api"]["report_in"]
                full_path = os.path.join(path, name_report_in)
                with open(full_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                return {"message": "Report salvato correttamente"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Errore nel salvataggio/eliminazione del report: {str(e)}")
            
    async def getReportIn(self):
        path = lb_config.g_config['app_api']['path_report']
        name_report_in = lb_config.g_config["app_api"]["report_in"]
        if name_report_in:
            full_path = os.path.join(path, name_report_in)
            if os.path.exists(full_path):
                return FileResponse(
                    full_path,
                    media_type="text/html",
                    headers={"Content-Disposition": f"attachment; filename={name_report_in}"}
                )
        raise HTTPException(status_code=404, detail="Report not found")

    async def getReportInPreview(self):
        path = lb_config.g_config['app_api']['path_report']
        name_report_in = lb_config.g_config["app_api"]["report_in"]
        if name_report_in:
            full_path = os.path.join(path, name_report_in)
            if os.path.exists(full_path):
                html = generate_html_report(path, name_report_in)
                pdf = printer.generate_pdf_from_html(html)
                return StreamingResponse(
                    BytesIO(pdf),
                    media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename={name_report_in}"}
                )
        raise HTTPException(status_code=404, detail="Report not found")

    async def saveReportOut(self, file: UploadFile = File(None)):
        path = lb_config.g_config['app_api']['path_report']
        name_report_out = lb_config.g_config["app_api"]["report_out"]
        if file and file.filename == lb_config.g_config["app_api"]["report_in"]:
            raise HTTPException(status_code=400, detail="File with this name just exists")
        try:
            if name_report_out is not None:
                full_path = os.path.join(path, name_report_out)
                # Elimina il file se esiste
                if os.path.exists(full_path):
                    os.remove(full_path)
                    lb_config.g_config["app_api"]["report_out"] = None
                    lb_config.saveconfig()
                if file is None:
                    return {"message": "Report eliminato correttamente"}
            if file is not None:
                # Controlla che sia un file HTML
                if not file.filename.lower().endswith('.html'):
                    raise HTTPException(status_code=400, detail="Il file deve essere in formato .html")
                if file.content_type not in ["text/html", "application/octet-stream"]:
                    raise HTTPException(status_code=400, detail="Il file deve essere di tipo text/html")
                lb_config.g_config["app_api"]["report_out"] = file.filename
                lb_config.saveconfig()
                name_report_out = lb_config.g_config["app_api"]["report_out"]
                full_path = os.path.join(path, name_report_out)
                with open(full_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                return {"message": "Report salvato correttamente"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Errore nel salvataggio/eliminazione del report: {str(e)}")

    async def getReportOut(self):
        path = lb_config.g_config['app_api']['path_report']
        name_report_out = lb_config.g_config["app_api"]["report_out"]
        if name_report_out:
            full_path = os.path.join(path, name_report_out)
            if os.path.exists(full_path):
                return FileResponse(
                    full_path,
                    media_type="text/html",
                    headers={"Content-Disposition": f"attachment; filename={name_report_out}"}
                )
        raise HTTPException(status_code=404, detail="Report not found")
    
    async def getReportOutPreview(self):
        path = lb_config.g_config['app_api']['path_report']
        name_report_out = lb_config.g_config["app_api"]["report_out"]
        if name_report_out:
            full_path = os.path.join(path, name_report_out)
            if os.path.exists(full_path):
                html = generate_html_report(path, name_report_out)
                pdf = printer.generate_pdf_from_html(html)
                return StreamingResponse(
                    BytesIO(pdf),
                    media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename={name_report_out}"}
                )
        raise HTTPException(status_code=404, detail="Report not found")