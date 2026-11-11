"""
CSV Bridge
==========
Script autonomo (non importa nulla da in-out) che gira in loop e fa due cose:

1. PESCA DA "in" (remoto → locale)
   Preleva i CSV che il cliente deposita nella cartella remota  <remoto>/csv/in
   (la stessa destinazione configurata in config.json → sync_folder.remote_folder)
   e li porta in locale in  /var/opt/in-out/csv/in.
   Il file viene cancellato dal remoto SOLO dopo che la copia locale è completa.
   Protocolli supportati: samba (share già montata da in-out su mount_point),
   ftp e sftp (connessione propria con le stesse credenziali).

2. DA "csv" A "out" (locale → locale)
   Prende i CSV che in-out genera in  /var/opt/in-out/csv  (solo la cartella,
   non le sottocartelle), li converte nel formato
       codicetessera;numerotessera;materiale;data ora
   (data della 2a pesata se presente, altrimenti della 1a) e li scrive in
   /var/opt/in-out/csv/out. L'originale viene spostato in csv/elaborati
   (oppure cancellato con KEEP_ORIGINAL=0).
   La sincronizzazione di in-out deve avere "csv/out" nei sub_paths al posto
   di "csv": così viene inviato al remoto solo il file già trasformato.

3. IMPORTA "in" → PRENOTAZIONI
   Ogni CSV in /var/opt/in-out/csv/in (separatore ;, senza intestazione) ha
   righe del tipo:
       119686;ZN2G5541C03000166;HISAL415164
       campo 1 → codice tessera   (card_registry.code)
       campo 2 → numero tessera   (card_registry.number, e anche targa)
       campo 3 → materiale        (material.description)
   Prima operazione: crea le tessere che non esistono (commit separato).
   Seconda operazione: crea veicolo (targa = numero tessera) e materiale se
   mancano e inserisce la prenotazione (access RESERVATION, stato WAITING,
   modalità GENERIC: al momento della pesata fa una pesata generica e si
   chiude quando ha raggiunto il numero di operazioni, 1 di default).
   Se per quella tessera c'è già una prenotazione in attesa, la aggiorna
   invece di crearne un'altra. A fine elaborazione il file viene ELIMINATO;
   se il file contiene errori viene spostato in csv/in/errori.

Struttura risultante:
    /var/opt/in-out/csv/            ← CSV generati da in-out (intercettati qui)
    /var/opt/in-out/csv/out/        ← CSV trasformati (sincronizzati sul remoto)
    /var/opt/in-out/csv/in/         ← CSV pescati dal remoto (per le prenotazioni)
    /var/opt/in-out/csv/elaborati/  ← originali già passati in out
    /var/opt/in-out/csv/.tmp/       ← file temporanei (scrittura atomica)

Un file viene preso solo quando la sua dimensione è rimasta invariata per
almeno STABLE_SECONDS, per non leggere file ancora in scrittura/caricamento.

Variabili d'ambiente (tutte opzionali):
    CONFIG_FILE      percorso di config.json   (default: <progetto>/config.json)
    CSV_DIR          cartella CSV generati     (default: app_api.path_csv o /var/opt/in-out/csv)
    OUT_DIR          cartella di uscita        (default: <CSV_DIR>/out)
    IN_DIR           cartella locale di "in"   (default: <CSV_DIR>/in)
    ERROR_DIR        file "in" con errori      (default: <IN_DIR>/errori)
    DB_PATH          database di in-out        (default: app_api.path_database o /var/opt/in-out/database.db)
    IMPORT_ENABLED   1 = crea prenotazioni da "in", 0 = no     (default: 1)
    ARCHIVE_DIR      cartella originali        (default: <CSV_DIR>/elaborati)
    KEEP_ORIGINAL    1 = sposta in ARCHIVE_DIR, 0 = cancella   (default: 1)
    REMOTE_IN        percorso di "in" sul remoto, relativo a share/sub_path
                     (default: <CSV_DIR relativo a local_dir>/in → "csv/in")
    PULL_ENABLED     1 = pesca dal remoto, 0 = disattivato     (default: 1)
    POLL_SECONDS     intervallo tra due controlli              (default: 2)
    STABLE_SECONDS   secondi di dimensione invariata           (default: 3)
    LOG_LEVEL        livello di log                            (default: INFO)
"""

import os
import json
import time
import shutil
import logging
import posixpath
import sqlite3
from datetime import datetime
from ftplib import FTP, FTP_TLS, error_perm

# ---------------------------------------------------------------------------
# Configurazione
# ---------------------------------------------------------------------------
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.environ.get("CONFIG_FILE", os.path.join(PROJECT_DIR, "config.json"))

POLL_SECONDS = float(os.environ.get("POLL_SECONDS", "2"))
STABLE_SECONDS = float(os.environ.get("STABLE_SECONDS", "3"))
KEEP_ORIGINAL = os.environ.get("KEEP_ORIGINAL", "1") == "1"
PULL_ENABLED = os.environ.get("PULL_ENABLED", "1") == "1"
IMPORT_ENABLED = os.environ.get("IMPORT_ENABLED", "1") == "1"

logging.basicConfig(
    level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("csv_bridge")


def load_app_config() -> dict:
    """Legge la sezione app_api di config.json (riletta a ogni giro)."""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("app_api", {})
    except Exception as e:
        logger.error(f"Impossibile leggere {CONFIG_FILE}: {e}")
        return {}


def resolve_paths(app_cfg: dict) -> dict:
    sync_cfg = app_cfg.get("sync_folder", {}) or {}
    local_dir = sync_cfg.get("local_dir") or "/var/opt/in-out"

    csv_dir = os.environ.get("CSV_DIR") or app_cfg.get("path_csv") or "/var/opt/in-out/csv"
    if not os.path.isabs(csv_dir):
        csv_dir = os.path.join(PROJECT_DIR, csv_dir)

    rel_csv = os.path.relpath(csv_dir, local_dir).replace("\\", "/")
    if rel_csv.startswith(".."):
        rel_csv = "csv"

    in_dir = os.environ.get("IN_DIR") or os.path.join(csv_dir, "in")
    db_path = os.environ.get("DB_PATH") or app_cfg.get("path_database") or "/var/opt/in-out/database.db"
    if not os.path.isabs(db_path):
        db_path = os.path.join(PROJECT_DIR, db_path)

    return {
        "local_dir": local_dir,
        "db_path": db_path,
        "error_dir": os.environ.get("ERROR_DIR") or os.path.join(in_dir, "errori"),
        "mount_point": sync_cfg.get("mount_point") or "/mnt/sync-folder",
        "remote_folder": sync_cfg.get("remote_folder"),
        "csv_dir": csv_dir,
        "out_dir": os.environ.get("OUT_DIR") or os.path.join(csv_dir, "out"),
        "in_dir": in_dir,
        "archive_dir": os.environ.get("ARCHIVE_DIR") or os.path.join(csv_dir, "elaborati"),
        "tmp_dir": os.path.join(csv_dir, ".tmp"),
        "remote_in": (os.environ.get("REMOTE_IN") or posixpath.join(rel_csv, "in")).strip("/"),
    }


# ---------------------------------------------------------------------------
# Trasformazione CSV: personalizzare qui
# ---------------------------------------------------------------------------
# Il CSV generato da in-out (applications/utils/utils_report.py →
# generate_csv_report) è una riga di 29 campi separati da ';':
#   13 numero tessera   14 codice tessera   19 materiale
#   22 data 1a pesata   25 data 2a pesata   (formato DD/MM/YYYY HH:MM)
# I campi della tessera e del materiale si leggono dall'inizio, le date dalla
# fine: così un ';' dentro note o riferimento documento non sposta le date.
CSV_FIELDS = 29
IDX_CARD_NUMBER = 13
IDX_CARD_CODE = 14
IDX_MATERIAL = 19
IDX_DATE1_FROM_END = 7   # data1 = campo 22 su 29
IDX_DATE2_FROM_END = 4   # data2 = campo 25 su 29


def transform(content: str, file_name: str) -> str:
    """
    Converte ogni riga del CSV di in-out nel formato:
        codicetessera;numerotessera;materiale;data ora
    La data è quella della 2a pesata se presente, altrimenti della 1a.

    Se solleva un'eccezione il file NON viene passato in out e resta in csv/
    per essere ritentato al giro successivo.
    """
    out_lines = []
    for line in content.splitlines():
        if not line.strip():
            continue
        f = line.split(";")
        if len(f) < CSV_FIELDS:
            raise ValueError(f"{file_name}: attesi {CSV_FIELDS} campi, trovati {len(f)}")
        if len(f) > CSV_FIELDS:
            logger.warning(f"{file_name}: {len(f)} campi invece di {CSV_FIELDS} "
                           f"(';' dentro un testo?), date lette dalla fine della riga")
        code = f[IDX_CARD_CODE].strip()
        number = f[IDX_CARD_NUMBER].strip()
        material = f[IDX_MATERIAL].strip()
        date = f[-IDX_DATE2_FROM_END].strip() or f[-IDX_DATE1_FROM_END].strip()
        out_lines.append(";".join([code, number, material, date]))
    return "\n".join(out_lines)


# ---------------------------------------------------------------------------
# Utilità
# ---------------------------------------------------------------------------
class StabilityTracker:
    """Considera pronto un file solo se la dimensione non cambia per STABLE_SECONDS."""

    def __init__(self):
        self._seen = {}  # chiave → (dimensione, istante in cui è stata vista per la prima volta)

    def is_stable(self, key: str, size: int) -> bool:
        now = time.monotonic()
        prev = self._seen.get(key)
        if prev is None or prev[0] != size:
            self._seen[key] = (size, now)
            return False
        return now - prev[1] >= STABLE_SECONDS

    def forget(self, key: str):
        self._seen.pop(key, None)

    def keep_only(self, keys):
        for k in list(self._seen):
            if k not in keys:
                del self._seen[k]


def is_csv(name: str) -> bool:
    return not name.startswith(".") and name.lower().endswith(".csv")


def unique_path(directory: str, name: str) -> str:
    """Se il file esiste già aggiunge un timestamp al nome per non sovrascriverlo."""
    path = os.path.join(directory, name)
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(name)
    stamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    return os.path.join(directory, f"{base}_{stamp}{ext}")


def atomic_write_bytes(tmp_dir: str, dest_path: str, data: bytes):
    """
    Scrive in un file temporaneo e poi lo rinomina nella destinazione, così chi
    osserva la cartella di destinazione (es. la sincronizzazione) non vede mai
    un file a metà.
    """
    os.makedirs(tmp_dir, exist_ok=True)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    tmp_path = os.path.join(tmp_dir, f".{os.path.basename(dest_path)}.{os.getpid()}.tmp")
    with open(tmp_path, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, dest_path)


# ---------------------------------------------------------------------------
# 1) csv → out
# ---------------------------------------------------------------------------
local_tracker = StabilityTracker()


def process_local_csv(paths: dict):
    csv_dir = paths["csv_dir"]
    if not os.path.isdir(csv_dir):
        return

    present = set()
    for name in sorted(os.listdir(csv_dir)):
        src = os.path.join(csv_dir, name)
        if not is_csv(name) or not os.path.isfile(src):
            continue
        present.add(src)
        try:
            size = os.path.getsize(src)
        except OSError:
            continue
        if not local_tracker.is_stable(src, size):
            continue

        try:
            with open(src, "r", encoding="utf-8", newline="") as f:
                content = f.read()
            new_content = transform(content, name)
            dest = os.path.join(paths["out_dir"], name)
            atomic_write_bytes(paths["tmp_dir"], dest, new_content.encode("utf-8"))

            if KEEP_ORIGINAL:
                os.makedirs(paths["archive_dir"], exist_ok=True)
                shutil.move(src, unique_path(paths["archive_dir"], name))
            else:
                os.remove(src)
            local_tracker.forget(src)
            logger.info(f"csv → out: {name}")
        except Exception as e:
            logger.error(f"Errore elaborando {name}: {e}")

    local_tracker.keep_only(present)


# ---------------------------------------------------------------------------
# 2) remoto/in → locale/in
# ---------------------------------------------------------------------------
class RemoteSource:
    """Interfaccia comune: list() → {nome: dimensione}, download(nome) → bytes, delete(nome)."""

    def connect(self) -> bool: ...
    def close(self): ...
    def list(self) -> dict: ...
    def download(self, name: str) -> bytes: ...
    def delete(self, name: str): ...


class SambaSource(RemoteSource):
    """La share è montata da in-out su mount_point: si legge come una cartella locale."""

    def __init__(self, paths: dict):
        rf = paths["remote_folder"]
        self.mount_point = paths["mount_point"]
        self.dir = os.path.join(self.mount_point, rf.get("sub_path") or "", paths["remote_in"])

    def connect(self) -> bool:
        if not os.path.ismount(self.mount_point):
            logger.debug(f"Share non montata su {self.mount_point}")
            return False
        return os.path.isdir(self.dir)

    def close(self):
        pass

    def list(self) -> dict:
        out = {}
        for name in os.listdir(self.dir):
            p = os.path.join(self.dir, name)
            if is_csv(name) and os.path.isfile(p):
                out[name] = os.path.getsize(p)
        return out

    def download(self, name: str) -> bytes:
        with open(os.path.join(self.dir, name), "rb") as f:
            return f.read()

    def delete(self, name: str):
        os.remove(os.path.join(self.dir, name))


class FTPSource(RemoteSource):
    def __init__(self, paths: dict):
        self.cfg = paths["remote_folder"]
        base = posixpath.join(self.cfg.get("share_name") or "", self.cfg.get("sub_path") or "")
        self.dir = "/" + posixpath.join(base, paths["remote_in"]).strip("/")
        self.ftp = None

    def connect(self) -> bool:
        host, port = self.cfg["ip"], self.cfg.get("port") or 21
        try:
            try:
                ftp = FTP_TLS()
                ftp.connect(host, port, timeout=10)
                ftp.login(self.cfg["username"], self.cfg["password"])
                ftp.prot_p()
            except Exception:
                ftp = FTP()
                ftp.connect(host, port, timeout=10)
                ftp.login(self.cfg["username"], self.cfg["password"])
            ftp.voidcmd("TYPE I")
            ftp.cwd(self.dir)
            self.ftp = ftp
            return True
        except error_perm as e:
            logger.debug(f"FTP: cartella {self.dir} non disponibile: {e}")
        except Exception as e:
            logger.warning(f"FTP: connessione fallita: {e}")
        self.close()
        return False

    def close(self):
        if self.ftp:
            try:
                self.ftp.quit()
            except Exception:
                pass
            self.ftp = None

    def list(self) -> dict:
        out = {}
        for name in self.ftp.nlst():
            name = posixpath.basename(name)
            if not is_csv(name):
                continue
            try:
                out[name] = self.ftp.size(name)
            except Exception:
                pass  # probabilmente una cartella
        return out

    def download(self, name: str) -> bytes:
        chunks = []
        self.ftp.retrbinary(f"RETR {name}", chunks.append)
        return b"".join(chunks)

    def delete(self, name: str):
        self.ftp.delete(name)


class SFTPSource(RemoteSource):
    def __init__(self, paths: dict):
        self.cfg = paths["remote_folder"]
        base = posixpath.join(self.cfg.get("share_name") or "", self.cfg.get("sub_path") or "")
        self.dir = posixpath.join(base, paths["remote_in"])
        self.ssh = None
        self.sftp = None

    def connect(self) -> bool:
        try:
            import paramiko
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(
                self.cfg["ip"],
                port=self.cfg.get("port") or 22,
                username=self.cfg["username"],
                password=self.cfg["password"],
                timeout=10,
            )
            self.sftp = self.ssh.open_sftp()
            self.sftp.chdir(self.dir)
            return True
        except FileNotFoundError:
            logger.debug(f"SFTP: cartella {self.dir} non trovata")
        except Exception as e:
            logger.warning(f"SFTP: connessione fallita: {e}")
        self.close()
        return False

    def close(self):
        for obj in (self.sftp, self.ssh):
            try:
                if obj:
                    obj.close()
            except Exception:
                pass
        self.sftp = self.ssh = None

    def list(self) -> dict:
        import stat
        return {
            a.filename: a.st_size
            for a in self.sftp.listdir_attr(".")
            if is_csv(a.filename) and stat.S_ISREG(a.st_mode or 0)
        }

    def download(self, name: str) -> bytes:
        with self.sftp.open(name, "rb") as f:
            return f.read()

    def delete(self, name: str):
        self.sftp.remove(name)


def make_source(paths: dict):
    rf = paths["remote_folder"]
    if not rf:
        return None
    protocol = (rf.get("protocol") or "samba").lower()
    if protocol == "samba":
        return SambaSource(paths)
    if protocol == "ftp":
        return FTPSource(paths)
    if protocol == "sftp":
        return SFTPSource(paths)
    logger.error(f"Protocollo non supportato: {protocol}")
    return None


remote_tracker = StabilityTracker()


def pull_remote_in(paths: dict):
    source = make_source(paths)
    if source is None:
        return
    if not source.connect():
        return
    try:
        files = source.list()
        remote_tracker.keep_only(set(files))
        for name, size in sorted(files.items()):
            if not remote_tracker.is_stable(name, size):
                continue
            try:
                data = source.download(name)
                if len(data) != size:
                    logger.warning(f"{name}: scaricati {len(data)} byte invece di {size}, riprovo")
                    remote_tracker.forget(name)
                    continue
                dest = unique_path(paths["in_dir"], name)
                atomic_write_bytes(paths["tmp_dir"], dest, data)
                # Si cancella dal remoto solo dopo che il file locale è completo
                source.delete(name)
                remote_tracker.forget(name)
                logger.info(f"remoto/in → {dest}")
            except Exception as e:
                logger.error(f"Errore prelevando {name}: {e}")
    except Exception as e:
        logger.error(f"Errore leggendo la cartella remota: {e}")
    finally:
        source.close()


# ---------------------------------------------------------------------------
# 3) csv/in → prenotazioni nel database di in-out
# ---------------------------------------------------------------------------
# Le scritture seguono le convenzioni di as400/as400.py: enum salvati con il
# NOME (es. 'WAITING', 'RESERVATION'), date 'YYYY-MM-DD HH:MM:SS.ffffff'.

class RowError(Exception):
    """Riga non valida o in conflitto con i dati esistenti."""


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")


def read_in_rows(path: str) -> list:
    """Legge il CSV e ritorna [(n_riga, codice, numero, materiale)]."""
    with open(path, "rb") as f:
        raw = f.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")

    rows = []
    for n, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        fields = [x.strip().strip('"').strip() for x in line.split(";")]
        if len(fields) < 3:
            raise RowError(f"riga {n}: attesi 3 campi, trovati {len(fields)}: {line!r}")
        code, number, material = fields[0], fields[1], fields[2]
        if not code or not number:
            raise RowError(f"riga {n}: codice o numero tessera vuoto: {line!r}")
        rows.append((n, code, number, material))
    return rows


def ensure_card(db: sqlite3.Connection, code: str, number: str) -> tuple:
    """Ritorna (id tessera, creata?). Cerca per codice o numero; se non c'è la crea."""
    by_code = db.execute("SELECT id, number FROM card_registry WHERE code = ? LIMIT 1", (code,)).fetchone()
    by_number = db.execute("SELECT id, code FROM card_registry WHERE number = ? LIMIT 1", (number,)).fetchone()

    if by_code and by_number and by_code[0] != by_number[0]:
        raise RowError(f"codice {code} e numero {number} appartengono a due tessere diverse")
    if by_code:
        if by_code[1] and by_code[1].upper() != number.upper():
            raise RowError(f"il codice {code} è già associato al numero {by_code[1]}")
        if not by_code[1]:
            db.execute("UPDATE card_registry SET number = ? WHERE id = ?", (number, by_code[0]))
        return by_code[0], False
    if by_number:
        if by_number[1] and by_number[1].upper() != code.upper():
            raise RowError(f"il numero {number} è già associato al codice {by_number[1]}")
        if not by_number[1]:
            db.execute("UPDATE card_registry SET code = ? WHERE id = ?", (code, by_number[0]))
        return by_number[0], False

    cur = db.execute(
        "INSERT INTO card_registry (number, code, date_created) VALUES (?, ?, ?)",
        (number, code, _now()),
    )
    return cur.lastrowid, True


def get_or_create_vehicle(db: sqlite3.Connection, plate: str) -> int:
    p = plate.strip().upper()
    row = db.execute("SELECT id FROM vehicle WHERE plate = ? COLLATE NOCASE LIMIT 1", (p,)).fetchone()
    if row:
        return row[0]
    return db.execute(
        "INSERT INTO vehicle (plate, date_created) VALUES (?, ?)", (p, _now())
    ).lastrowid


def get_or_create_material(db: sqlite3.Connection, description: str):
    if not description:
        return None
    row = db.execute(
        "SELECT id FROM material WHERE description = ? COLLATE NOCASE LIMIT 1", (description,)
    ).fetchone()
    if row:
        return row[0]
    return db.execute(
        "INSERT INTO material (description, date_created) VALUES (?, ?)", (description, _now())
    ).lastrowid


def upsert_reservation(db: sqlite3.Connection, id_card: int, id_vehicle: int, id_material) -> str:
    """
    Se per la tessera esiste già una prenotazione in attesa (WAITING, non di
    transito) la aggiorna, altrimenti ne inserisce una nuova.
    """
    row = db.execute(
        "SELECT id FROM access WHERE idCardRegistry = ? AND status = 'WAITING' "
        "AND type = 'RESERVATION' AND (mode IS NULL OR mode != 'TRANSIT') "
        "ORDER BY id DESC LIMIT 1",
        (id_card,),
    ).fetchone()
    if row:
        db.execute(
            "UPDATE access SET idVehicle = ?, idMaterial = ?, mode = 'GENERIC' WHERE id = ?",
            (id_vehicle, id_material, row[0]),
        )
        return "aggiornata"
    db.execute(
        "INSERT INTO access (idVehicle, idMaterial, idCardRegistry, number_in_out, "
        "selected, date_created, status, type, hidden, mode) "
        "VALUES (?, ?, ?, 1, 0, ?, 'WAITING', 'RESERVATION', 0, 'GENERIC')",
        (id_vehicle, id_material, id_card, _now()),
    )
    return "inserita"


def import_file(path: str, db_path: str):
    rows = read_in_rows(path)
    if not rows:
        logger.info(f"{os.path.basename(path)}: file vuoto")
        return

    db = sqlite3.connect(db_path, timeout=30)
    try:
        # Operazione 1: tessere (commit a sé, prima delle prenotazioni)
        cards = {}
        with db:
            for n, code, number, _ in rows:
                try:
                    id_card, created = ensure_card(db, code, number)
                except RowError as e:
                    raise RowError(f"riga {n}: {e}")
                cards[n] = id_card
                if created:
                    logger.info(f"Tessera creata: codice {code}, numero {number}")

        # Operazione 2: veicoli, materiali e prenotazioni (tutto o niente)
        with db:
            for n, code, number, material in rows:
                id_vehicle = get_or_create_vehicle(db, number)
                id_material = get_or_create_material(db, material)
                esito = upsert_reservation(db, cards[n], id_vehicle, id_material)
                logger.info(f"Prenotazione {esito}: tessera {code}/{number}, materiale {material}")
    finally:
        db.close()


def import_in_dir(paths: dict):
    in_dir, db_path = paths["in_dir"], paths["db_path"]
    if not os.path.isdir(in_dir):
        return
    if not os.path.exists(db_path):
        logger.error(f"Database non trovato: {db_path}")
        return

    for name in sorted(os.listdir(in_dir)):
        path = os.path.join(in_dir, name)
        if not is_csv(name) or not os.path.isfile(path):
            continue
        try:
            import_file(path, db_path)
            os.remove(path)
            logger.info(f"{name}: importato ed eliminato")
        except (RowError, sqlite3.IntegrityError) as e:
            # Dati non validi: riprovare non serve, si sposta in errori
            os.makedirs(paths["error_dir"], exist_ok=True)
            shutil.move(path, unique_path(paths["error_dir"], name))
            logger.error(f"{name}: {e} → spostato in {paths['error_dir']}")
        except sqlite3.OperationalError as e:
            # Es. database bloccato: il file resta in "in" e si ritenta
            logger.warning(f"{name}: database non disponibile ({e}), riprovo")
        except Exception as e:
            logger.error(f"{name}: errore imprevisto ({e}), riprovo")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    paths = resolve_paths(load_app_config())
    for key in ("csv_dir", "out_dir", "in_dir", "archive_dir"):
        os.makedirs(paths[key], exist_ok=True)

    logger.info(f"CSV generati : {paths['csv_dir']}")
    logger.info(f"Uscita (out) : {paths['out_dir']}")
    logger.info(f"Ingresso (in): {paths['in_dir']}  ← remoto '{paths['remote_in']}'"
                + ("" if PULL_ENABLED else " (prelievo disattivato)"))

    sub_paths = ((load_app_config().get("sync_folder") or {}).get("sub_paths")) or []
    rel_csv = os.path.relpath(paths["csv_dir"], paths["local_dir"]).replace("\\", "/")
    if rel_csv in sub_paths:
        logger.warning(
            f"sync_folder.sub_paths contiene '{rel_csv}': la sincronizzazione invierà "
            f"(e cancellerà) i CSV prima che vengano trasformati. Sostituirlo con "
            f"'{posixpath.join(rel_csv, 'out')}'."
        )

    try:
        while True:
            paths = resolve_paths(load_app_config())
            process_local_csv(paths)
            if PULL_ENABLED:
                pull_remote_in(paths)
            if IMPORT_ENABLED:
                import_in_dir(paths)
            time.sleep(POLL_SECONDS)
    except KeyboardInterrupt:
        logger.info("Arresto.")


if __name__ == "__main__":
    main()
