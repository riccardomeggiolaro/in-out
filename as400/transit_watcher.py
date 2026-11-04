#!/usr/bin/env python3
"""
Crea un TRANSITO in in-out per ogni pesata completata con riferimento
documento diverso da "ITA".

Non usa i CSV: legge (in sola lettura) il database di in-out ogni
POLL_INTERVAL secondi e cerca le pesate completate dopo l'ultima elaborata.
Così non c'è conflitto con il watcher di in-out che sposta i CSV sulla
cartella di rete, e funziona anche con la generazione dei CSV disattivata.

Per ogni pesata completata (riga in_out con seconda pesata) che:
    - ha riferimento documento valorizzato e diverso da "ITA",
    - non appartiene a un transito né a una pesata di test,
crea il transito con POST /api/anagrafic/access (type RESERVATION,
mode TRANSIT) con tipo soggetto, soggetto, vettore, autista, veicolo,
materiale, note, riferimento documento e badge della pesata.

- Riferimento: id della seconda pesata (weighing), che cresce nel tempo.
  Una riga in_out nasce alla prima pesata e si completa dopo: per questo
  non si usa l'id di in_out.
- Al primo avvio parte dall'ultima pesata esistente: nessun transito
  per le pesate vecchie.
- Se la chiamata API fallisce scrive l'errore nel log e passa oltre.

Variabili d'ambiente (oppure file .env nella cartella dello script):
    IN_OUT_TOKEN=...                          (obbligatoria, token API di baronpesi)
    IN_OUT_URL=http://localhost:80            (opzionale)
    MAIN_DB_PATH=/var/opt/in-out/database.db  (opzionale)
    TRANSIT_EXCLUDED_REFERENCE=ITA            (opzionale)
    TRANSIT_POLL_INTERVAL=1.5                 (opzionale, secondi)

Uso:
    python3 transit_watcher.py
"""

import json
import logging
import os
import signal
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from typing import Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_env_file(path: str) -> None:
    """Carica CHIAVE=valore da un file .env senza sovrascrivere l'ambiente."""
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


_load_env_file(os.environ.get("AS400_ENV_FILE", os.path.join(SCRIPT_DIR, ".env")))

IN_OUT_URL = os.environ.get("IN_OUT_URL", "http://localhost:80").rstrip("/")
IN_OUT_TOKEN = os.environ.get("IN_OUT_TOKEN", "")
MAIN_DB_PATH = os.environ.get("MAIN_DB_PATH", "/var/opt/in-out/database.db")
EXCLUDED_REFERENCE = os.environ.get("TRANSIT_EXCLUDED_REFERENCE", "ITA").strip().upper()
POLL_INTERVAL = float(os.environ.get("TRANSIT_POLL_INTERVAL", "1.5"))
STATE_PATH = os.environ.get(
    "TRANSIT_STATE_PATH", os.path.join(SCRIPT_DIR, "transit_watcher_state.json")
)

# Pesate già elaborate da ricordare: copre il caso (raro) di due pese che
# completano quasi insieme e scrivono nel database in ordine diverso.
LOOKBACK = 200

log = logging.getLogger("transit_watcher")

# Pesate completate dopo un certo id di seconda pesata.
# Esclusi i transiti (eviterebbe un transito per ogni transito pesato)
# e le pesate di test.
SQL_COMPLETED = """
    SELECT io.idWeight2, io.id, io.typeSubject, io.idSubject, io.idVector,
           io.idDriver, io.idMaterial, io.note, io.document_reference,
           COALESCE(io.idCardRegistry, a.idCardRegistry), a.idVehicle,
           v.plate
    FROM in_out io
    LEFT JOIN access a  ON a.id = io.idAccess
    LEFT JOIN vehicle v ON v.id = a.idVehicle
    WHERE io.idWeight2 IS NOT NULL
      AND io.idWeight2 > ?
      AND (a.mode IS NULL OR a.mode != 'TRANSIT')
      AND (a.type IS NULL OR a.type != 'TEST')
    ORDER BY io.idWeight2
"""


# ===========================================================================
# Stato
# ===========================================================================

def load_state() -> Optional[tuple]:
    """
    (floor, done): floor = pesata di partenza (mai si elabora una pesata con
    id <= floor), done = id delle seconde pesate già elaborate.
    None al primo avvio.
    """
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and isinstance(data.get("done"), list):
            return int(data.get("floor", 0)), [int(x) for x in data["done"]]
        # formato vecchio (elenco di CSV): si riparte dall'ultima pesata
    except FileNotFoundError:
        return None
    except Exception:
        log.warning("Stato illeggibile (%s): riparto dall'ultima pesata", STATE_PATH)
    return None


def save_state(floor: int, done: list) -> None:
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"floor": floor, "done": done[-LOOKBACK:]}, f)
    os.replace(tmp, STATE_PATH)


# ===========================================================================
# Database e API
# ===========================================================================

def open_db() -> sqlite3.Connection:
    return sqlite3.connect(f"file:{MAIN_DB_PATH}?mode=ro", uri=True, timeout=10)


def last_weighing_id(db: sqlite3.Connection) -> int:
    row = db.execute("SELECT MAX(idWeight2) FROM in_out").fetchone()
    return row[0] or 0


def build_transit(row: tuple) -> dict:
    (_, _, type_subject, id_subject, id_vector, id_driver, id_material,
     note, reference, id_card, id_vehicle, plate) = row
    return {
        "typeSubject": type_subject if type_subject in ("CUSTOMER", "SUPPLIER") else "CUSTOMER",
        "subject": {"id": id_subject},
        "vector": {"id": id_vector},
        "driver": {"id": id_driver},
        "vehicle": {"id": id_vehicle, "plate": None if id_vehicle else plate},
        "material": {"id": id_material},
        "note": note,
        "document_reference": reference,
        "idCardRegistry": id_card,
        "type": "RESERVATION",
        "mode": "TRANSIT",
        "permanent": False,
        "hidden": False,
    }


def create_transit(body: dict) -> Optional[int]:
    """Crea il transito. Solleva RuntimeError con il dettaglio se fallisce."""
    req = urllib.request.Request(
        f"{IN_OUT_URL}/api/anagrafic/access",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {IN_OUT_TOKEN}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read() or b"{}").get("id")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(detail).get("detail", detail)
        except Exception:
            pass
        if e.code == 401:
            detail = f"token non valido o scaduto ({detail})"
        raise RuntimeError(f"HTTP {e.code}: {detail}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"in-out non raggiungibile su {IN_OUT_URL}: {e.reason}") from None


def handle(row: tuple) -> None:
    id_w2, id_in_out = row[0], row[1]
    reference = (row[8] or "").strip()
    plate = row[11] or f"veicolo id {row[10]}"
    if not reference or reference.upper() == EXCLUDED_REFERENCE:
        log.info("Pesata %s (in_out %s, %s): riferimento %r, nessun transito",
                 id_w2, id_in_out, plate, reference or None)
        return
    log.info("Pesata %s (in_out %s): riferimento %s, creo transito per %s (badge id %s)",
             id_w2, id_in_out, reference, plate, row[9])
    try:
        new_id = create_transit(build_transit(row))
        log.info("Transito creato: id=%s", new_id)
    except RuntimeError as e:
        log.error("Pesata %s: transito NON creato: %s", id_w2, e)


# ===========================================================================
# Ciclo principale
# ===========================================================================

_running = True


def _stop(*_):
    global _running
    _running = False


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    if not IN_OUT_TOKEN:
        log.error("Variabile IN_OUT_TOKEN mancante (token API di in-out)")
        return 1

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    state = load_state()
    while state is None and _running:
        try:
            db = open_db()
            try:
                start = last_weighing_id(db)
            finally:
                db.close()
            state = (start, [])
            save_state(*state)
            log.info("Primo avvio: parto dopo la pesata %s (le precedenti sono ignorate)", start)
        except sqlite3.Error as e:
            log.warning("Database non leggibile (%s): riprovo", e)
            time.sleep(5)

    if state is None:
        return 0
    floor, done = state
    log.info("In ascolto su %s ogni %ss (API %s, escluso riferimento %r)",
             MAIN_DB_PATH, POLL_INTERVAL, IN_OUT_URL, EXCLUDED_REFERENCE)
    db_error = False
    while _running:
        try:
            done_set = set(done)
            since = max(floor, max(done) - LOOKBACK) if done else floor
            db = open_db()
            try:
                rows = db.execute(SQL_COMPLETED, (since,)).fetchall()
            finally:
                db.close()
            if db_error:
                log.info("Database di nuovo leggibile")
                db_error = False
            for row in rows:
                if row[0] in done_set:
                    continue
                handle(row)
                done.append(row[0])
                done_set.add(row[0])
                save_state(floor, done)
            done = done[-LOOKBACK:]
        except sqlite3.Error as e:
            if not db_error:
                log.warning("Lettura database fallita (%s): riprovo", e)
                db_error = True
        time.sleep(POLL_INTERVAL)
    return 0


if __name__ == "__main__":
    sys.exit(main())
