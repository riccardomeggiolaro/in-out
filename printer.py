import cups
import tempfile

import cups
import tempfile

def print_html(html_content, printer_name=None):
    """
    Stampa una stringa HTML utilizzando CUPS.
    Se la stampante è offline, il lavoro rimarrà in coda fino a quando non sarà disponibile.

    Args:
        html_content (str): Il contenuto HTML da stampare.
        printer_name (str): Nome della stampante. Se None, utilizza la stampante predefinita.
    """
    # Connessione al server CUPS
    conn = cups.Connection()

    # Usa la stampante predefinita se non specificato
    if printer_name is None:
        printer_name = conn.getDefault()

    if not printer_name:
        raise ValueError("Nessuna stampante predefinita trovata e nessuna stampante specificata.")

    # Controlla lo stato della stampante
    printers = conn.getPrinters()
    printer_status = printers.get(printer_name, {}).get('printer-state', None)

    if printer_status == cups.IPP_PRINTER_STOPPED:
        print(f"Avviso: La stampante '{printer_name}' è attualmente ferma o offline. La stampa rimarrà in coda.")

    # Crea un file temporaneo per il contenuto HTML
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as temp_file:
        temp_file.write(html_content.encode('utf-8'))
        temp_file_path = temp_file.name

    # Invia il file HTML alla stampante
    try:
        conn.printFile(printer_name, temp_file_path, "HTML Print Job", {})
        print(f"Stampa inviata alla stampante '{printer_name}' con successo. La stampa rimarrà in coda se la stampante è offline.")
    except Exception as e:
        print(f"Errore durante la stampa: {e}")
    finally:
        # Rimuovi il file temporaneo
        import os
        os.unlink(temp_file_path)

if __name__ == "__main__":
    printer_name = "OfficeJet-Pro-8720"
    html = f"""
    <html>
        <body>
            <h1>Benvenuto</h1>
            <p>Questo è un test di stampa. {printer_name}</p>
        </body>
    </html>
    """
    print_html(html, printer_name=printer_name)