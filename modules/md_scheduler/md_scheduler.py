# ==============================================================
# ==== MODULO SCHEDULER PER CLEANUP ACCESSI MANUALI ===========
# ==============================================================

"""
Modulo per la gestione di task schedulati.
Implementa un job che ogni mezzanotte elimina gli accessi manuali
senza un peso 2 (seconda pesata).
"""

import threading
import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import libs.lb_log as lb_log
import libs.lb_config as lb_config
from modules.md_database.md_database import SessionLocal, Access, InOut, TypeAccess

# ==============================================================
# ==== VARIABILI GLOBALI =======================================
# ==============================================================

name_module = "scheduler"
scheduler = None
scheduler_thread = None

# ==============================================================
# ==== FUNZIONE DI CLEANUP =====================================
# ==============================================================

def cleanup_manual_accesses_without_weight2():
    """
    Elimina gli accessi manuali che non hanno un peso 2.
    Questa funzione viene eseguita ogni mezzanotte.
    """
    try:
        lb_log.info(f"[{name_module}] Inizio cleanup accessi manuali senza peso 2")

        # Crea una sessione del database
        db = SessionLocal()

        try:
            # Trova tutti gli accessi manuali
            manual_accesses = db.query(Access).filter(
                Access.type == TypeAccess.MANUALLY
            ).all()

            deleted_count = 0

            for access in manual_accesses:
                # Controlla se l'accesso ha almeno un InOut con peso 2
                has_weight2 = False

                for in_out in access.in_out:
                    if in_out.idWeight2 is not None:
                        has_weight2 = True
                        break

                # Se non ha nessun peso 2, elimina l'accesso
                if not has_weight2:
                    lb_log.info(f"[{name_module}] Eliminazione accesso ID {access.id} senza peso 2")
                    db.delete(access)
                    deleted_count += 1

            # Salva le modifiche
            db.commit()

            lb_log.info(f"[{name_module}] Cleanup completato: {deleted_count} accessi eliminati")

        except Exception as e:
            db.rollback()
            lb_log.error(f"[{name_module}] Errore durante il cleanup: {str(e)}")
            raise
        finally:
            db.close()

    except Exception as e:
        lb_log.error(f"[{name_module}] Errore fatale durante il cleanup: {str(e)}")

# ==============================================================
# ==== INIZIALIZZAZIONE SCHEDULER ==============================
# ==============================================================

def init():
    """
    Inizializzazione del modulo scheduler.
    """
    global scheduler

    lb_log.info(f"[{name_module}] Inizializzazione scheduler...")

    # Crea lo scheduler in background
    scheduler = BackgroundScheduler(timezone='Europe/Rome')

    # Aggiungi il job che viene eseguito ogni mezzanotte (00:00)
    scheduler.add_job(
        func=cleanup_manual_accesses_without_weight2,
        trigger=CronTrigger(hour=0, minute=0),
        id='cleanup_manual_accesses',
        name='Cleanup accessi manuali senza peso 2',
        replace_existing=True
    )

    lb_log.info(f"[{name_module}] Scheduler inizializzato con job mezzanotte")

# ==============================================================
# ==== AVVIO SCHEDULER =========================================
# ==============================================================

def start():
    """
    Avvia lo scheduler.
    """
    global scheduler

    if scheduler is not None and not scheduler.running:
        scheduler.start()
        lb_log.info(f"[{name_module}] Scheduler avviato")

        # Mantieni il thread attivo
        while lb_config.g_enabled:
            time.sleep(1)
    else:
        lb_log.warning(f"[{name_module}] Scheduler già in esecuzione o non inizializzato")

# ==============================================================
# ==== CHIUSURA SCHEDULER ======================================
# ==============================================================

def stop():
    """
    Ferma lo scheduler.
    """
    global scheduler

    if scheduler is not None and scheduler.running:
        scheduler.shutdown(wait=True)
        lb_log.info(f"[{name_module}] Scheduler fermato")
    else:
        lb_log.warning(f"[{name_module}] Scheduler non in esecuzione")

# ==============================================================
