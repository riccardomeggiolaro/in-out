"""
CSV Folder Watcher → Oracle DB
- Monitora una cartella per nuovi file CSV (watchdog)
- Carica i dati di pesatura nella tabella PESA_BA.ARCHIVIO
- Entrata (solo 1a pesata): INSERT con STATO_IMPORTAZIONE = 0
- Uscita (2a pesata): UPDATE del record di entrata (cercato per CK1 = pid1)
  con STATO_IMPORTAZIONE = 1; se il record non esiste viene inserito completo
- Elimina il file dopo l'elaborazione (in caso di errori lo sposta in ./errori)
"""

import os
import time
import csv
import logging
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import oracledb

# --- Configurazione ---
WATCH_DIR   = os.environ.get("WATCH_DIR",   "/var/opt/in-out/csv")
ERROR_DIR   = os.environ.get("ERROR_DIR",   "")  # default: <WATCH_DIR>/errori
LOG_LEVEL   = os.environ.get("LOG_LEVEL",   "INFO")

# Connessione Oracle
ORA_USER    = os.environ.get("ORA_USER",    "PESA_BA")
ORA_PASS    = os.environ.get("ORA_PASS",    "318101")
ORA_DSN     = os.environ.get("ORA_DSN",     "localhost:1521/XEPDB1")
ORA_SCHEMA  = os.environ.get("ORA_SCHEMA",  "PESA_BA")
ORA_TABLE   = "ARCHIVIO"

TIPO_PESATA = "P"

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Formato CSV (separatore ;, senza header, una pesata per riga)
# ---------------------------------------------------------------------------
#   0  tipo_soggetto              (ignorato)
#   1  id_soggetto                (ignorato)
#   2  ragione_sociale_soggetto   (ignorato)
#   3  cell_soggetto              (ignorato)
#   4  cfpiva_soggetto            (ignorato)
#   5  id_vettore                 (ignorato)
#   6  ragione_sociale_vettore    (ignorato)
#   7  cell_vettore               (ignorato)
#   8  cfpiva_vettore             (ignorato)
#   9  id_autista                 (ignorato)
#  10  ragione_sociale_autista    (ignorato)
#  11  cell_autista               (ignorato)
#  12  id_tessera                 (ignorato)
#  13  numero_tessera             → CLIENTE1
#  14  codice_tessera             → DESCR
#  15  id_veicolo                 (ignorato)
#  16  targa_veicolo              (ignorato)
#  17  descrizione_veicolo        (ignorato)
#  18  id_materiale               (ignorato)
#  19  descrizione_materiale      (ignorato)
#  20  note                       (ignorato)
#  21  referenza_documento        (ignorato)
#  22  data1 (DD/MM/YYYY HH:MM)   → DATA1 + ORA1
#  23  pid1                       → CK1
#  24  peso1                      → PESO1
#  25  data2 (DD/MM/YYYY HH:MM)   → DATA2 + ORA2
#  26  pid2                       → CK2
#  27  peso2                      → PESO2
#  28  netto                      → NETTO (solo uscita)
#
# TIPO = 'P' fisso
# ID   = MAX(ID)+1 (con retry in caso di collisione)
# ---------------------------------------------------------------------------
IDX_NUMERO_TESSERA = 13
IDX_CODICE_TESSERA = 14
IDX_DATA1  = 22
IDX_PID1   = 23
IDX_PESO1  = 24
IDX_DATA2  = 25
IDX_PID2   = 26
IDX_PESO2  = 27
IDX_NETTO  = 28

# Lunghezze di default se non ricavabili dal dizionario dati
DEFAULT_LEN = {"CLIENTE1": 60, "DESCR": 15, "CK1": 30, "CK2": 30}

INSERT_RETRY = 5

# Metadati colonne ARCHIVIO (tipo e lunghezza), letti all'avvio
COLUMNS: dict = {}


def get_connection():
    """Apre una connessione Oracle thin (nessun client necessario)."""
    return oracledb.connect(user=ORA_USER, password=ORA_PASS, dsn=ORA_DSN)


def load_columns_metadata():
    """Legge tipo e lunghezza delle colonne di ARCHIVIO per adattare i valori."""
    global COLUMNS
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COLUMN_NAME, DATA_TYPE, CHAR_LENGTH
                  FROM ALL_TAB_COLUMNS
                 WHERE OWNER = :owner AND TABLE_NAME = :tab
                """,
                owner=ORA_SCHEMA.upper(), tab=ORA_TABLE,
            )
            COLUMNS = {
                name: {"type": dtype, "len": length}
                for name, dtype, length in cur.fetchall()
            }
    if not COLUMNS:
        raise RuntimeError(f"Tabella {ORA_SCHEMA}.{ORA_TABLE} non trovata o non accessibile")
    for col in ("DATA1", "ORA1", "DATA2", "ORA2"):
        logger.info(f"Colonna {col}: {COLUMNS.get(col, {}).get('type', 'N/D')}")


def col_type(col: str) -> str:
    return (COLUMNS.get(col, {}).get("type") or "VARCHAR2").upper()


def cut(col: str, value: str):
    """Tronca la stringa alla lunghezza della colonna; '' → None."""
    if not value:
        return None
    length = COLUMNS.get(col, {}).get("len") or DEFAULT_LEN.get(col)
    return value[:length] if length else value


def parse_datetime(dt_str: str):
    dt_str = (dt_str or "").strip()
    if not dt_str:
        return None
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y"):
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    logger.warning(f"Data non riconosciuta: '{dt_str}'")
    return None


def adapt_date(col: str, dt: datetime):
    """Valore per DATA1/DATA2 in base al tipo della colonna."""
    if dt is None:
        return None
    t = col_type(col)
    if t == "DATE" or t.startswith("TIMESTAMP"):
        return datetime(dt.year, dt.month, dt.day)
    return cut(col, dt.strftime("%Y-%m-%d"))


def adapt_time(col: str, dt: datetime):
    """Valore per ORA1/ORA2 in base al tipo della colonna (formato HH.MM)."""
    if dt is None:
        return None
    t = col_type(col)
    if t == "DATE" or t.startswith("TIMESTAMP"):
        return dt
    if t in ("NUMBER", "FLOAT", "BINARY_DOUBLE", "BINARY_FLOAT"):
        return float(f"{dt.hour}.{dt.minute:02d}")
    return cut(col, f"{dt.hour:02d}.{dt.minute:02d}")


def to_num(val: str):
    val = (val or "").strip().replace(",", ".")
    if not val:
        return None
    try:
        num = float(val)
        return int(num) if num.is_integer() else num
    except ValueError:
        return None


def row_to_record(fields: list) -> dict:
    """Converte la riga CSV nei valori delle colonne di ARCHIVIO."""
    def f(idx):
        return fields[idx].strip() if idx < len(fields) else ""

    dt1 = parse_datetime(f(IDX_DATA1))
    dt2 = parse_datetime(f(IDX_DATA2))
    peso1 = to_num(f(IDX_PESO1))
    peso2 = to_num(f(IDX_PESO2))

    is_uscita = peso2 is not None or dt2 is not None

    netto = None
    if is_uscita:
        netto = to_num(f(IDX_NETTO))
        if netto is None and peso1 is not None and peso2 is not None:
            netto = abs(peso1 - peso2)

    return {
        "is_uscita": is_uscita,
        "values": {
            "TIPO":     TIPO_PESATA,
            "CLIENTE1": cut("CLIENTE1", f(IDX_NUMERO_TESSERA)),
            "DESCR":    cut("DESCR", f(IDX_CODICE_TESSERA)),
            "DATA1":    adapt_date("DATA1", dt1),
            "ORA1":     adapt_time("ORA1", dt1),
            "CK1":      cut("CK1", f(IDX_PID1)),
            "PESO1":    peso1,
            "DATA2":    adapt_date("DATA2", dt2),
            "ORA2":     adapt_time("ORA2", dt2),
            "CK2":      cut("CK2", f(IDX_PID2)),
            "PESO2":    peso2,
            "NETTO":    netto,
            "STATO_IMPORTAZIONE": 1 if is_uscita else 0,
        },
    }


def table() -> str:
    return f"{ORA_SCHEMA}.{ORA_TABLE}"


def insert_record(cur, values: dict) -> int:
    """INSERT con ID = MAX(ID)+1; riprova in caso di chiave duplicata."""
    cols = list(values.keys())
    sql = (
        f"INSERT INTO {table()} (ID, {', '.join(cols)}) "
        f"VALUES (:ID, {', '.join(':' + c for c in cols)})"
    )
    for attempt in range(1, INSERT_RETRY + 1):
        cur.execute(f"SELECT NVL(MAX(ID), 0) + 1 FROM {table()}")
        new_id = cur.fetchone()[0]
        try:
            cur.execute(sql, {"ID": new_id, **values})
            return new_id
        except oracledb.IntegrityError as e:
            if "ORA-00001" in str(e) and attempt < INSERT_RETRY:
                time.sleep(0.2)
                continue
            raise


def update_uscita(cur, values: dict) -> int:
    """Aggiorna il record di entrata (CK1 = pid1) con i dati di uscita."""
    upd_cols = ["DATA2", "ORA2", "CK2", "PESO2", "NETTO", "STATO_IMPORTAZIONE"]
    # Aggiorna la tessera solo se presente nel CSV
    for c in ("CLIENTE1", "DESCR"):
        if values.get(c):
            upd_cols.append(c)
    params = {c: values[c] for c in upd_cols}
    params["ck1_key"] = values["CK1"]
    sql = (
        f"UPDATE {table()} SET {', '.join(f'{c} = :{c}' for c in upd_cols)} "
        f"WHERE CK1 = :ck1_key"
    )
    cur.execute(sql, params)
    return cur.rowcount


def save_row(cur, fields: list) -> str:
    rec = row_to_record(fields)
    values = rec["values"]
    if rec["is_uscita"] and values["CK1"]:
        n = update_uscita(cur, values)
        if n > 0:
            if n > 1:
                logger.warning(f"  CK1={values['CK1']}: aggiornati {n} record")
            return f"UPDATE uscita CK1={values['CK1']} CK2={values['CK2']}"
        logger.warning(f"  Entrata CK1={values['CK1']} non trovata: inserisco record completo")
    new_id = insert_record(cur, values)
    kind = "uscita" if rec["is_uscita"] else "entrata"
    return f"INSERT {kind} ID={new_id} CK1={values['CK1']} CK2={values['CK2']}"


def read_rows(filepath: Path) -> list:
    with open(filepath, newline="", encoding="utf-8-sig") as f:
        return [r for r in csv.reader(f, delimiter=";") if any(c.strip() for c in r)]


def move_to_errors(filepath: Path):
    err_dir = Path(ERROR_DIR) if ERROR_DIR else filepath.parent / "errori"
    err_dir.mkdir(parents=True, exist_ok=True)
    target = err_dir / filepath.name
    if target.exists():
        target = err_dir / f"{filepath.stem}_{datetime.now():%Y%m%d%H%M%S}{filepath.suffix}"
    filepath.replace(target)
    logger.error(f"File spostato in {target}")


def process_file(filepath: Path):
    """Legge il CSV, salva le righe in Oracle, poi elimina il file."""
    rows = read_rows(filepath)
    if not rows:
        logger.warning(f"{filepath.name} è vuoto, nessun dato da elaborare.")
        filepath.unlink()
        return

    logger.info(f"File: {filepath.name} | Righe: {len(rows)}")
    errors = 0
    with get_connection() as conn:
        with conn.cursor() as cur:
            for i, fields in enumerate(rows, start=1):
                try:
                    logger.info(f"  Riga {i}: {save_row(cur, fields)}")
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    errors += 1
                    logger.error(f"  Riga {i} ERRORE: {e} | dati={fields}")

    if errors:
        move_to_errors(filepath)
    else:
        filepath.unlink()
        logger.info(f"File eliminato: {filepath.name}\n")


class CSVHandler(FileSystemEventHandler):
    """Reagisce alla creazione (o rinomina) di file CSV."""

    def _handle(self, path: str):
        filepath = Path(path)
        if filepath.suffix.lower() != ".csv" or not filepath.exists():
            return
        logger.info(f"Nuovo CSV rilevato: {filepath.name}")
        time.sleep(0.5)  # attende fine scrittura
        try:
            process_file(filepath)
        except Exception as e:
            logger.error(f"Errore nell'elaborazione di {filepath.name}: {e}")

    def on_created(self, event):
        if not event.is_directory:
            self._handle(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._handle(event.dest_path)


def process_existing(watch_path: Path):
    """Elabora i file CSV già presenti nella cartella all'avvio."""
    existing = sorted(watch_path.glob("*.csv"), key=lambda p: p.stat().st_mtime)
    if not existing:
        logger.info("Nessun file CSV preesistente trovato.")
        return
    logger.info(f"Trovati {len(existing)} file CSV preesistenti — elaborazione in corso...")
    for filepath in existing:
        try:
            process_file(filepath)
        except Exception as e:
            logger.error(f"Errore elaborando {filepath.name}: {e}")
    logger.info("Elaborazione file preesistenti completata.\n")


def main():
    watch_path = Path(WATCH_DIR)
    watch_path.mkdir(parents=True, exist_ok=True)

    try:
        load_columns_metadata()
        logger.info(f"Connessione Oracle OK → {ORA_DSN}")
    except Exception as e:
        logger.error(f"Impossibile connettersi a Oracle: {e}")
        raise SystemExit(1)

    # Ordinati per data di modifica: l'entrata viene caricata prima dell'uscita
    process_existing(watch_path)

    logger.info(f"Monitoraggio avviato su: {watch_path.resolve()}")
    logger.info("In attesa di nuovi file CSV... (Ctrl+C per uscire)\n")

    observer = Observer()
    observer.schedule(CSVHandler(), str(watch_path), recursive=False)
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
