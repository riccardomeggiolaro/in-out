import cups
import tempfile
import os
from typing import List
import libs.lb_log as lb_log
import datetime as dt
from weasyprint import HTML, CSS
from lxml import html

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

    def generate_pdf_from_html(self, html_content):
        """
        Genera un PDF con gestione corretta dei margini per WeasyPrint
        """
        # Genera il PDF
        pdf_bytes = None
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as html_file, \
            tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as pdf_file:
            
            html_file.write(html_content.encode('utf-8'))
            html_file.flush()
            
            try:
                weasy_html = HTML(filename=html_file.name)
                
                weasy_html.write_pdf(pdf_file.name)
                    
                with open(pdf_file.name, "rb") as f:
                    pdf_bytes = f.read()
            finally:
                os.unlink(html_file.name)
                os.unlink(pdf_file.name)
        
        return pdf_bytes

    def print_pdf(self, pdf_bytes, printer_name: str, number_of_prints: int = 1):
        """
        Invia un file PDF (bytes) alla stampante specificata.
        Auto-rileva stampanti termiche e ottimizza la qualità.
        """
        import tempfile
        import os

        job_id = None
        message1 = None
        message2 = None

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

            printer_status = printers[printer_name].get('printer-state', None)
            if printer_status == cups.IPP_PRINTER_STOPPED:
                message1 = f"Avviso: La stampante '{printer_name}' è attualmente ferma o offline."

            # AUTO-DETECT: Rileva se è stampante termica
            printer_info = printers[printer_name]
            driver = printer_info.get('printer-make-and-model', '').lower()
            
            # Criteri di rilevamento
            is_thermal = (
                'rastertotmt' in driver or
                'thermal' in driver or
                'escpos' in driver or
                'tm-' in driver.lower() or
                'star' in driver.lower()
            )
            
            # Fallback: controlla larghezza carta (termiche < 100mm = 283 punti a 72dpi)
            if not is_thermal:
                try:
                    ppd_path = self.conn.getPPD(printer_name)
                    with open(ppd_path, 'r') as f:
                        ppd_content = f.read()
                        # Cerca larghezza in punti (es. PageSize[204 841.8])
                        import re
                        match = re.search(r'PageSize\[(\d+\.?\d*)\s+\d+', ppd_content)
                        if match:
                            width = float(match.group(1))
                            is_thermal = width < 283  # ~100mm
                except:
                    pass  # Se fallisce, assume NON termica
            
            # STAMPA: Logica differenziata
            if is_thermal:
                # === STAMPANTE TERMICA: Pre-processing per qualità ===
                try:
                    import pypdfium2 as pdfium
                    from PIL import Image
                except ImportError:
                    message1 = "Libreria pypdfium2 mancante. Installa con: pip install pypdfium2"
                    message2 = "Stampa non inviata."
                    return job_id, message1, message2
                
                pdf = pdfium.PdfDocument(pdf_bytes)
                page = pdf[0]
                
                # Rendering a 203dpi (risoluzione nativa stampanti termiche)
                bitmap = page.render(scale=203/72, rotation=0)
                pil_image = bitmap.to_pil()
                
                # Converti in B/N puro con threshold (elimina sgranatura)
                grayscale = pil_image.convert('L')
                bw_image = grayscale.point(lambda x: 0 if x < 128 else 255, mode='1')
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as img_file:
                    bw_image.save(img_file.name, format='PNG', optimize=True)
                    
                    try:
                        options = {
                            'copies': str(number_of_prints),
                            'TmtSpeed': '4',  # Velocità lenta per qualità massima
                            'scaling': '100'
                        }
                        
                        job_id = self.conn.printFile(
                            printer_name,
                            img_file.name,
                            "Thermal Print Job",
                            options
                        )
                        message2 = f"Stampa termica inviata a '{printer_name}' ({number_of_prints} copie)."
                    finally:
                        os.unlink(img_file.name)
                        
                pdf.close()
                
            else:
                # === STAMPANTE A4: Stampa PDF diretto ===
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as pdf_file:
                    pdf_file.write(pdf_bytes)
                    pdf_file.flush()
                    
                    try:
                        options = {
                            'orientation-requested': '3',
                            'landscape': '0',
                            'fit-to-page': 'true',
                            'copies': str(number_of_prints),
                        }
                        
                        job_id = self.conn.printFile(
                            printer_name,
                            pdf_file.name,
                            "PDF Print Job",
                            options
                        )
                        message2 = f"Stampa inviata a '{printer_name}' ({number_of_prints} copie)."
                    finally:
                        os.unlink(pdf_file.name)

        except Exception as e:
            message1 = f"Errore nella gestione delle stampanti: {e}"
            message2 = "Stampa non inviata."

        return job_id, message1, message2

    def print_html(self, html_content, printer_name: str, number_of_prints: int = 1):
        pdf_bytes = self.generate_pdf_from_html(html_content)
        job_id, message1, message2 = self.print_pdf(pdf_bytes, printer_name, number_of_prints)
        return pdf_bytes, job_id, message1, message2
    
printer = HTMLPrinter()