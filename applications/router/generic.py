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
        self.router.add_api_route('/export-config-doc', self.exportConfigDoc, dependencies=[Depends(is_super_admin)])

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
        if report not in ["report_in", "report_out", "report_tare", "report_generic"]:
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
        """Riavvia il software tramite servizio di sistema. Disponibile solo con servizio attivo."""
        is_windows = lb_system.is_windows()
        is_linux = lb_system.is_linux()
        service_name = "in-out"

        def is_service_active():
            try:
                if is_windows:
                    # Controlla servizio Windows
                    result = subprocess.run(
                        ["sc", "query", service_name],
                        capture_output=True,
                        text=True
                    )
                    return "RUNNING" in result.stdout
                elif is_linux:
                    # Controlla servizio systemd su Linux
                    result = subprocess.run(
                        ["systemctl", "is-active", service_name],
                        capture_output=True,
                        text=True
                    )
                    return result.stdout.strip() == "active"
                return False
            except Exception:
                return False

        if not is_service_active():
            raise HTTPException(status_code=400, detail="Funzione non abilitata (servizio non attivo)")

        async def restart_after_response():
            await asyncio.sleep(1)  # Attendi che la risposta sia inviata
            if is_windows:
                subprocess.run(["sc", "stop", service_name], capture_output=True)
                subprocess.run(["sc", "start", service_name], capture_output=True)
            elif is_linux:
                subprocess.run(["systemctl", "restart", service_name])

        asyncio.create_task(restart_after_response())
        return {"message": f"Riavvio del servizio {service_name} in corso..."}

    @staticmethod
    def _si_no(value):
        return "Sì" if value else "No"

    @staticmethod
    def _row(label, value):
        return f'<tr><td>{label}</td><td>{value}</td></tr>'

    def _build_config_explanation_html(self, config):
        app = config.get("app_api", {})

        mode_descriptions = {
            "AUTOMATIC": "Automatica (la pesata viene gestita in modo automatico dal sistema)",
            "MANUAL": "Manuale (l'operatore gestisce manualmente le fasi di pesata)",
        }
        mode = app.get("mode", "N/D")
        mode_desc = mode_descriptions.get(mode, mode)

        # --- Sezione: informazioni generali ---
        general_rows = (
            self._row("Nome software", config.get("name", "N/D"))
            + self._row("Versione installata", config.get("ver", "N/D"))
            + self._row("Porta web utilizzata", app.get("port", "N/D"))
            + self._row("Modalità di funzionamento", mode_desc)
        )

        # --- Sezione: percorsi dati ---
        paths_rows = (
            self._row("Database (tutti i dati di pesate, anagrafiche, ecc.)", app.get("path_database", "N/D"))
            + self._row("Cartella dei file CSV esportati", app.get("path_csv", "N/D"))
            + self._row("Cartella delle immagini salvate (es. foto pesate)", app.get("path_img", "N/D"))
            + self._row("Cartella dei PDF generati (report di pesata)", app.get("path_pdf", "N/D"))
        )

        # --- Sezione: funzionalità abilitate ---
        use_anagrafic = app.get("use_anagrafic", {})
        features_rows = (
            self._row("Tipo soggetto predefinito nelle nuove pesate", app.get("default_type_subject", "N/D"))
            + self._row("Anagrafica documento di riferimento", self._si_no(use_anagrafic.get("document_reference")))
            + self._row("Anagrafica conducente (driver)", self._si_no(use_anagrafic.get("driver")))
            + self._row("Anagrafica materiale trasportato", self._si_no(use_anagrafic.get("material")))
            + self._row("Anagrafica note", self._si_no(use_anagrafic.get("note")))
            + self._row("Anagrafica operatore", self._si_no(use_anagrafic.get("operator")))
            + self._row("Anagrafica soggetto (cliente/fornitore)", self._si_no(use_anagrafic.get("subject")))
            + self._row("Anagrafica vettore", self._si_no(use_anagrafic.get("vector")))
            + self._row("Anagrafica veicolo", self._si_no(use_anagrafic.get("vehicle")))
            + self._row("Salvataggio foto durante la pesata", self._si_no(use_anagrafic.get("weighing_pictures")))
            + self._row("Uso del badge per identificare l'utente", self._si_no(app.get("use_badge")))
            + self._row("Uso di un peso preimpostato", self._si_no(app.get("use_preset_weight")))
            + self._row("Salvataggio delle registrazioni (recordings)", self._si_no(app.get("use_recordings")))
            + self._row("Uso delle prenotazioni", self._si_no(app.get("use_reservation")))
            + self._row("Gestione transiti", self._si_no(app.get("use_transit")))
            + self._row("Uso della lista bianca (white list)", self._si_no(app.get("use_white_list")))
            + self._row("Visualizzazione totali esportati", self._si_no(app.get("show_export_totals")))
            + self._row("Eliminazione automatica pesate in sospeso a mezzanotte", self._si_no(app.get("delete_pending_accesses_at_midnight")))
            + self._row("Copia del PDF restituita dopo la pesata", self._si_no(app.get("return_pdf_copy_after_weighing")))
            + self._row("Modalità di test attiva", self._si_no(app.get("test_mode")))
        )

        # --- Sezione: totem ---
        totem_anagrafiche = app.get("totem_anagrafiche", {})
        totem_rows = (
            self._row("Totem self-service abilitato", self._si_no(app.get("totem_enabled")))
            + self._row("Anagrafica badge/tessera al totem", self._si_no(totem_anagrafiche.get("card")))
            + self._row("Anagrafica conducente (driver) al totem", self._si_no(totem_anagrafiche.get("driver")))
            + self._row("Anagrafica materiale trasportato al totem", self._si_no(totem_anagrafiche.get("material")))
            + self._row("Anagrafica soggetto al totem", self._si_no(totem_anagrafiche.get("subject")))
            + self._row("Anagrafica vettore al totem", self._si_no(totem_anagrafiche.get("vector")))
            + self._row("Anagrafica veicolo al totem", self._si_no(totem_anagrafiche.get("vehicle")))
        )

        # --- Sezione: pannello e sirena ---
        panel = app.get("panel", {})
        siren = app.get("siren", {})
        devices_rows = (
            self._row("Pannello informativo abilitato", self._si_no(panel.get("enabled")))
            + self._row("Tipo di pannello", panel.get("type", "N/D"))
            + self._row("Indirizzo IP del pannello", panel.get("connection", {}).get("ip", "N/D"))
            + self._row("Sirena/segnalatore abilitato", self._si_no(siren.get("enabled")))
            + self._row("Tipo di sirena", siren.get("type", "N/D"))
            + self._row("Indirizzo IP della sirena", siren.get("connection", {}).get("ip", "N/D"))
        )

        # --- Sezione: sincronizzazione cartella remota ---
        sync = app.get("sync_folder", {})
        sync_rows = (
            self._row("Cartella locale sincronizzata", sync.get("local_dir", "N/D"))
            + self._row("Punto di mount della cartella remota", sync.get("mount_point", "N/D"))
            + self._row("Cartella remota di destinazione", sync.get("remote_folder") or "Non configurata")
            + self._row("Sottocartelle sincronizzate", ", ".join(sync.get("sub_paths", [])) or "Nessuna")
        )

        # --- Sezione: pese collegate ---
        weighers = app.get("weighers", {})
        weighers_html = ""
        for index, (w_id, weigher) in enumerate(sorted(weighers.items()), start=1):
            connection = weigher.get("connection", {})
            weighers_html += f'<h3>Connessione {index}</h3><table>'
            weighers_html += self._row("Indirizzo IP della pesa", connection.get("ip", "N/D"))
            weighers_html += self._row("Porta di comunicazione", connection.get("port", "N/D"))
            weighers_html += self._row("Timeout di comunicazione (secondi)", connection.get("timeout", "N/D"))
            weighers_html += self._row("Attesa tra un'azione e l'altra (secondi)", weigher.get("time_between_actions", "N/D"))
            weighers_html += "</table>"

            nodes = weigher.get("nodes", {})
            for n_id, node in sorted(nodes.items()):
                weighers_html += f'<h4>Pesa {node.get("name", n_id)}</h4><table>'
                weighers_html += self._row("Tipo di terminale di pesata", node.get("terminal", "N/D"))
                weighers_html += self._row("Punto di pesata attivo", self._si_no(node.get("run")))
                weighers_html += self._row("Peso minimo accettato (kg)", node.get("min_weight", "N/D"))
                weighers_html += self._row("Peso massimo accettato (kg)", node.get("max_weight", "N/D"))
                weighers_html += self._row("Soglia massima di allarme", node.get("max_theshold") if node.get("max_theshold") is not None else "Non impostata")
                weighers_html += self._row("Divisione (risoluzione del peso)", node.get("division", "N/D"))
                weighers_html += self._row("Numero di copie di stampa predefinito", node.get("number_of_prints", "N/D"))
                weighers_html += self._row("Stampante associata", node.get("printer_name") or "Predefinita di sistema")
                weighers_html += self._row("Scarico (azzeramento) richiesto prima della pesata", self._si_no(node.get("need_take_of_weight_before_weighing")))
                weighers_html += self._row("Scarico (azzeramento) richiesto all'avvio", self._si_no(node.get("need_take_of_weight_on_startup")))
                weighers_html += self._row("Trasmissione continua del peso (continuous transmission)", self._si_no(node.get("continuous_transmission")))
                weighers_html += self._row("Mantieni la sessione attiva dopo un comando", self._si_no(node.get("maintaine_session_realtime_after_command")))
                weighers_html += self._row("Diagnostica con priorità sul tempo reale", self._si_no(node.get("diagnostic_has_priority_than_realtime")))
                weighers_html += self._row("Esecuzione tempo reale anche sotto soglia minima", self._si_no(node.get("always_execute_realtime_in_undeground")))
                weighers_html += self._row("Relè collegati", ", ".join(node.get("rele", {}).keys()) or "Nessuno")
                weighers_html += self._row("Porta del modulo relè", node.get("port_rele") or "Non configurata")
                weighers_html += "</table>"

        sections = [
            ("1. Informazioni generali", general_rows),
            ("2. Percorsi dei dati", paths_rows),
            ("3. Funzionalità abilitate", features_rows),
            ("4. Totem self-service", totem_rows),
            ("5. Pannello e sirena", devices_rows),
            ("6. Sincronizzazione con cartella remota", sync_rows),
        ]

        sections_html = ""
        for title, rows in sections:
            sections_html += f"<h2>{title}</h2><table>{rows}</table>"
        sections_html += "<h2>7. Pese collegate</h2>" + (weighers_html or "<p>Nessuna pesa configurata.</p>")

        return sections_html

    async def exportConfigDoc(self):
        """Genera un PDF con la documentazione della configurazione (in linguaggio comprensibile)
        e lo esporta insieme al config.json in un file ZIP."""
        try:
            config_dict = lb_config.g_config
            config_path = os.path.join(lb_config.config_path, "config.json")

            with open(config_path, "r", encoding="utf-8") as f:
                config_raw = f.read()

            generated_at = time.strftime("%Y-%m-%d %H:%M:%S")
            sections_html = self._build_config_explanation_html(config_dict)
            html = f"""
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; font-size: 12px; color: #222; }}
                    h1 {{ font-size: 20px; margin-bottom: 0; }}
                    h2 {{ font-size: 15px; margin-top: 22px; border-bottom: 2px solid #4CAF50; padding-bottom: 4px; }}
                    h3 {{ font-size: 13px; margin-top: 14px; color: #2196F3; }}
                    h4 {{ font-size: 12px; margin-top: 8px; }}
                    p.subtitle {{ color: #666; margin-top: 2px; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 4px; }}
                    td {{ border-bottom: 1px solid #ddd; padding: 4px 6px; vertical-align: top; }}
                    td:first-child {{ width: 55%; color: #333; }}
                    td:last-child {{ font-weight: bold; word-break: break-all; }}
                </style>
            </head>
            <body>
                <h1>Documentazione della configurazione</h1>
                <p class="subtitle">Software: {config_dict.get('name', '')} — Generato il {generated_at}</p>
                <p>
                    Questo documento descrive, in modo semplice e leggibile, come è attualmente
                    configurato il software. Per i dettagli tecnici completi è incluso anche il
                    file <strong>config.json</strong> in questo stesso archivio.
                </p>
                {sections_html}
            </body>
            </html>
            """

            pdf_bytes = await asyncio.to_thread(printer.generate_pdf_from_html, html)

            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.writestr("documentazione_configurazione.pdf", pdf_bytes)
                zip_file.writestr("config.json", config_raw)
            zip_buffer.seek(0)

            return StreamingResponse(
                zip_buffer,
                media_type="application/zip",
                headers={"Content-Disposition": "attachment; filename=in-out-config-export.zip"}
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Errore nella generazione dell'export: {str(e)}")