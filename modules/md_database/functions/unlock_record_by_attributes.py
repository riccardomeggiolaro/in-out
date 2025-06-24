from modules.md_database.md_database import LockRecord, SessionLocal

def unlock_record_by_attributes(table_name, idRecord, websocket_identifier, weigher_name):
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
            
            if table_name:
                record = record.filter_by(table_name=table_name)
                
            if idRecord:
                record = record.filter_by(idRecord=idRecord)
                
            if websocket_identifier:
                record = record.filter_by(websocket_identifier=websocket_identifier)
                
            if weigher_name:
                record = record.filter_by(weigher_name=weigher_name)
            
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