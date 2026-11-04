#!/usr/bin/env python3

"""
Sincronizza le prenotazioni aperte da AS400 (LIBDAT.CARARRP) nel database
principale dell'applicazione in-out (/var/opt/in-out/database.db).

Comportamento:
- Legge solo le prenotazioni filtrate (FEGUTS='', FEADCE='01', FEGVTS='',
  FEONDT=0, FEBZTM=0, FEJSUS IN ('C','S','H')).
- Per ogni riga crea/aggiorna le anagrafiche (Subject, Vector, Driver,
  Vehicle, Material, CardRegistry) con logica lookup-or-create.
- Upsert sull'Access: chiave = document_reference (formato "AA-PPPPPPP").
  Se l'accesso esiste già e ha status WAITING/OPEN aggiorna i campi;
  se è ENTERED/CLOSED lo salta (non sovrascrive pesate già fatte).
- Solo lettura sull'AS400: nessun UPDATE/DELETE sul sistema remoto.
- Rilanciabile quante volte si vuole (idempotente).

Dipendenze (Debian 13):
    sudo apt install python3-pyodbc unixodbc
    + driver "IBM i Access ODBC Driver" configurato in odbcinst.ini
    + pacchetti del progetto nel PYTHONPATH (per importare md_database)

Variabili d'ambiente:
    AS400_SYSTEM=10.0.0.1
    AS400_UID=...
    AS400_PWD=...
    AS400_DRIVER="IBM i Access ODBC Driver"   (opzionale)
    TEST_DB_PATH=./test_as400.db              (opzionale, solo per lo staging)

Uso:
    # dalla root del progetto in-out:
    python3 as400/as400.py
"""

import logging
import os
import sqlite3
import sys
from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional

# Aggiunge la root del progetto al path così i moduli si trovano
# sia lanciando da as400/ che dalla root
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Inizializza la config dell'app (richiesta da md_database)
import libs.lb_config as lb_config
lb_config.init()

try:
    import pyodbc
except ImportError:
    pyodbc = None  # type: ignore  # non serve per il caricamento da staging

# ---------------------------------------------------------------------------
# Configurazione connessione AS400 (lette solo quando serve main())
# ---------------------------------------------------------------------------
AS400_DRIVER = os.environ.get("AS400_DRIVER", "IBM i Access ODBC Driver")

# Path del db di staging (usato solo dalla funzione _load_staging)
TEST_DB_PATH   = os.environ.get("TEST_DB_PATH",   "test_as400.db")
SAMPLE_DB_PATH = os.environ.get("SAMPLE_DB_PATH", "sample_as400.db")

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
# Lookup-or-create helpers (lavorano sulla sessione SQLAlchemy del db principale)
# ===========================================================================

def _get_or_create_subject(session, social_reason: Optional[str]) -> Optional[int]:
    """Ritorna l'id di Subject (crea se non esiste). None se social_reason vuota."""
    from modules.md_database.md_database import Subject
    if not social_reason:
        return None
    sr = social_reason.strip()
    obj = session.query(Subject).filter(Subject.social_reason.ilike(sr)).first()
    if obj:
        return obj.id
    obj = Subject(social_reason=sr)
    session.add(obj)
    session.flush()
    return obj.id


def _get_or_create_vector(session, social_reason: Optional[str]) -> Optional[int]:
    """Ritorna l'id di Vector (crea se non esiste). None se vuoto."""
    from modules.md_database.md_database import Vector
    if not social_reason:
        return None
    sr = social_reason.strip()
    obj = session.query(Vector).filter(Vector.social_reason.ilike(sr)).first()
    if obj:
        return obj.id
    obj = Vector(social_reason=sr)
    session.add(obj)
    session.flush()
    return obj.id


def _get_or_create_driver(session, social_reason: Optional[str],
                           telephone: Optional[str]) -> Optional[int]:
    """Ritorna l'id di Driver (crea se non esiste). Cerca prima per telefono."""
    from modules.md_database.md_database import Driver
    if not social_reason and not telephone:
        return None
    obj = None
    if telephone:
        obj = session.query(Driver).filter(Driver.telephone == telephone.strip()).first()
    if obj is None and social_reason:
        obj = session.query(Driver).filter(
            Driver.social_reason.ilike(social_reason.strip())
        ).first()
    if obj:
        return obj.id
    obj = Driver(
        social_reason=social_reason.strip() if social_reason else None,
        telephone=telephone.strip() if telephone else None,
    )
    session.add(obj)
    session.flush()
    return obj.id


def _get_or_create_vehicle(session, plate: Optional[str],
                            description: Optional[str],
                            tare_kg: Optional[int],
                            max_threshold: Optional[int],
                            print_weight: Optional[str]) -> Optional[int]:
    """
    Ritorna l'id di Vehicle (crea se non esiste).
    - Targa valorizzata: lookup per targa (UNIQUE), riusa se esiste.
    - Targa vuota + tara presente: lookup per tara, crea nuovo se tara diversa.
      Usa plate=NULL per non violare il UNIQUE constraint (SQLite ammette NULL multipli).
    - Targa vuota + nessuna tara: restituisce None.
    """
    from modules.md_database.md_database import Vehicle

    p = plate.strip().upper() if plate and plate.strip() else None

    # Nessuna targa e nessuna tara → non creare il veicolo
    if not p and not tare_kg:
        return None

    if p:
        obj = session.query(Vehicle).filter(Vehicle.plate.ilike(p)).first()
    else:
        # Targa vuota: cerca per tara — se tara diversa crea nuovo veicolo
        obj = session.query(Vehicle).filter(
            Vehicle.plate.is_(None),
            Vehicle.tare == tare_kg,
        ).first()

    if obj:
        if tare_kg and not obj.tare:
            obj.tare = tare_kg
        if max_threshold and not obj.max_threshold:
            obj.max_threshold = max_threshold
        return obj.id

    obj = Vehicle(
        plate=p,  # None se targa vuota
        description=description,
        tare=tare_kg,
        max_threshold=max_threshold,
    )
    session.add(obj)
    session.flush()
    return obj.id


def _get_or_create_material(session, description: Optional[str]) -> Optional[int]:
    """Ritorna l'id di Material (crea se non esiste). None se descrizione vuota."""
    from modules.md_database.md_database import Material
    if not description:
        return None
    d = description.strip()
    obj = session.query(Material).filter(Material.description.ilike(d)).first()
    if obj:
        return obj.id
    obj = Material(description=d)
    session.add(obj)
    session.flush()
    return obj.id


def _get_or_create_card_registry(session, code: Optional[str]) -> Optional[int]:
    """Ritorna l'id di CardRegistry (crea se non esiste). None se code vuoto."""
    from modules.md_database.md_database import CardRegistry
    if not code:
        return None
    c = code.strip()
    obj = session.query(CardRegistry).filter(
        (CardRegistry.code == c) | (CardRegistry.number == c)
    ).first()
    if obj:
        return obj.id
    obj = CardRegistry(number=c, code=c)
    session.add(obj)
    session.flush()
    return obj.id


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
        "booked_at":     booked_at,
    }


# ===========================================================================
# Upsert nel database principale
# ===========================================================================

def _upsert_access(session, mapped: dict) -> str:
    """
    Inserisce o aggiorna un Access nel database principale.
    Chiave di upsert: document_reference (FEMRA0-FEE8A0).
    Ritorna 'inserted', 'updated' o 'skipped'.
    """
    from modules.md_database.md_database import (
        Access, AccessStatus, TypeAccess, TypeSubjectEnum, AccessMode,
    )

def _upsert_access(session, mapped: dict) -> str:
    """
    Inserisce o aggiorna un Access nel database principale.
    Chiave di upsert: badge (FEMRA0-FEE8A0) → card_registry + document_reference.
    Ritorna 'inserted', 'updated' o 'skipped'.
    """
    from modules.md_database.md_database import (
        Access, AccessStatus, TypeAccess, TypeSubjectEnum, AccessMode,
    )

    badge = mapped["badge"]
    if not badge:
        return "skipped"

    # --- Lookup / crea anagrafiche ---
    id_subject = _get_or_create_subject(session, mapped["subject_name"])
    id_vehicle = _get_or_create_vehicle(
        session,
        mapped["plate"],
        mapped["plate_trail"],
        mapped["tare_kg"],
        mapped["max_threshold"],
        mapped["print_weight"],
    )
    id_card = _get_or_create_card_registry(session, badge)

    # --- Cerca accesso esistente per badge ---
    access = session.query(Access).filter(
        Access.idCardRegistry == id_card
    ).first()

    if access is not None:
        if access.status in (AccessStatus.ENTERED, AccessStatus.CLOSED):
            return "skipped"

        access.typeSubject        = TypeSubjectEnum[mapped["type_subject"]]
        access.idSubject          = id_subject
        access.idVehicle          = id_vehicle
        access.idCardRegistry     = id_card
        access.note               = mapped["note"]
        return "updated"

    # --- Crea nuovo accesso ---
    access = Access(
        typeSubject        = TypeSubjectEnum[mapped["type_subject"]],
        idSubject          = id_subject,
        idVehicle          = id_vehicle,
        idCardRegistry     = id_card,
        number_in_out      = 2 if mapped["tare_kg"] else 1,
        note               = mapped["note"],
        document_reference = None,
        type               = TypeAccess.RESERVATION,
        status             = AccessStatus.WAITING,
        mode               = AccessMode.STANDARD,
        hidden             = False,
        date_created       = mapped["booked_at"] or datetime.now(),
    )
    session.add(access)
    return "inserted"


# ===========================================================================
# Funzione principale di sincronizzazione
# ===========================================================================

def sync_to_main_db(rows: list[dict]) -> tuple[int, int, int]:
    """
    Itera le righe CARARRP normalizzate e le upserta nel db principale.
    Ritorna (inseriti, aggiornati, saltati).
    """
    from modules.md_database.md_database import SessionLocal

    inserted = updated = skipped = 0

    with SessionLocal() as session:
        try:
            for row in rows:
                mapped = _map_row(row)
                result = _upsert_access(session, mapped)
                if result == "inserted":
                    inserted += 1
                elif result == "updated":
                    updated += 1
                else:
                    skipped += 1

            session.commit()
        except Exception:
            session.rollback()
            raise

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
        ins, upd, skip = sync_to_main_db(rows)
        log.info(
            "Sincronizzazione completata: %d inseriti, %d aggiornati, %d saltati",
            ins, upd, skip,
        )
        return 0

    # ------------------------------------------------------------------
    # Sorgente: AS400 reale
    # ------------------------------------------------------------------
    if pyodbc is None:
        log.error("pyodbc non installato. Installa con: sudo apt install python3-pyodbc")
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
