#!/usr/bin/env python3

"""
Sincronizza le prenotazioni aperte da AS400 (LIBDAT.CARARRP) nel database
principale dell'applicazione in-out (/var/opt/in-out/database.db).

Comportamento:
- Legge solo le prenotazioni filtrate (FEGUTS='', FEADCE='01', FEGVTS='',
  FEONDT=0, FEBZTM=0, FEJSUS IN ('C','S','H')).
- Per ogni riga crea/aggiorna le anagrafiche (Subject, Vector, Driver,
  Vehicle, Material, CardRegistry) con logica lookup-or-create.
- Upsert sull'Access: chiave = badge "AA-PPPPPPP" (anno-progressivo).
  Se l'accesso esiste già e ha status WAITING/OPEN aggiorna i campi;
  se è ENTERED/CLOSED lo salta (non sovrascrive pesate già fatte).
- Solo lettura sull'AS400: nessun UPDATE/DELETE sul sistema remoto.
- Rilanciabile quante volte si vuole (idempotente).

Script autonomo: non importa nulla dal progetto in-out. Scrive direttamente
nel database SQLite di in-out con il modulo standard sqlite3.

Dipendenze (Debian 13):
    sudo apt install unixodbc
    pip install pyodbc
    + driver "IBM i Access ODBC Driver" configurato in odbcinst.ini

Variabili d'ambiente (oppure file .env nella cartella dello script):
    AS400_SYSTEM=10.0.0.1
    AS400_UID=...
    AS400_PWD=...
    AS400_DRIVER="IBM i Access ODBC Driver"        (opzionale)
    MAIN_DB_PATH=/var/opt/in-out/database.db       (opzionale)
    TEST_DB_PATH=<cartella script>/test_as400.db   (opzionale)
    SAMPLE_DB_PATH=<cartella script>/sample_as400.db (opzionale)
    AS400_ENV_FILE=/percorso/.env                  (opzionale, file .env alternativo)

Uso:
    python3 as400.py                  # legge da AS400
    python3 as400.py --source local   # legge da test_as400.db
"""

import logging
import os
import sqlite3
import sys
from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional

# Cartella in cui si trova questo script: i percorsi di default sono relativi
# a questa cartella, così lo script funziona da qualunque posizione venga lanciato.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_env_file(path: str) -> None:
    """
    Carica le variabili da un file .env (formato CHIAVE=valore, righe '#' ignorate,
    'export ' iniziale ammesso, valori tra apici singoli o doppi).
    Le variabili già presenti nell'ambiente NON vengono sovrascritte.
    """
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):].strip()
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            os.environ.setdefault(key, value)


# .env: prima quello indicato da AS400_ENV_FILE, poi quello accanto allo script
_load_env_file(os.environ.get("AS400_ENV_FILE", os.path.join(SCRIPT_DIR, ".env")))

try:
    import pyodbc
except ImportError:
    pyodbc = None  # type: ignore  # non serve per il caricamento da staging

# ---------------------------------------------------------------------------
# Configurazione
# ---------------------------------------------------------------------------
AS400_DRIVER = os.environ.get("AS400_DRIVER", "IBM i Access ODBC Driver")

# Database principale di in-out (scritto direttamente con sqlite3)
MAIN_DB_PATH = os.environ.get("MAIN_DB_PATH", "/var/opt/in-out/database.db")

# Copie di controllo dei dati letti dall'AS400
TEST_DB_PATH   = os.environ.get("TEST_DB_PATH",   os.path.join(SCRIPT_DIR, "test_as400.db"))
SAMPLE_DB_PATH = os.environ.get("SAMPLE_DB_PATH", os.path.join(SCRIPT_DIR, "sample_as400.db"))

# Colonne esposte nel db di esempio (da column.txt)
SAMPLE_COLUMNS = [
    "FEMRA0",   # Anno del carico
    "FEE8A0",   # Progressivo
    "FEA335",   # Targa motrice
    "FEHCTY",   # Targa rimorchio
    "FEHBTY",   # Nome
    "FEJSUS",   # Carico/Scarico
    "FEG1TY",   # Note merce
    "FERSCC",   # Limite peso
    "FER5TS",   # Flag stampa peso
    "FERSTS",   # Tipo automezzo
    "FER3CC",   # Tara mezzo
    "FEFMCD",   # Riferimento documento (codice nazione)
]

STAGING_TABLE = "cararrp"
KEY_COLS = ("FEMRA0", "FEE8A0")  # anno + progressivo

# Filtro prenotazioni aperte (stesso del vecchio VBA)
SQL_SELECT = (
    "SELECT * FROM LIBDAT.CARARRP "
    "WHERE FEGUTS = '' AND FEADCE = '01' AND FEGVTS = '' "
    "AND FEONDT = 0 AND FEBZTM = 0 AND FEJSUS IN ('C','S','H')"
)

log = logging.getLogger("as400")


# ===========================================================================
# Helpers generici
# ===========================================================================

def _s(value) -> Optional[str]:
    """Stringa pulita o None se vuota/None."""
    if value is None:
        return None
    v = str(value).strip()
    return v if v else None


def _i(value) -> Optional[int]:
    """Intero o None."""
    if value is None:
        return None
    try:
        v = int(Decimal(str(value)))
        return v if v != 0 else None
    except Exception:
        return None


def _as400_date(value) -> Optional[datetime]:
    """
    Converte una data AS400 packed (CYYMMDD, es. 1260925 = 26/09/2026)
    in datetime. Restituisce None se valore == 0 o non valido.
    """
    if not value:
        return None
    try:
        v = int(Decimal(str(value)))
        if v == 0:
            return None
        # Formato CYYMMDD: C=secolo (1=2000), YY=anno, MM=mese, DD=giorno
        day   = v % 100
        month = (v // 100) % 100
        year  = (v // 10000) % 100
        cent  = (v // 1000000)
        full_year = 1900 + cent * 100 + year
        return datetime(full_year, month, day)
    except Exception:
        return None


def _as400_time(value) -> Optional[time]:
    """
    Converte un orario AS400 packed (HHMMSS, es. 143025 = 14:30:25)
    in time. Restituisce None se valore == 0 o non valido.
    """
    if not value:
        return None
    try:
        v = int(Decimal(str(value)))
        if v == 0:
            return None
        sec  = v % 100
        min_ = (v // 100) % 100
        hour = (v // 10000)
        return time(hour, min_, sec)
    except Exception:
        return None


def _as400_datetime(date_val, time_val) -> Optional[datetime]:
    """Combina data e ora AS400 in un datetime completo."""
    d = _as400_date(date_val)
    if d is None:
        return None
    t = _as400_time(time_val) or time(0, 0, 0)
    return datetime(d.year, d.month, d.day, t.hour, t.minute, t.second)


def _peso_kg(value) -> Optional[int]:
    """
    Converte un peso AS400 (packed 7.2, es. 12345 = 123.45 tonnellate)
    in chilogrammi interi.
    Formato: il valore numerico ha 2 decimali impliciti → valore / 100 = tonnellate
    → * 1000 = kg.
    """
    if value is None:
        return None
    try:
        d = Decimal(str(value))
        if d == 0:
            return None
        # Il tipo P 7.2 significa 2 cifre decimali già nel valore
        # Decimale già corretto da pyodbc; valore = tonnellate
        kg = int(d * 1000)
        return kg if kg > 0 else None
    except Exception:
        return None


def _tare_from_type(fersts: Optional[str]) -> Optional[int]:
    """
    FERSTS → Tara mezzo in kg:
        A = Autotreno      → 15000 kg
        M = Motrice        → 10000 kg
        B = Bilico         → 15000 kg
        C = Collettamista  → None (nessuna tara)
        altri              → None
    """
    mapping = {"A": 15000, "B": 15000, "M": 10000}
    if fersts:
        return mapping.get(fersts.strip().upper())
    return None


def _tare(fersts: Optional[str], fer3cc) -> Optional[int]:
    """
    Tara mezzo in kg:
        - FER3CC > 0 e diverso da 10000/15000 → valore di FER3CC (es. 15500)
        - altrimenti                           → tara standard da FERSTS
    Vale anche con targa vuota e per FERSTS = C o vuoto.
    """
    tare = _i(fer3cc)
    if tare and tare > 0 and tare not in (10000, 15000):
        return tare
    return _tare_from_type(fersts)


def _type_subject(fejsus: Optional[str]) -> str:
    """
    FEJSUS: C=Carico (cliente porta merce) → CUSTOMER
            S=Scarico (fornitore porta merce) → SUPPLIER
            H=Entrambi → SUPPLIER (default)
    """
    if fejsus == "C":
        return "CUSTOMER"
    return "SUPPLIER"
    """
    FEJSUS: C=Carico (cliente porta merce) → CUSTOMER
            S=Scarico (fornitore porta merce) → SUPPLIER
            H=Entrambi → SUPPLIER (default)
    """
    if fejsus == "C":
        return "CUSTOMER"
    return "SUPPLIER"


def _doc_ref(anno, progressivo) -> Optional[str]:
    """Chiave univoca AS400: 'AA-PPPPPPP'."""
    a = _i(anno)
    p = _i(progressivo)
    if a is None or p is None:
        return None
    return f"{a}-{p}"


# ===========================================================================
# Staging su SQLite (fase 1: copia grezza dall'AS400)
# ===========================================================================

def _to_sqlite(value):
    """Converte i tipi non accettati da sqlite3."""
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    return value


def load_staging(as400_conn) -> int:
    """
    Scarica tutte le righe filtrate da CARARRP in un SQLite di staging locale.
    Restituisce il numero di righe lette.
    """
    db = sqlite3.connect(TEST_DB_PATH, timeout=10)
    try:
        cur = as400_conn.cursor()
        cur.execute(SQL_SELECT)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()

        col_defs   = ", ".join(f'"{c}"' for c in cols)
        key_defs   = ", ".join(f'"{c}"' for c in KEY_COLS)
        placeholders = ", ".join("?" * len(cols))
        update_cols  = [c for c in cols if c not in KEY_COLS]
        set_defs   = ", ".join(f'"{c}" = excluded."{c}"' for c in update_cols)

        with db:
            db.execute(
                f'CREATE TABLE IF NOT EXISTS {STAGING_TABLE} ({col_defs}, UNIQUE({key_defs}))'
            )
            db.executemany(
                f"INSERT INTO {STAGING_TABLE} ({col_defs}) VALUES ({placeholders}) "
                f"ON CONFLICT({key_defs}) DO UPDATE SET {set_defs}",
                ([_to_sqlite(v) for v in row] for row in rows),
            )

        log.info("Staging: %d righe caricate in %s", len(rows), TEST_DB_PATH)
        return len(rows)
    finally:
        db.close()


def make_sample_db() -> int:
    """
    Crea SAMPLE_DB_PATH con solo le colonne di column.txt (SAMPLE_COLUMNS),
    copiando i dati da TEST_DB_PATH (staging completo).
    Restituisce il numero di righe scritte.
    """
    src = sqlite3.connect(TEST_DB_PATH)
    src.row_factory = sqlite3.Row
    try:
        col_list = ", ".join(SAMPLE_COLUMNS)
        rows = src.execute(f"SELECT {col_list} FROM {STAGING_TABLE}").fetchall()
    finally:
        src.close()

    if os.path.exists(SAMPLE_DB_PATH):
        os.remove(SAMPLE_DB_PATH)

    dst = sqlite3.connect(SAMPLE_DB_PATH)
    try:
        col_defs     = ", ".join(f'"{c}" TEXT' for c in SAMPLE_COLUMNS)
        placeholders = ", ".join("?" * len(SAMPLE_COLUMNS))
        with dst:
            dst.execute(f"CREATE TABLE {STAGING_TABLE} ({col_defs})")
            dst.executemany(
                f"INSERT INTO {STAGING_TABLE} ({col_list}) VALUES ({placeholders})",
                [tuple(r[c] for c in SAMPLE_COLUMNS) for r in rows],
            )
    finally:
        dst.close()

    log.info("Sample DB: %d righe scritte in %s", len(rows), SAMPLE_DB_PATH)
    return len(rows)


# ===========================================================================
# Accesso diretto al database principale di in-out (SQLite, senza ORM)
#
# Lo script NON importa nulla dal progetto in-out: scrive direttamente nelle
# tabelle subject, vehicle, card_registry e access di database.db.
# Gli enum sono salvati con il NOME (es. 'WAITING', 'RESERVATION'), come fa
# SQLAlchemy; le date nel formato 'YYYY-MM-DD HH:MM:SS.ffffff'.
# ===========================================================================

def _now() -> str:
    return _fmt_dt(datetime.now())


def _fmt_dt(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S.%f")


def _get_or_create_subject(db: sqlite3.Connection, social_reason: Optional[str]) -> Optional[int]:
    """Ritorna l'id del soggetto (lo crea se non esiste). None se ragione sociale vuota."""
    if not social_reason:
        return None
    sr = social_reason.strip()
    row = db.execute(
        "SELECT id FROM subject WHERE social_reason = ? COLLATE NOCASE LIMIT 1", (sr,)
    ).fetchone()
    if row:
        return row[0]
    cur = db.execute(
        "INSERT INTO subject (social_reason, date_created) VALUES (?, ?)", (sr, _now())
    )
    return cur.lastrowid


def _get_or_create_vehicle(db: sqlite3.Connection, plate: Optional[str],
                           description: Optional[str],
                           tare_kg: Optional[int],
                           max_threshold: Optional[int]) -> Optional[int]:
    """
    Ritorna l'id del veicolo (lo crea se non esiste).
    - Targa valorizzata: cerca per targa (UNIQUE), riusa se esiste.
    - Targa vuota + tara presente: cerca un veicolo senza targa con la stessa
      tara; se non c'è ne crea uno nuovo (plate=NULL, SQLite ammette NULL multipli).
    - Targa vuota + nessuna tara: None.
    """
    p = plate.strip().upper() if plate and plate.strip() else None

    if not p and not tare_kg:
        return None

    if p:
        row = db.execute(
            "SELECT id, tare, max_threshold FROM vehicle "
            "WHERE plate = ? COLLATE NOCASE LIMIT 1", (p,)
        ).fetchone()
    else:
        row = db.execute(
            "SELECT id, tare, max_threshold FROM vehicle "
            "WHERE plate IS NULL AND tare = ? LIMIT 1", (tare_kg,)
        ).fetchone()

    if row:
        vid, cur_tare, cur_max = row
        if tare_kg and not cur_tare:
            db.execute("UPDATE vehicle SET tare = ? WHERE id = ?", (tare_kg, vid))
        if max_threshold and not cur_max:
            db.execute("UPDATE vehicle SET max_threshold = ? WHERE id = ?", (max_threshold, vid))
        return vid

    cur = db.execute(
        "INSERT INTO vehicle (plate, description, tare, max_threshold, date_created) "
        "VALUES (?, ?, ?, ?, ?)",
        (p, description, tare_kg, max_threshold, _now()),
    )
    return cur.lastrowid


def _get_or_create_card_registry(db: sqlite3.Connection, code: Optional[str]) -> Optional[int]:
    """Ritorna l'id del badge (lo crea se non esiste). None se codice vuoto."""
    if not code:
        return None
    c = code.strip()
    row = db.execute(
        "SELECT id FROM card_registry WHERE code = ? OR number = ? LIMIT 1", (c, c)
    ).fetchone()
    if row:
        return row[0]
    cur = db.execute(
        "INSERT INTO card_registry (number, code, date_created) VALUES (?, ?, ?)",
        (c, c, _now()),
    )
    return cur.lastrowid


# ===========================================================================
# Trasformazione singola riga CARARRP → Access
# ===========================================================================

def _map_row(row: dict) -> dict:
    """
    Mappa i campi AS400 in un dizionario normalizzato pronto per l'upsert.

    Mapping (da column.txt):
        FEMRA0 + FEE8A0  → badge (chiave univoca "AA-PPPPPPP")
        FEA335           → targa motrice
        FEHCTY           → descrizione veicolo (targa rimorchio)
        FERSTS           → tara veicolo (A/B=15000kg, M=10000kg, C=None)
        FER3CC           → tara veicolo, prevale se > 0 e diversa da 10000/15000
        FERSCC           → soglia massima veicolo
        FER5TS           → flag stampa peso per autista
        FEHBTY           → ragione sociale soggetto
        FEJSUS           → tipo soggetto (C=Cliente, S/H=Fornitore)
        FEG1TY           → note
        FEFMCD           → riferimento documento (access.document_reference)
    """
    anno  = _s(row.get("FEMRA0"))
    prog  = _s(row.get("FEE8A0"))

    # Badge = chiave univoca AS400 (anno-progressivo)
    badge = _doc_ref(row.get("FEMRA0"), row.get("FEE8A0"))

    # Tipo soggetto
    type_subject = _type_subject(_s(row.get("FEJSUS")))

    # Ragione sociale soggetto
    subject_name = _s(row.get("FEHBTY"))

    # Veicolo
    plate         = _s(row.get("FEA335"))           # Targa motrice
    plate_trail   = _s(row.get("FEHCTY"))           # Targa rimorchio → description
    veh_type      = _s(row.get("FERSTS"))           # Tipo automezzo
    tare_kg       = _tare(veh_type, row.get("FER3CC"))  # Tara da FER3CC o tipo
    max_threshold = _i(row.get("FERSCC"))           # Limite peso → soglia veicolo
    print_weight  = _s(row.get("FER5TS"))           # Flag stampa peso

    # Note merce
    note = _s(row.get("FEG1TY"))

    # Riferimento documento (es. codice nazione ITA, BGR, ...)
    document_reference = _s(row.get("FEFMCD"))

    # Timestamp prenotazione (campi extra, presenti solo da AS400 reale)
    booked_at = _as400_datetime(row.get("FESIDT"), row.get("FEB9TM"))

    return {
        "badge":         badge,
        "type_subject":  type_subject,
        "subject_name":  subject_name,
        "plate":         plate,
        "plate_trail":   plate_trail,
        "veh_type":      veh_type,
        "tare_kg":       tare_kg,
        "max_threshold": max_threshold,
        "print_weight":  print_weight,
        "note":          note,
        "document_reference": document_reference,
        "booked_at":     booked_at,
    }


# ===========================================================================
# Upsert nel database principale
# ===========================================================================

def _upsert_access(db: sqlite3.Connection, mapped: dict) -> str:
    """
    Inserisce o aggiorna una prenotazione (tabella access).
    Chiave: badge "AA-PPPPPPP" (FEMRA0-FEE8A0) → card_registry → access.
    Se l'accesso esiste ed è ENTERED/CLOSED non viene toccato.
    Ritorna 'inserted', 'updated' o 'skipped'.
    """
    badge = mapped["badge"]
    if not badge:
        return "skipped"

    id_subject = _get_or_create_subject(db, mapped["subject_name"])
    id_vehicle = _get_or_create_vehicle(
        db,
        mapped["plate"],
        mapped["plate_trail"],
        mapped["tare_kg"],
        mapped["max_threshold"],
    )
    id_card = _get_or_create_card_registry(db, badge)

    row = db.execute(
        "SELECT id, status FROM access WHERE idCardRegistry = ? LIMIT 1", (id_card,)
    ).fetchone()

    if row is not None:
        access_id, status = row
        if status in ("ENTERED", "CLOSED"):
            return "skipped"
        db.execute(
            "UPDATE access SET typeSubject = ?, idSubject = ?, idVehicle = ?, "
            "idCardRegistry = ?, note = ?, document_reference = ? WHERE id = ?",
            (mapped["type_subject"], id_subject, id_vehicle, id_card,
             mapped["note"], mapped["document_reference"], access_id),
        )
        return "updated"

    booked_at = mapped["booked_at"] or datetime.now()
    db.execute(
        "INSERT INTO access (typeSubject, idSubject, idVehicle, idCardRegistry, "
        "number_in_out, note, selected, date_created, status, document_reference, "
        "type, hidden, mode) "
        "VALUES (?, ?, ?, ?, ?, ?, 0, ?, 'WAITING', ?, 'RESERVATION', 0, 'STANDARD')",
        (mapped["type_subject"], id_subject, id_vehicle, id_card,
         2 if mapped["tare_kg"] else 1, mapped["note"], _fmt_dt(booked_at),
         mapped["document_reference"]),
    )
    return "inserted"


# ===========================================================================
# Funzione principale di sincronizzazione
# ===========================================================================

def sync_to_main_db(rows: list[dict]) -> tuple[int, int, int]:
    """
    Scrive le righe CARARRP nel database principale in un'unica transazione
    (se qualcosa va storto non viene salvato niente).
    Ritorna (inseriti, aggiornati, saltati).
    """
    if not os.path.exists(MAIN_DB_PATH):
        raise FileNotFoundError(f"Database principale non trovato: {MAIN_DB_PATH}")

    inserted = updated = skipped = 0
    # timeout alto: in-out può tenere il database occupato per qualche istante
    db = sqlite3.connect(MAIN_DB_PATH, timeout=30)
    try:
        with db:  # commit se tutto ok, rollback in caso di eccezione
            for row in rows:
                result = _upsert_access(db, _map_row(row))
                if result == "inserted":
                    inserted += 1
                elif result == "updated":
                    updated += 1
                else:
                    skipped += 1
    finally:
        db.close()

    log.info("Database principale: %s", MAIN_DB_PATH)
    return inserted, updated, skipped


# ===========================================================================
# Entry point
# ===========================================================================

def _load_from_local() -> list[dict]:
    """Legge le righe da test_as400.db (staging completo)."""
    db = sqlite3.connect(TEST_DB_PATH)
    db.row_factory = sqlite3.Row
    try:
        rows = db.execute(f"SELECT * FROM {STAGING_TABLE}").fetchall()
        log.info("Lette %d righe da %s", len(rows), TEST_DB_PATH)
        return [dict(r) for r in rows]
    finally:
        db.close()


def main() -> int:
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    parser = argparse.ArgumentParser(description="Sincronizza prenotazioni AS400")
    parser.add_argument(
        "--source",
        choices=["as400", "local"],
        default="as400",
        help="as400 = connessione reale, local = legge da test_as400.db (default: as400)",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Sorgente: SQLite locale (test)
    # ------------------------------------------------------------------
    if args.source == "local":
        if not os.path.exists(TEST_DB_PATH):
            log.error("File locale non trovato: %s", TEST_DB_PATH)
            return 1
        rows = _load_from_local()
        if not rows:
            log.warning("Nessuna riga nel db locale, uscita.")
            return 1
        try:
            ins, upd, skip = sync_to_main_db(rows)
        except Exception:
            log.exception("Errore durante la sincronizzazione")
            return 1
        log.info(
            "Sincronizzazione completata: %d inseriti, %d aggiornati, %d saltati",
            ins, upd, skip,
        )
        return 0

    # ------------------------------------------------------------------
    # Sorgente: AS400 reale
    # ------------------------------------------------------------------
    if pyodbc is None:
        log.error("pyodbc non installato. Installalo nel venv con: pip install pyodbc")
        return 1

    as400_system = os.environ.get("AS400_SYSTEM")
    as400_uid    = os.environ.get("AS400_UID")
    as400_pwd    = os.environ.get("AS400_PWD")
    if not all([as400_system, as400_uid, as400_pwd]):
        log.error("Variabili d'ambiente AS400_SYSTEM, AS400_UID, AS400_PWD richieste")
        return 1

    conn_str = (
        f"DRIVER={{{AS400_DRIVER}}};SYSTEM={as400_system};"
        f"UID={as400_uid};PWD={as400_pwd};"
    )

    try:
        as400 = pyodbc.connect(conn_str, timeout=15)
    except pyodbc.Error:
        log.exception("Connessione AS400 fallita")
        return 1

    try:
        # 1. Lettura righe dall'AS400
        cur = as400.cursor()
        cur.execute(SQL_SELECT)
        cols = [d[0] for d in cur.description]
        raw_rows = cur.fetchall()
        rows = [dict(zip(cols, row)) for row in raw_rows]
        log.info("Lette %d prenotazioni da AS400", len(rows))

        # 2. Salva copia grezza nel db di staging
        try:
            load_staging(as400)
        except Exception:
            log.warning("Staging su SQLite fallito (non bloccante)", exc_info=True)

        # 3. Crea db di esempio con sole colonne di column.txt
        try:
            make_sample_db()
        except Exception:
            log.warning("Creazione sample DB fallita (non bloccante)", exc_info=True)

        # 4. Sincronizzazione nel database principale
        ins, upd, skip = sync_to_main_db(rows)
        log.info(
            "Sincronizzazione completata: %d inseriti, %d aggiornati, %d saltati",
            ins, upd, skip,
        )
        return 0

    except (pyodbc.Error, Exception):
        log.exception("Errore durante la sincronizzazione")
        return 1
    finally:
        as400.close()


if __name__ == "__main__":
    sys.exit(main())
