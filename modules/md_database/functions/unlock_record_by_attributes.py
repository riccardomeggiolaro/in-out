from sqlalchemy.exc import IntegrityError
from modules.md_database.md_database import LockRecord, SessionLocal

def unlock_record_by_attributes(name_table, record_id, web_socket):
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
            record = session.query(LockRecord)
            
            if name_table:
                record = record.filter_by(nameTable=name_table)
                
            if record_id:
                record = record.filter_by(idRecord=record_id)
                
            if web_socket:
                record = record.filter_by(websocket=web_socket)
            
            record = record.one_or_none()
            
            if not record:
                return False
                
            # Elimina il record di blocco
            session.delete(record)
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            raise Exception(f"Errore durante lo sblocco del record: {str(e)}")
        finally:
            session.close()