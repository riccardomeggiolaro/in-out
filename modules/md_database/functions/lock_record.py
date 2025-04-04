from sqlalchemy.exc import IntegrityError
from modules.md_database.md_database import LockRecord, SessionLocal

def lock_record(name_table, id_record, web_socket=None):
    """
    Prova a bloccare un record se non è già bloccato.
    
    Restituisce:
    - (True, record) se il blocco ha successo
    - (False, existing_record) se il record è già bloccato
    """

    with SessionLocal() as session:
        try:
            # Prova a creare il blocco
            nuovo_record = LockRecord(
                nameTable=name_table,
                idRecord=id_record,
                websocket=web_socket
            )
            session.add(nuovo_record)
            session.commit()  # Commit delle modifiche
            session.refresh(nuovo_record)  # Rinfresca l'oggetto con i dati dal DB

            return True, nuovo_record
            
        except IntegrityError:
            # In caso di errore di integrità, rollback e recupera il record esistente
            session.rollback()
            existing_record = session.query(LockRecord).filter(
                LockRecord.nameTable == name_table,
                LockRecord.idRecord == id_record
            ).first()
            
            return False, existing_record
        except Exception as e:
            # Gestisce altre possibili eccezioni
            session.rollback()
            return False, None
        finally:
            session.close()