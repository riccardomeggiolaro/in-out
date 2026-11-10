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
   non le sottocartelle), li passa a transform() e scrive il risultato in
   /var/opt/in-out/csv/out. L'originale viene spostato in csv/elaborati
   (oppure cancellato con KEEP_ORIGINAL=0).
   La sincronizzazione di in-out deve avere "csv/out" nei sub_paths al posto
   di "csv": così viene inviato al remoto solo il file già trasformato.

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

    return {
        "local_dir": local_dir,
        "mount_point": sync_cfg.get("mount_point") or "/mnt/sync-folder",
        "remote_folder": sync_cfg.get("remote_folder"),
        "csv_dir": csv_dir,
        "out_dir": os.environ.get("OUT_DIR") or os.path.join(csv_dir, "out"),
        "in_dir": os.environ.get("IN_DIR") or os.path.join(csv_dir, "in"),
        "archive_dir": os.environ.get("ARCHIVE_DIR") or os.path.join(csv_dir, "elaborati"),
        "tmp_dir": os.path.join(csv_dir, ".tmp"),
        "remote_in": (os.environ.get("REMOTE_IN") or posixpath.join(rel_csv, "in")).strip("/"),
    }


# ---------------------------------------------------------------------------
# Trasformazione CSV: personalizzare qui
# ---------------------------------------------------------------------------
def transform(content: str, file_name: str) -> str:
    """
    Riceve il contenuto del CSV generato da in-out e restituisce quello da
    scrivere in out. Per ora lo lascia invariato: inserire qui la logica
    (es. cambio separatore, colonne, filtri).

    Se solleva un'eccezione il file NON viene passato in out e resta in csv/
    per essere ritentato al giro successivo.
    """
    return content


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
            time.sleep(POLL_SECONDS)
    except KeyboardInterrupt:
        logger.info("Arresto.")


if __name__ == "__main__":
    main()
