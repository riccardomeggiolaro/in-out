"""
CSV Folder Watcher
- Monitora una cartella per nuovi file CSV (watchdog)
- Estrae tutto il contenuto e lo stampa a console
- Elimina il file dopo l'elaborazione
"""

import os
import sys
import time
import csv
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- Configurazione ---
WATCH_DIR = os.environ.get("WATCH_DIR", "/var/opt/in-out/csv")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class CSVHandler(FileSystemEventHandler):
    """Handler che reagisce alla creazione di nuovi file CSV."""

    def on_created(self, event):
        if event.is_directory:
            return

        filepath = Path(event.src_path)

        if filepath.suffix.lower() != ".csv":
            return

        logger.info(f"Nuovo CSV rilevato: {filepath.name}")

        # Piccolo delay per assicurarsi che la scrittura del file sia completata
        time.sleep(0.5)

        try:
            self._process_and_delete(filepath)
        except Exception as e:
            logger.error(f"Errore nell'elaborazione di {filepath.name}: {e}")

    def _process_and_delete(self, filepath: Path):
        """Legge il CSV, stampa il contenuto e lo elimina."""

        with open(filepath, newline="", encoding="utf-8") as f:
            # Rileva automaticamente il delimitatore
            sample = f.read(4096)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample)
            except csv.Error:
                dialect = csv.excel  # fallback a virgola

            reader = csv.DictReader(f, dialect=dialect)

            rows = list(reader)

            if not rows:
                logger.warning(f"{filepath.name} è vuoto, nessun dato da elaborare.")
            else:
                headers = reader.fieldnames
                logger.info(f"File: {filepath.name} | Colonne: {headers} | Righe: {len(rows)}")
                logger.info("-" * 60)

                for i, row in enumerate(rows, start=1):
                    logger.info(f"  Riga {i}: {dict(row)}")

                logger.info("-" * 60)

        # Elimina il file
        filepath.unlink()
        logger.info(f"File eliminato: {filepath.name}\n")


def main():
    watch_path = Path(WATCH_DIR)
    watch_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Monitoraggio avviato su: {watch_path.resolve()}")
    logger.info("In attesa di nuovi file CSV... (Ctrl+C per uscire)\n")

    handler = CSVHandler()
    observer = Observer()
    observer.schedule(handler, str(watch_path), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Arresto in corso...")
        observer.stop()

    observer.join()
    logger.info("Watcher terminato.")


if __name__ == "__main__":
    main()