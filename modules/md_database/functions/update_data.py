from modules.md_database.md_database import table_models, SessionLocal
from modules.md_database.functions.lock_record import lock_record
from modules.md_database.functions.unlock_record_by_id import unlock_record_by_id

def update_data(table_name, record_id, updated_data, web_socket=None):
    """
    Aggiorna un record specifico in una tabella.
    
    Args:
        table_name (str): Il nome della tabella in cui aggiornare i dati.
        record_id (int): L'ID del record da aggiornare.
        updated_data (dict): Un dizionario dei nuovi valori per i campi da aggiornare.
    
    Returns:
        dict: Dizionario contenente i dati del record aggiornato, incluse le relazioni.
    
    Raises:
        ValueError: Se la tabella o il record non sono trovati.
        SQLAlchemyError: Per errori durante l'aggiornamento del record.
    """
    # Normalizza il nome della tabella
    table_name = table_name.lower()
    
    # Verifica che il modello esista
    model = table_models.get(table_name)
    if not model:
        raise ValueError(f"Tabella '{table_name}' non trovata.")

    success, locked_record = False, None

    if web_socket:
        success, locked_record = lock_record(table_name, record_id, web_socket)
        if success is False:
            raise ValueError(f"Record con id '{record_id}' nella tabella '{table_name}' bloccato dall'utente '{locked_record.websocket}'")
    
    try:
        # Gestione della sessione con context manager
        with SessionLocal() as session:
            try:
                # Recupera il record specifico in base all'ID
                record = session.query(model).filter_by(id=record_id).one_or_none()
                
                if record is None:
                    raise ValueError(f"Record con ID {record_id} non trovato nella tabella '{table_name}'.")
                
                # Aggiorna i campi con i nuovi valori
                for key, value in updated_data.items():
                    if hasattr(record, key) and value is not None:
                        # Gestione speciale per campi ID
                        if value in ["", -1]:
                            value = None
                        
                        setattr(record, key, value)
                
                # Committa le modifiche
                session.commit()
                
                # Refresh per assicurare che tutti i valori siano aggiornati
                session.refresh(record)
                
                # Funzione di supporto per serializzare oggetti
                def serialize_object(obj):
                    if obj is None:
                        return None
                    
                    # Gestione oggetti singoli
                    if not hasattr(obj, '__table__'):
                        return obj
                    
                    # Serializzazione base
                    serialized = {}
                    for column in obj.__table__.columns:
                        serialized[column.name] = getattr(obj, column.name)
                    
                    return serialized
                
                # Preparazione del risultato
                result = {}
                
                # Serializzazione attributi base
                for column in model.__table__.columns:
                    result[column.name] = getattr(record, column.name)
                
                # Serializzazione relazioni
                for rel_name, rel_obj in model.__mapper__.relationships.items():
                    related_data = getattr(record, rel_name)
                    
                    if related_data is None:
                        result[rel_name] = None
                    elif hasattr(related_data, '__iter__') and not isinstance(related_data, str):
                        # Gestione collection
                        result[rel_name] = [
                            serialize_object(item) for item in related_data
                        ]
                    else:
                        # Gestione oggetto singolo
                        result[rel_name] = serialize_object(related_data)
                
                return result
            
            except Exception as e:
                # Rollback in caso di errore
                session.rollback()
                raise e
            finally:
                session.close()
    except Exception as e:
        raise e
    finally:
        if web_socket and success is True:
            unlock_record_by_id(locked_record.id)