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
    def __init__(self):
        self.conn = cups.Connection()

    def close_connection(self):
        # Explicitly delete the connection object to clean up
        del self.conn
        print("CUPS connection closed.")

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

    def get_detailed_status(self, printer_name: str):
        status = self.get_printer_status()
        
        detailed_status = {
            'nome': printer_name if status.get('printer-info') else 'Sconosciuto',
            'stato': self.get_printer_state_description(status.get('printer-state')),
            'messaggi': self.interpret_state_reasons(status.get('printer-state-reasons', [])),
            'modello': status.get('printer-make-and-model', 'Sconosciuto'),
            'condivisa': 'Sì' if status.get('printer-is-shared') else 'No',
            'uri_dispositivo': status.get('device-uri', 'Sconosciuto')
        }
        
        return detailed_status

    def get_printer_status(self, printer_name: str):
        printers = self.conn.getPrinters()
        return printers.get(printer_name, {})

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
                'uri_dispositivo': status.get('device-uri', 'Sconosciuto')
            }

            detaileds_status.append(detailed_status)

        return detaileds_status

    def get_list_printers_name(self):
        return [printer['nome'] for printer in self.get_list_printers()]

    def get_printer_default(self):
        return self.conn.getDefault()

    def print_html(self, html_content, printer_name: str):
        job_id = None
        message1 = None
        message2 = None

        # Controlla lo stato della stampante
        printers = self.conn.getPrinters()
        printer_status = printers.get(printer_name, {}).get('printer-state', None)

        if printer_status == cups.IPP_PRINTER_STOPPED:
            message1 = f"Avviso: La stampante '{printer_name}' è attualmente ferma o offline. La stampa rimarrà in coda."

        # Crea un file temporaneo per il contenuto HTML
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as temp_file:
            temp_file.write(html_content.encode('utf-8'))
            temp_file_path = temp_file.name

        # Invia il file HTML alla stampante
        try:
            job_id = self.conn.printFile(printer_name, temp_file_path, "HTML Print Job", {})
            message2 = f"Stampa inviata alla stampante '{printer_name}' con successo. La stampa rimarrà in coda se la stampante è offline."
        except Exception as e:
            raise ValueError(f"Errore durante la stampa: {e}")
        finally:
            # Rimuovi il file temporaneo
            os.unlink(temp_file_path)

        return job_id, message1, message2

    def get_job_status(self, job_id: int):
        jobs = self.conn.getJobs()
        return jobs.get(job_id)

    def cancel_job(self, printer_name: str, job_id: int):
        try:
            # Ottieni le informazioni sul lavoro di stampa
            job_attributes = self.conn.getJobAttributes(job_id)
            
            # Verifica se la stampante associata al lavoro corrisponde a quella passata
            if job_attributes['printer-name'] == printer_name:
                self.conn.cancelJob(job_id)
            else:
                raise ValueError(f"Il lavoro {job_id} non appartiene alla stampante {printer_name}.")
        
        except cups.IPPError as e:
            raise ValueError(f"Errore nell'annullamento del lavoro {job_id}: {str(e)}")
        except KeyError:
            raise ValueError(f"Impossibile ottenere le informazioni sul lavoro {job_id}.")

    def cancel_all_jobs(self, printer_name: str):
        try:
            # Ottieni tutti i lavori di stampa
            jobs = self.conn.getJobs()
            
            # Filtra i lavori che appartengono alla stampante specificata
            jobs_to_cancel = [job_id for job_id, job_info in jobs.items() if job_info['printer-name'] == printer_name]
            
            # Annulla tutti i lavori associati alla stampante
            for job_id in jobs_to_cancel:
                self.conn.cancelJob(job_id)

            return len(jobs_to_cancel)
        except cups.IPPError as e:
            raise ValueError(f"Errore nell'annullamento dei lavori per la stampante {printer_name}: {str(e)}")

    def get_active_jobs(self, printer_name: str):
        jobs = self.conn.getJobs(which_jobs='not-completed')
        detaileds_job = []
        for job in jobs:
            detailed_job = self.get_detailed_job_info(job)
            if detailed_job["printer_name"] == printer_name:
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

            # Extract the printer name from the job attributes
            printer_name = job_attrs.get('printer', 'Unknown Printer')

            return {
                'id': job_id,
                'stato': self.get_job_state_description(job_attrs.get('job-state', 0)),
                'dimensione': f"{job_attrs.get('job-k-octets', 0)} KB",
                'pagine': job_attrs.get('job-impressions-completed', 'Sconosciuto'),
                'priorità': job_attrs.get('job-priority', 50),
                'ora_creazione': dt.datetime.fromtimestamp(job_attrs.get('time-at-creation', 0)),
                'printer_name': printer_name
            }
        except cups.IPPError:
            return None
    
printer = HTMLPrinter()