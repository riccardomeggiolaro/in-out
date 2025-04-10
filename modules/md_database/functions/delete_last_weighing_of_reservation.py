from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError
from modules.md_database.md_database import table_models, SessionLocal, Weighing
from modules.md_database.functions.lock_record import lock_record
from modules.md_database.functions.unlock_record_by_id import unlock_record_by_id

def delete_last_weighing_of_reservation(reservation_id, web_socket=None):
    """
    Elimina la pesata più recente per una specifica prenotazione.
    
    Args:
        session: La sessione SQLAlchemy da utilizzare
        idReservation: L'ID della prenotazione di cui eliminare l'ultima pesata
    
    Returns:
        tuple: (success, message)
            - success: Boolean che indica se l'operazione è avvenuta con successo
            - message: Messaggio di esito o di errore
            - deleted_weighing: L'oggetto pesata eliminato (o None in caso di errore)
    """
    try:
        # Crea una sessione
        with SessionLocal() as session:
            try:
                # Trova la pesata più recente per la prenotazione specificata
                latest_weighing = session.query(Weighing).filter(
                    Weighing.idReservation == reservation_id
                ).order_by(desc(Weighing.date)).first()
                
                # Se non esiste nessuna pesata per questa prenotazione
                if not latest_weighing:
                    raise ValueError(f"Weighing with idReservation {reservation_id} not found")
                
                # Salva i dati della pesata prima di eliminarla (per eventuale riferimento)
                deleted_weighing = {
                    'id': latest_weighing.id,
                    'weight': latest_weighing.weight,
                    'date': latest_weighing.date,
                    'pid': latest_weighing.pid,
                    'weigher': latest_weighing.weigher
                }
                
                # Elimina la pesata
                session.delete(latest_weighing)
                session.commit()
                
                return deleted_weighing
            except Exception as e:
                import libs.lb_log as lb_log
                lb_log.warning(e)
                session.rollback()
                raise e
            finally:
                # Chiudi la sessione dopo aver finito
                session.close()    
    except SQLAlchemyError as e:
        session.rollback()
        raise e
    except Exception as e:
        session.rollback()
        raise e