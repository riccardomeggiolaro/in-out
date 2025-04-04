from sqlalchemy.exc import IntegrityError
from modules.md_database.md_database import LockRecord, SessionLocal

def unlock_all_record():
    """
    Sblocca un record eliminando il lock specificato dall'ID
    
    Args:
        id: ID del record da sbloccare
    
    Returns:
        bool: True se lo sblocco è riuscito, False se il record non esiste
    
    Raises:
        Exception: Errore generico del database
    """
    with SessionLocal() as session:
        try:
            # Cerca il record di blocco specifico
            deleted_count = session.query(LockRecord).delete(synchronize_session=False)
            
            session.commit()
            return deleted_count
        except Exception as e:
            session.rollback()
            raise Exception(f"Errore durante lo sblocco del record: {str(e)}")
        finally:
            session.close()