import cups
import tempfile
import os
from typing import List
import libs.lb_log as lb_log
import datetime as dt

"""
Linux debian dependencies:
    apt-get install libcups2-dev python3-dev cups python3-pycups build-essential libusb-1.0-0-dev
    sudo apt install hplip hplip-gui
    cd ~/Downloads
    chmod +x hplip-<version>.run
    ./hplip-<version>.run
    hp-setup
    sudo usermod -aG lp $(whoami)
"""

class HTMLPrinter:
    def __init__(self, printer_name=None):
        self.conn = cups.Connection()
        if printer_name is not None:
            self.printer_name = printer_name
            self.mode = 1
        else:
            self.printer_name = self.conn.getDefault()
            self.mode = 0

    def get_printer_state_description(self, state: int):
        states = {
            3: "Pronta",
            4: "In elaborazione",
            5: "Fermata",
        }
        return states.get(state, f"Stato sconosciuto ({state})")

    def interpret_state_reasons(self, reasons: List[str]):
        reason_descriptions = {
            'marker-supply-low-warning': 'Livello inchiostro basso',
            'marker-supply-empty-warning': 'Cartuccia vuota',
            'toner-low': 'Toner basso',
            'toner-empty': 'Toner esaurito',
            'cover-open': 'Coperchio aperto',
            'door-open': 'Sportello aperto',
            'paper-empty': 'Carta esaurita',
            'paper-jam': 'Inceppamento carta',
            'media-empty-warning': 'Vassio carta vuoto',
            'offline-report': 'Stampante offline',
            'cups-waiting-for-job-completed': 'In attessa di completamento stampa'
        }
        
        return [reason_descriptions.get(reason, reason) for reason in reasons]

    def get_detailed_status(self):
        status = self.get_printer_status()
        
        detailed_status = {
            'nome': self.printer_name if status.get('printer-info') else 'Sconosciuto',
            'stato': self.get_printer_state_description(status.get('printer-state')),
            'messaggi': self.interpret_state_reasons(status.get('printer-state-reasons', [])),
            'modello': status.get('printer-make-and-model', 'Sconosciuto'),
            'condivisa': 'Sì' if status.get('printer-is-shared') else 'No',
            'uri_dispositivo': status.get('device-uri', 'Sconosciuto'),
            'modalità': 'Predefinita' if self.mode == 0 else 'Configurata'
        }
        
        return detailed_status

    def get_printer_status(self):
        printers = self.conn.getPrinters()
        return printers.get(self.printer_name, {})

    def get_list_printers(self):
        # Verifica se la stampante esiste
        printers = self.conn.getPrinters()

        detaileds_status = []

        for printer in printers:
            status = printers.get(printer, {})

            detailed_status = {
                'nome': printer,
                'stato': self.get_printer_state_description(status.get('printer-state')),
                'messaggi': self.interpret_state_reasons(status.get('printer-state-reasons', [])),
                'modello': status.get('printer-make-and-model', 'Sconosciuto'),
                'condivisa': 'Sì' if status.get('printer-is-shared') else 'No',
                'uri_dispositivo': status.get('device-uri', 'Sconosciuto'),
                'selected': True if printer == self.printer_name else False
            }

            detaileds_status.append(detailed_status)

        return detaileds_status

    def set_printer(self, printer_name: str):
        # Ottieni l'elenco delle stampanti disponibili
        printers = self.conn.getPrinters()

        # Controlla se la stampante esiste
        if printer_name not in printers:
            raise ValueError(f"La stampante '{printer_name}' non è configurata.")

        try:
            # Imposta la stampante come predefinita
            self.conn.setDefault(printer_name)
            self.mode = 1
            return self.get_detailed_status()
        except cups.IPPError as e:
            raise ValueError(f"Errore nell'impostare la stampante come predefinita: {e}")

    def print_html(self, html_content):
        job_id = None
        message1 = None
        message2 = None

        # Controlla lo stato della stampante
        printers = self.conn.getPrinters()
        printer_status = printers.get(self.printer_name, {}).get('printer-state', None)

        if printer_status == cups.IPP_PRINTER_STOPPED:
            message1 = f"Avviso: La stampante '{self.printer_name}' è attualmente ferma o offline. La stampa rimarrà in coda."

        # Crea un file temporaneo per il contenuto HTML
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as temp_file:
            temp_file.write(html_content.encode('utf-8'))
            temp_file_path = temp_file.name

        # Invia il file HTML alla stampante
        try:
            job_id = self.conn.printFile(self.printer_name, temp_file_path, "HTML Print Job", {})
            message2 = f"Stampa inviata alla stampante '{self.printer_name}' con successo. La stampa rimarrà in coda se la stampante è offline."
        except Exception as e:
            raise ValueError(f"Errore durante la stampa: {e}")
        finally:
            # Rimuovi il file temporaneo
            os.unlink(temp_file_path)

        return job_id, message1, message2

    def get_job_status(self, job_id: int):
        jobs = self.conn.getJobs()
        return jobs.get(job_id)

    def cancel_job(self, job_id: int):
        try:
            self.conn.cancelJob(job_id)
        except cups.IPPError as e:
            raise ValueError(f"Errore nell'annullamento del lavoro {job_id}: {str(e)}")

    def cancel_jobs(self):
        jobs = self.get_active_jobs()
        for job in jobs:
            try:
                self.cancel_job(job["id"])
            except Exception as e:
                lb_log.error(e)

    def get_active_jobs(self):
        jobs = self.conn.getJobs(which_jobs='not-completed')
        detaileds_job = []
        for job in jobs:
            detailed_job = self.get_detailed_job_info(job)
            detaileds_job.append(detailed_job)
        return detaileds_job

    def get_job_state_description(self, state: int):
        states = {
            3: "Pending",
            4: "In attesa di essere elaborato",
            5: "In elaborazione",
            6: "Fermato",
            7: "Annullato",
            8: "Abortito",
            9: "Completato"
        }
        return states.get(state, f"Stato sconosciuto ({state})")

    def get_detailed_job_info(self, job_id: int):
        try:
            job_attrs = self.conn.getJobAttributes(job_id)
            lb_log.warning(job_attrs)
            return {
                'id': job_id,
                'stato': self.get_job_state_description(job_attrs.get('job-state', 0)),
                'dimensione': f"{job_attrs.get('job-k-octets', 0)} KB",
                'pagine': job_attrs.get('job-impressions-completed', 'Sconosciuto'),
                'priorità': job_attrs.get('job-priority', 50),
                'ora_creazione': dt.datetime.fromtimestamp(job_attrs.get('time-at-creation', 0))
            }
        except cups.IPPError:
            return None