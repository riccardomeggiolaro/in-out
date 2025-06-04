import cups
import tempfile
import os
from typing import List
import libs.lb_log as lb_log
import datetime as dt
from weasyprint import HTML

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

    def check_subsystem_connection(self):
        try:
            # Tentiamo di connetterci a CUPS senza cercare le stampanti
            return True if self.conn.getPrinters() else False  # Chiamata che verifica la connessione
        except cups.IPPError as e:
            # Gestisce errori relativi al server CUPS
            return f"Errore CUPS: {e}"
        except Exception as e:
            # Gestisce altre eccezioni generiche
            return f"Errore nella connessione a CUPS: {str(e)}"

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
            'cups-waiting-for-job-completed': 'In attesa di completamento stampa'
        }
        
        return [reason_descriptions.get(reason, reason) for reason in reasons]

    def get_detailed_status(self, printer_name: str):
        status = self.get_printer_status(printer_name=printer_name)

        return {
            'stampante': printer_name,
            'nome': printer_name if status.get('printer-info') else 'Sconosciuto',
            'printer-uri': status.get('printer-uri-supported', 'Sconosciuto'),
            'stato': self.get_printer_state_description(status.get('printer-state')),
            'messaggi': self.interpret_state_reasons(status.get('printer-state-reasons', [])),
            'modello': status.get('printer-make-and-model', 'Sconosciuto'),
            'condivisa': 'Sì' if status.get('printer-is-shared') else 'No',
            'uri_dispositivo': status.get('device-uri', 'Sconosciuto')
        }
        
    def get_list_printers_name(self):
        return [printer['nome'] for printer in self.get_list_printers()]

    def get_printer_status(self, printer_name: str):
        try:
            printers = self.conn.getPrinters()
            return printers.get(printer_name, {})
        except Exception as e:
            lb_log.error(f"Errore nella gestione delle stampanti: {e}")
            return {}

    def get_list_printers(self):
        try:
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
        except Exception as e:
            lb_log.error(f"Errore nella gestione delle stampanti: {e}")
            return []

    def get_printer_default(self):
        try:
            return self.conn.getDefault()
        except Exception as e:
            lb_log.error(f"Errore nella ricerca della stampante predefinita: {e}")
            return None

    def print_html(self, html_content, printer_name: str):
        job_id = None
        message1 = None
        message2 = None

        # Gestione del caso in cui printer_name è None
        if not printer_name:
            message1 = "Stampante non specificata."
            message2 = "Stampa non inviata."
            return job_id, message1, message2

        try:
            printers = self.conn.getPrinters()
            if printer_name not in printers:
                message1 = f"Stampante '{printer_name}' non trovata."
                message2 = "Stampa non inviata."
                return job_id, message1, message2

            # Controlla lo stato della stampante
            printer_status = printers[printer_name].get('printer-state', None)

            # Gestione stampante offline
            if printer_status == cups.IPP_PRINTER_STOPPED:
                message1 = f"Avviso: La stampante '{printer_name}' è attualmente ferma o offline. La stampa rimarrà in coda."

            # Crea file temporanei per HTML e PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as html_file, \
                 tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as pdf_file:
                
                # Salva il contenuto HTML
                html_file.write(html_content.encode('utf-8'))
                html_file.flush()

                try:
                    # Converti HTML in PDF
                    HTML(filename=html_file.name).write_pdf(pdf_file.name)

                    # Imposta le opzioni di stampa
                    options = {
                        'orientation-requested': '3',  # 3 = portrait (verticale)
                        'landscape': '0',             # 0 = disabilita orientamento orizzontale
                        'fit-to-page': 'true'        # Adatta alla pagina
                    }

                    # Stampa il PDF
                    job_id = self.conn.printFile(
                        printer_name,
                        pdf_file.name,
                        "HTML to PDF Print Job",
                        options
                    )
                    message2 = f"Stampa inviata alla stampante '{printer_name}' con successo."
                
                except Exception as e:
                    message2 = f"Errore durante la conversione/stampa: {e}"
                
                finally:
                    # Rimuovi i file temporanei
                    os.unlink(html_file.name)
                    os.unlink(pdf_file.name)

        except Exception as e:
            message1 = f"Errore nella gestione delle stampanti: {e}"
            message2 = "Stampa non inviata."

        return job_id, message1, message2
    
printer = HTMLPrinter()