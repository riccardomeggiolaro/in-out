"""
CSV Folder Watcher → Oracle DB
- Monitora una cartella per nuovi file CSV (watchdog)
- Mappa i 25 campi del formato pesatura sulla tabella PESA_BA.ARCHIVIO
- Salva ogni riga nel database Oracle
- Elimina il file dopo l'elaborazione
"""

import os
import time
import csv
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import oracledb

# --- Configurazione ---
WATCH_DIR   = os.environ.get("WATCH_DIR",   "/var/opt/in-out/csv")
LOG_LEVEL   = os.environ.get("LOG_LEVEL",   "INFO")

# Connessione Oracle
ORA_USER    = os.environ.get("ORA_USER",    "PESA_BA")
ORA_PASS    = os.environ.get("ORA_PASS",    "318101")
ORA_DSN     = os.environ.get("ORA_DSN",     "localhost:1521/XEPDB1")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mapping CSV → ARCHIVIO
# ---------------------------------------------------------------------------
# Il CSV ha 25 campi posizionali (separatore ;), senza header.
# Indici 0-based:
#   0  tipo_soggetto         → CLIENTE (tipo soggetto, es. "Cliente")
#   1  id_soggetto           → (non mappato direttamente)
#   2  ragione_sociale_sogg  → CLIENTE1
#   3  cell_soggetto         → (non presente in ARCHIVIO, ignorato)
#   4  cfpiva_soggetto       → (ignorato)
#   5  id_vettore            → (ignorato)
#   6  ragione_sociale_vett  → VETTORE
#   7  cell_vettore          → (ignorato)
#   8  cfpiva_vettore        → (ignorato)
#   9  id_autista            → (ignorato)
#  10  ragione_sociale_aut   → VETTORE1
#  11  cell_autista          → (ignorato)
#  12  id_veicolo            → (ignorato)
#  13  targa_veicolo         → TARGA
#  14  descrizione_veicolo   → RIMORCHIO (campo più vicino disponibile)
#  15  id_materiale          → (ignorato)
#  16  descrizione_materiale → PRODOTTO / PRODOTTO1
#  17  note                  → NOTE
#  18  referenza_documento   → BOLLA
#  19  data1  (DD/MM/YYYY HH:MM) → DATA1_STR (stringa) + DATA1 (stringa compat.)
#  20  pid1                  → CK1
#  21  peso1                 → PESO1
#  22  data2  (DD/MM/YYYY HH:MM) → DATA2_STR + DATA2
#  23  pid2                  → CK2
#  24  peso2                 → PESO2
#
# NETTO = |PESO1 - PESO2|
# TIPO  = 'E' (entrata) per convenzione, modificabile
# ID    = sequenza ottenuta da ARCHIVIO_SEQ (creata se non esiste)
# STATO_IMPORTAZIONE = 0 (il trigger lo gestisce già, ma lo impostiamo esplicitamente)
# ---------------------------------------------------------------------------

INSERT_SQL = """
INSERT INTO PESA_BA.ARCHIVIO (
    ID, TIPO, BOLLA, NOTE,
    CLIENTE, CLIENTE1,
    FORNITORE, FORNITORE1,
    PRODOTTO, PRODOTTO1,
    VETTORE, VETTORE1,
    DESCR, TARGA, RIMORCHIO,
    PESO1, CK1,
    PESO2, CK2,
    NETTO,
    DATA1, ORA1,
    DATA2, ORA2,
    DATA1_STR, DATA2_STR,
    STATO_IMPORTAZIONE
) VALUES (
    PESA_BA.ARCHIVIO_SEQ.NEXTVAL, :tipo, :bolla, :note,
    :cliente, :cliente1,
    :fornitore, :fornitore1,
    :prodotto, :prodotto1,
    :vettore, :vettore1,
    :descr, :targa, :rimorchio,
    :peso1, :ck1,
    :peso2, :ck2,
    :netto,
    :data1, :ora1,
    :data2, :ora2,
    :data1_str, :data2_str,
    0
)
"""

CREATE_SEQ_SQL = """
BEGIN
    EXECUTE IMMEDIATE 'CREATE SEQUENCE PESA_BA.ARCHIVIO_SEQ
        START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -955 THEN RAISE; END IF; -- -955 = già esiste
END;
"""


def get_connection():
    """Apre una connessione Oracle thin (nessun client necessario)."""
    return oracledb.connect(user=ORA_USER, password=ORA_PASS, dsn=ORA_DSN)


def ensure_sequence():
    """Crea la sequenza ARCHIVIO_SEQ se non esiste."""
    with get_connection() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(CREATE_SEQ_SQL)
    logger.info("Sequenza ARCHIVIO_SEQ verificata/creata.")


def split_datetime(dt_str: str):
    """
    Divide 'DD/MM/YYYY HH:MM' in (data_str, ora_str).
    Restituisce ('', '') se il valore è vuoto o malformato.
    """
    dt_str = (dt_str or "").strip()
    if not dt_str:
        return "", ""
    parts = dt_str.split(" ", 1)
    data = parts[0] if len(parts) > 0 else ""
    ora  = parts[1] if len(parts) > 1 else ""
    return data, ora


def row_to_params(fields: list) -> dict:
    """
    Converte la lista di 25 campi posizionali nel dizionario
    dei parametri per INSERT_SQL.
    """
    def f(idx):
        """Ritorna il campo all'indice idx, o stringa vuota se mancante."""
        return fields[idx].strip() if idx < len(fields) else ""

    def to_num(val):
        try:
            return float(val.strip()) if val.strip() else None
        except ValueError:
            return None

    data1, ora1 = split_datetime(f(19))
    data2, ora2 = split_datetime(f(22))

    peso1 = to_num(f(21))
    peso2 = to_num(f(24))
    netto = abs((peso1 or 0) - (peso2 or 0))

    return {
        "tipo":       "E",          # Entrata — adatta se necessario
        "bolla":      f(18)[:30],   # referenza_documento → BOLLA (max 30)
        "note":       f(17)[:60],   # note → NOTE (max 60)
        "cliente":    f(0)[:60],    # tipo_soggetto
        "cliente1":   f(2)[:60],    # ragione_sociale_soggetto
        "fornitore":  "",
        "fornitore1": "",
        "prodotto":   f(16)[:60],   # descrizione_materiale
        "prodotto1":  f(16)[:60],
        "vettore":    f(6)[:60],    # ragione_sociale_vettore
        "vettore1":   f(10)[:60],   # ragione_sociale_autista
        "descr":      f(14)[:15],   # descrizione_veicolo
        "targa":      f(13)[:10],   # targa_veicolo
        "rimorchio":  "",
        "peso1":      peso1,
        "ck1":        f(20)[:30],   # pid1
        "peso2":      peso2,
        "ck2":        f(23)[:30],   # pid2
        "netto":      netto,
        "data1":      data1[:20],
        "ora1":       ora1[:20],
        "data2":      data2[:20],
        "ora2":       ora2[:20],
        "data1_str":  f(19)[:20],
        "data2_str":  f(22)[:20],
    }


class CSVHandler(FileSystemEventHandler):
    """Handler che reagisce alla creazione di nuovi file CSV."""

    def on_created(self, event):
        if event.is_directory:
            return

        filepath = Path(event.src_path)
        if filepath.suffix.lower() != ".csv":
            return

        logger.info(f"Nuovo CSV rilevato: {filepath.name}")
        time.sleep(0.5)  # attende fine scrittura

        try:
            self._process_and_delete(filepath)
        except Exception as e:
            logger.error(f"Errore nell'elaborazione di {filepath.name}: {e}")

    def _process_and_delete(self, filepath: Path):
        """Legge il CSV, salva ogni riga in Oracle, poi elimina il file."""

        with open(filepath, newline="", encoding="utf-8") as f:
            # Rileva delimitatore automaticamente
            sample = f.read(4096)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample)
            except csv.Error:
                dialect = csv.excel  # fallback virgola

            reader = csv.reader(f, dialect=dialect)
            rows = list(reader)

        if not rows:
            logger.warning(f"{filepath.name} è vuoto, nessun dato da elaborare.")
            filepath.unlink()
            return

        logger.info(f"File: {filepath.name} | Righe da inserire: {len(rows)}")

        inserted = 0
        errors   = 0

        with get_connection() as conn:
            with conn.cursor() as cur:
                for i, fields in enumerate(rows, start=1):
                    try:
                        params = row_to_params(fields)
                        cur.execute(INSERT_SQL, params)
                        inserted += 1
                        logger.debug(f"  Riga {i} inserita — BOLLA={params['bolla']}")
                    except Exception as e:
                        errors += 1
                        logger.error(f"  Riga {i} ERRORE: {e} | dati={fields}")
            conn.commit()

        logger.info(
            f"Completato: {inserted} righe inserite, {errors} errori — {filepath.name}"
        )

        filepath.unlink()
        logger.info(f"File eliminato: {filepath.name}\n")


def process_existing(watch_path: Path, handler: "CSVHandler"):
    """Elabora i file CSV già presenti nella cartella all'avvio."""
    existing = sorted(watch_path.glob("*.csv"))
    if not existing:
        logger.info("Nessun file CSV preesistente trovato.")
        return

    logger.info(f"Trovati {len(existing)} file CSV preesistenti — elaborazione in corso...")
    for filepath in existing:
        try:
            handler._process_and_delete(filepath)
        except Exception as e:
            logger.error(f"Errore elaborando {filepath.name}: {e}")
    logger.info("Elaborazione file preesistenti completata.\n")


def main():
    watch_path = Path(WATCH_DIR)
    watch_path.mkdir(parents=True, exist_ok=True)

    # Verifica connessione e sequenza all'avvio
    try:
        ensure_sequence()
        logger.info(f"Connessione Oracle OK → {ORA_DSN}")
    except Exception as e:
        logger.error(f"Impossibile connettersi a Oracle: {e}")
        raise SystemExit(1)

    handler = CSVHandler()

    # Carica i file già presenti prima di avviare il watcher
    process_existing(watch_path, handler)

    logger.info(f"Monitoraggio avviato su: {watch_path.resolve()}")
    logger.info("In attesa di nuovi file CSV... (Ctrl+C per uscire)\n")

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