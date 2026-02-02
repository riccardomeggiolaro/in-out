from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from applications.middleware.super_admin import is_super_admin
from fastapi.responses import StreamingResponse
import libs.lb_system as lb_system
import libs.lb_config as lb_config
from fastapi.responses import FileResponse
import os
from libs.lb_printer import printer
from applications.utils.utils_report import generate_html_report
from io import BytesIO
import shutil
from pathlib import Path
from collections import defaultdict
from pydantic import BaseModel, validator, field_validator, ValidationInfo
import re
import json
import zipfile
import os
import json
import zipfile
import asyncio
import aiofiles
import time
import sys
import platform
import subprocess
from io import BytesIO
from fastapi import UploadFile, HTTPException

class MarginsDTO(BaseModel):
    top: str
    right: str
    bottom: str
    left: str
    
    @validator('*')
    def validate_margin(cls, v):
        # Verifica che la stringa contenga solo numeri (interi o decimali)
        if not re.match(r'^\d+(\.\d+)?$', v):
            raise ValueError(f"{v} non è un numero valido.")
        return v

class ReportTemplateDTO(BaseModel):
    canvas: str
    html: str
    format: str
    margins: MarginsDTO
    zoom: int
    elementCounter: int
    totalPages: int
    globalFont: str

   # Validatore per canvas, html e globalFont (stringhe non vuote)
    @field_validator('canvas', 'html', 'globalFont')
    @classmethod
    def validate_non_empty_string(cls, v: str, info: ValidationInfo):
        if not v or not isinstance(v, str):
            raise ValueError(f"{info.field_name} deve essere una stringa non vuota.")
        return v.strip()

    @field_validator('format')
    @classmethod
    def validate_format(cls, v: str):
        valid_formats = ['A4', 'A5', 'A6', 'A7', 'A8', 'Receipt80']
        v_upper = v.upper()

        # Normalizza Receipt80 a uppercase per confronto
        normalized_formats = [f.upper() for f in valid_formats]

        if v_upper not in normalized_formats:
            raise ValueError(f"Il formato deve essere uno di: {', '.join(valid_formats)}.")
        
        # Restituisce il formato così com'è nella lista originale (corretto casing)
        for original_format in valid_formats:
            if original_format.upper() == v_upper:
                return original_format

    # Validatore per zoom, elementCounter e totalPages (numeri interi positivi)
    @field_validator('zoom', 'elementCounter', 'totalPages')
    @classmethod
    def validate_positive_integer(cls, v: int, info: ValidationInfo):
        if not isinstance(v, int) or v <= 0:
            raise ValueError(f"{info.field_name} deve essere un intero positivo.")
        return v

class GenericRouter:
    def __init__(self):
        self.router = APIRouter()

        # Aggiungi le rotte
        self.router.add_api_route('/list/serial-ports', self.getSerialPorts, dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('/list/default-reports', self.listDefualtReports, dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('/report/{report}', self.saveReportTemplate, methods=['POST'], dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('/restart', self.restartSoftware, methods=['POST'], dependencies=[Depends(is_super_admin)])

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
        directory = Path(__file__).cwd() / "applications" / lb_config.g_config['app_api']['path_content'] / "report/default-report"
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

    async def saveReportTemplate(self, report: str, file: UploadFile):
        if report not in ["report_in", "report_out"]:
            raise HTTPException(status_code=400, detail="Tipo di report non valido")
        
        path = Path(__file__).cwd() / "applications" / lb_config.g_config["app_api"]["path_content"] / "report"
        report_file = lb_config.g_config["app_api"][report]
        full_path = os.path.join(path, report_file)
        
        start_time = time.time()
        
        try:
            await asyncio.to_thread(os.makedirs, os.path.dirname(full_path), exist_ok=True)

            # Statistiche per il tracking
            stats = {
                "zip_read_time": 0,
                "extraction_time": 0,
                "validation_time": 0,
                "write_time": 0,
                "verification_time": 0
            }

            # Fase 1: Lettura streaming ottimizzata
            phase_start = time.time()
            
            zip_data = await file.read()  # Leggi tutto per ZIP (necessario per struttura)
            if len(zip_data) == 0:
                raise HTTPException(status_code=400, detail="File vuoto ricevuto")
                
            stats["zip_read_time"] = time.time() - phase_start

            # Fase 2: Estrazione asincrona
            phase_start = time.time()
            
            async def extract_json():
                def _extract():
                    with zipfile.ZipFile(BytesIO(zip_data), 'r') as zip_file:
                        files = zip_file.namelist()
                        json_file = next((f for f in files if f.endswith('.json')), None)
                        if not json_file:
                            raise ValueError("Nessun file JSON nel ZIP")
                        
                        with zip_file.open(json_file) as jf:
                            return jf.read().decode('utf-8')
                
                return await asyncio.to_thread(_extract)

            json_content = await extract_json()
            stats["extraction_time"] = time.time() - phase_start

            # Fase 3: Validazione asincrona
            phase_start = time.time()
            
            await asyncio.to_thread(json.loads, json_content)
            stats["validation_time"] = time.time() - phase_start

            # Fase 4: Scrittura streaming ad alta velocità
            phase_start = time.time()
            
            json_bytes = json_content.encode('utf-8')
            chunk_size = 1024 * 1024  # 1MB chunks per massima velocità
            
            async with aiofiles.open(full_path, 'wb') as f:
                for i in range(0, len(json_bytes), chunk_size):
                    chunk = json_bytes[i:i + chunk_size]
                    await f.write(chunk)
                await f.flush()
                await asyncio.to_thread(os.fsync, f.fileno())
                
            stats["write_time"] = time.time() - phase_start

            # Fase 5: Verifica finale
            phase_start = time.time()
            
            def verify():
                if not os.path.exists(full_path):
                    raise ValueError("File non esistente")
                size = os.path.getsize(full_path)
                if size != len(json_bytes):
                    raise ValueError(f"Dimensioni errate: {size} vs {len(json_bytes)}")
                return size
                
            final_size = await asyncio.to_thread(verify)
            stats["verification_time"] = time.time() - phase_start
            total_time = time.time() - start_time
            
            return {
                "message": "Report salvato con successo",
                "status": "completed", 
                "original_zip_size": len(zip_data),
                "final_json_size": final_size,
                "compression_ratio": f"{(1 - len(zip_data)/final_size)*100:.1f}%",
                "performance": {
                    **stats,
                    "total_time": total_time,
                    "throughput_mbps": (final_size / (1024*1024)) / total_time
                }
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Errore: {str(e)}")
            
    async def getReportIn(self):
        path = lb_config.g_config['app_api']['path_report']
        name_report_in = lb_config.g_config["app_api"]["report_in"]
        if name_report_in:
            full_path = os.path.join(path, name_report_in)
            if os.path.exists(full_path):
                return FileResponse(
                    full_path,
                    media_type="text/html",
                    headers={
                        "Content-Disposition": f"attachment; filename={name_report_in}",
                        "Cache-Control": "no-cache, no-store, must-revalidate",
                        "Pragma": "no-cache",
                        "Expires": "0"
                    },
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
                    headers={
                        "Content-Disposition": f"attachment; filename={name_report_out}",
                        "Cache-Control": "no-cache, no-store, must-revalidate",
                        "Pragma": "no-cache",
                        "Expires": "0"
                    }
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

    async def restartSoftware(self):
        """Riavvia il software tramite systemd. Disponibile solo su Linux con servizio attivo."""
        # Controlla se siamo su Windows
        if platform.system() == "Windows":
            raise HTTPException(status_code=400, detail="Funzione non abilitata su Windows")

        # Siamo su Linux - controlla se esiste un demone systemd attivo
        service_name = "baron"

        def is_systemd_service_active():
            try:
                result = subprocess.run(
                    ["systemctl", "is-active", service_name],
                    capture_output=True,
                    text=True
                )
                return result.stdout.strip() == "active"
            except Exception:
                return False

        if not is_systemd_service_active():
            raise HTTPException(status_code=400, detail="Funzione non abilitata (servizio non attivo)")

        async def restart_after_response():
            await asyncio.sleep(1)  # Attendi che la risposta sia inviata
            subprocess.run(["systemctl", "restart", service_name])

        asyncio.create_task(restart_after_response())
        return {"message": f"Riavvio del servizio {service_name} in corso..."}