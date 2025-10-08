from modules.md_database.md_database import LockRecord, SessionLocal

def unlock_record_by_attributes(table_name, idRecord, websocket_identifier, weigher_name):
    """
    Sblocca un record eliminando i lock che corrispondono agli attributi specificati.
    
    Args:
        table_name: Nome della tabella (opzionale)
        idRecord: ID del record (opzionale)
        websocket_identifier: Identificatore WebSocket (opzionale)
        weigher_name: Nome del weigher (opzionale)
    
    Returns:
        bool: True se almeno un lock è stato eliminato, False se nessun lock corrisponde
    
    Raises:
        Exception: Errore generico del database
    """
    with SessionLocal() as session:
        try:
            # Costruisci la query con i filtri opzionali
            query = session.query(LockRecord)
            
            if table_name:
                query = query.filter_by(table_name=table_name)
                
            if idRecord:
                query = query.filter_by(idRecord=idRecord)
                
            if websocket_identifier:
                query = query.filter_by(websocket_identifier=websocket_identifier)
                
            if weigher_name:
                query = query.filter_by(weigher_name=weigher_name)
            
            # Recupera tutti i record corrispondenti
            records = query.all()
            
            if not records:
                return False
                
            # Elimina tutti i record di lock trovati
            for record in records:
                session.delete(record)
            
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            raise Exception(f"Errore durante lo sblocco del record: {str(e)}")
        finally:
            session.close()