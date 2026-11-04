#!/usr/bin/env python3
"""
Osserva la cartella dei CSV delle pesate di in-out e, per ogni pesata
completa con riferimento documento diverso da "ITA", crea un TRANSITO
tramite le API di in-out (POST /api/anagrafic/access, mode=TRANSIT).

Comportamento:
- Reagisce subito alla scrittura di un CSV (inotify, tramite watchdog).
- Considera solo le pesate complete: seconda pesata o pesata con tara.
- Riferimento documento vuoto o "ITA" → nessun transito.
- Ogni CSV viene elaborato una sola volta (elenco in transit_watcher_state.json).
  Al primo avvio i CSV già presenti vengono segnati come elaborati, senza
  creare transiti per le pesate vecchie.
- Il badge non è nel CSV: viene letto (solo lettura) dal database di in-out,
  risalendo dalla pesata (pid) alla prenotazione appena pesata.
- Se la chiamata API fallisce scrive l'errore nel log e passa oltre.

Formato CSV (una riga, separatore ';', generato da utils_report.generate_csv_report):
     0 typeSubject ("Cliente"/"Fornitore")
     1-4  soggetto: id, ragione sociale, telefono, cf/piva
     5-8  vettore:  id, ragione sociale, telefono, cf/piva
     9-11 autista:  id, nome, telefono
    12-14 veicolo:  id, targa, descrizione
    15-16 materiale: id, descrizione
    17 note
    18 riferimento documento
    19-21 pesata 1: data, pid, peso
    22-24 pesata 2: data, pid, peso
    25 netto

Variabili d'ambiente (oppure file .env nella cartella dello script):
    IN_OUT_TOKEN=...                          (obbligatoria, token API di baronpesi)
    IN_OUT_URL=http://localhost:80            (opzionale)
    CSV_DIR=/var/opt/in-out/csv               (opzionale)
    TRANSIT_EXCLUDED_REFERENCE=ITA            (opzionale)
    MAIN_DB_PATH=/var/opt/in-out/database.db  (opzionale, per leggere il badge)

Uso:
    python3 transit_watcher.py
"""

import json
import logging
import os
import sqlite3
import sys
import threading
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
CSV_DIR = os.environ.get("CSV_DIR", "/var/opt/in-out/csv")
EXCLUDED_REFERENCE = os.environ.get("TRANSIT_EXCLUDED_REFERENCE", "ITA").strip().upper()
MAIN_DB_PATH = os.environ.get("MAIN_DB_PATH", "/var/opt/in-out/database.db")
STATE_PATH = os.environ.get(
    "TRANSIT_STATE_PATH", os.path.join(SCRIPT_DIR, "transit_watcher_state.json")
)

CSV_FIELDS = 26
TYPE_SUBJECT = {"Cliente": "CUSTOMER", "Fornitore": "SUPPLIER"}

log = logging.getLogger("transit_watcher")


# ===========================================================================
# Lettura CSV
# ===========================================================================

def _v(value: str) -> Optional[str]:
    """Valore pulito: '' e 'None' (scritto da str(None)) diventano None."""
    v = value.strip()
    return None if v in ("", "None") else v


def _id(value: str) -> Optional[int]:
    v = _v(value)
    try:
        return int(v) if v is not None else None
    except ValueError:
        return None


def parse_csv_line(line: str) -> Optional[list]:
    """
    Divide la riga in 26 campi. Le note (campo 17) possono contenere ';':
    i primi 17 e gli ultimi 8 campi hanno posizione fissa, il resto sono note.
    """
    parts = line.rstrip("\r\n").split(";")
    if len(parts) < CSV_FIELDS:
        return None
    head, tail = parts[:17], parts[-8:]
    note = ";".join(parts[17:len(parts) - 8])
    return head + [note] + tail


def is_complete(fields: list) -> bool:
    """Pesata completa: c'è la seconda pesata (anche con tara) o il netto."""
    return _v(fields[24]) is not None or _v(fields[25]) is not None


def find_badge(fields: list, file_name: str) -> Optional[int]:
    """
    id del badge (card_registry) della prenotazione appena pesata.
    Pesata → in_out (idWeight2) → badge dell'in_out o, se vuoto, dell'accesso.
    Se lo stesso pid esiste su più pese, preferisce quella che dà il nome al file
    ("<pesa>_<pid...>.csv"), poi la più recente. Database in sola lettura.
    """
    pid = _v(fields[23])
    if pid is None:
        return None
    try:
        db = sqlite3.connect(f"file:{MAIN_DB_PATH}?mode=ro", uri=True, timeout=10)
    except sqlite3.Error as e:
        log.warning("%s: database non leggibile (%s), transito senza badge", file_name, e)
        return None
    try:
        rows = db.execute(
            "SELECT w.weigher, COALESCE(io.idCardRegistry, a.idCardRegistry) "
            "FROM weighing w "
            "JOIN in_out io ON io.idWeight2 = w.id "
            "LEFT JOIN access a ON a.id = io.idAccess "
            "WHERE w.pid = ? ORDER BY w.id DESC",
            (pid,),
        ).fetchall()
    except sqlite3.Error as e:
        log.warning("%s: lettura badge fallita (%s), transito senza badge", file_name, e)
        return None
    finally:
        db.close()
    for weigher, card in rows:
        if weigher and file_name.startswith(f"{weigher}_"):
            return card
    return rows[0][1] if rows else None


def build_transit(fields: list, id_card: Optional[int] = None) -> dict:
    """Corpo della POST /api/anagrafic/access per il transito."""
    return {
        "typeSubject": TYPE_SUBJECT.get(_v(fields[0]) or "", "CUSTOMER"),
        "subject": {
            "id": _id(fields[1]),
            "social_reason": _v(fields[2]),
            "telephone": _v(fields[3]),
            "cfpiva": _v(fields[4]),
        },
        "vector": {
            "id": _id(fields[5]),
            "social_reason": _v(fields[6]),
            "telephone": _v(fields[7]),
            "cfpiva": _v(fields[8]),
        },
        "driver": {
            "id": _id(fields[9]),
            "social_reason": _v(fields[10]),
            "telephone": _v(fields[11]),
        },
        "vehicle": {
            "id": _id(fields[12]),
            "plate": _v(fields[13]),
            "description": _v(fields[14]),
        },
        "material": {
            "id": _id(fields[15]),
            "description": _v(fields[16]),
        },
        "note": _v(fields[17]),
        "document_reference": _v(fields[18]),
        "idCardRegistry": id_card,
        "type": "RESERVATION",
        "mode": "TRANSIT",
        "permanent": False,
        "hidden": False,
    }


# ===========================================================================
# Chiamata API
# ===========================================================================

def create_transit(body: dict) -> None:
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
            data = json.loads(resp.read() or b"{}")
            log.info("Transito creato: id=%s", data.get("id"))
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


# ===========================================================================
# Elaborazione di un file
# ===========================================================================

class State:
    """Elenco dei CSV già elaborati, salvato su disco."""

    def __init__(self, path: str):
        self.path = path
        self.lock = threading.Lock()
        self.done: set = set()
        self.first_run = not os.path.exists(path)
        if not self.first_run:
            try:
                with open(path, encoding="utf-8") as f:
                    self.done = set(json.load(f))
            except Exception:
                log.warning("Stato illeggibile (%s): riparto da vuoto", path)

    def is_done(self, name: str) -> bool:
        with self.lock:
            return name in self.done

    def mark(self, *names: str) -> None:
        with self.lock:
            self.done.update(names)
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(sorted(self.done), f)
            os.replace(tmp, self.path)


def process_file(path: str, state: State) -> None:
    name = os.path.basename(path)
    if not name.lower().endswith(".csv") or state.is_done(name):
        return
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            line = f.readline()
    except OSError as e:
        log.warning("%s: impossibile leggere il file (%s)", name, e)
        return

    fields = parse_csv_line(line)
    if fields is None:
        log.warning("%s: formato non riconosciuto, ignorato", name)
        state.mark(name)
        return

    if not is_complete(fields):
        # prima pesata: il CSV della pesata completa avrà un altro nome
        log.info("%s: pesata non completa, ignorato", name)
        state.mark(name)
        return

    reference = _v(fields[18])
    if reference is None or reference.upper() == EXCLUDED_REFERENCE:
        log.info("%s: riferimento documento %r, nessun transito", name, reference)
        state.mark(name)
        return

    id_card = find_badge(fields, name)
    body = build_transit(fields, id_card)
    plate = body["vehicle"]["plate"] or f"veicolo id {body['vehicle']['id']}"
    log.info("%s: riferimento %s, creo transito per %s (badge id %s)",
             name, reference, plate, id_card)
    try:
        create_transit(body)
    except RuntimeError as e:
        log.error("%s: transito NON creato: %s", name, e)
    # in ogni caso non riproviamo lo stesso file
    state.mark(name)


# ===========================================================================
# Watcher
# ===========================================================================

def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    if not IN_OUT_TOKEN:
        log.error("Variabile IN_OUT_TOKEN mancante (token API di in-out)")
        return 1

    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:
        log.error("watchdog non installato. Installalo nel venv con: pip install watchdog")
        return 1

    os.makedirs(CSV_DIR, exist_ok=True)
    state = State(STATE_PATH)

    existing = [n for n in os.listdir(CSV_DIR) if n.lower().endswith(".csv")]
    if state.first_run:
        state.mark(*existing)
        log.info("Primo avvio: %d CSV esistenti segnati come già elaborati", len(existing))
    else:
        # CSV arrivati mentre il servizio era fermo
        for n in sorted(existing, key=lambda n: os.path.getmtime(os.path.join(CSV_DIR, n))):
            process_file(os.path.join(CSV_DIR, n), state)

    class Handler(FileSystemEventHandler):
        # in-out scrive il CSV e chiude il file: agiamo alla chiusura
        def on_closed(self, event):
            if not event.is_directory:
                process_file(event.src_path, state)

        # file copiati/spostati nella cartella
        def on_moved(self, event):
            if not event.is_directory:
                process_file(event.dest_path, state)

    observer = Observer()
    observer.schedule(Handler(), CSV_DIR, recursive=False)
    observer.start()
    log.info("In ascolto su %s (API %s, escluso riferimento %r)",
             CSV_DIR, IN_OUT_URL, EXCLUDED_REFERENCE)
    try:
        while observer.is_alive():
            observer.join(1)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()
    return 0


if __name__ == "__main__":
    sys.exit(main())
