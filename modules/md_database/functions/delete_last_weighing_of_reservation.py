from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from modules.md_database.md_database import SessionLocal, Weighing

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
            
            # Imposta idReservation a None invece di eliminare il record
            latest_weighing.idReservation = None
            session.commit()
            
            return deleted_weighing
        except Exception as e:
            session.rollback()
            raise e
        finally:
            # Chiudi la sessione dopo aver finito
            session.close()