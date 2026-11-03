import os
import shutil
import libs.lb_log as lb_log


def backup_database(db_path: str, backup_dir: str, backup_filename: str = "database.db.bak") -> bool:
    """
    Esegue il backup del database copiandolo nella cartella di backup.
    Sovrascrive il backup precedente — un solo file mantenuto.

    Args:
        db_path:         Percorso assoluto del file database sorgente.
        backup_dir:      Cartella di destinazione del backup.
        backup_filename: Nome del file di backup (default: database.db.bak).

    Returns:
        True se il backup è riuscito, False altrimenti.
    """
    if not db_path or not backup_dir:
        lb_log.error("backup_database: db_path e backup_dir sono obbligatori")
        return False

    if not os.path.exists(db_path):
        lb_log.error(f"backup_database: file database non trovato: {db_path}")
        return False

    try:
        os.makedirs(backup_dir, exist_ok=True)
        dest = os.path.join(backup_dir, backup_filename)
        shutil.copy2(db_path, dest)
        lb_log.info(f"Backup giornaliero database completato: {dest}")
        return True
    except Exception as e:
        lb_log.error(f"Errore durante il backup del database: {e}")
        return False
