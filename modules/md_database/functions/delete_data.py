from modules.md_database.md_database import table_models, SessionLocal
from sqlalchemy.orm import joinedload

def delete_data(table_name, record_id):
    """Elimina un record specifico da una tabella."""
    # Verifica che il modello esista nel dizionario dei modelli
    model = table_models.get(table_name.lower())
    if not model:
        raise ValueError(f"Tabella '{table_name}' non trovata.")
    
    # Crea una sessione
    session = SessionLocal()
    try:
        # Option 1: Eager loading - load all relationships up front
        # This way relationships are already loaded before the session closes
        record = session.query(model).options(
            joinedload('*')  # Load all direct relationships
        ).filter_by(id=record_id).one_or_none()
        
        if record is None:
            raise ValueError(f"Record con ID {record_id} non trovato nella tabella '{table_name}'.")
        
        # Serializza tutto prima di eliminare il record
        result = {}
        
        # Serializzazione attributi base
        for column in model.__table__.columns:
            result[column.name] = getattr(record, column.name)
        
        # Serializzazione relazioni - già precaricate grazie a joinedload
        for rel_name, rel_obj in model.__mapper__.relationships.items():
            related_data = getattr(record, rel_name)
            
            if related_data is None:
                result[rel_name] = None
            elif hasattr(related_data, '__iter__') and not isinstance(related_data, str):
                # Gestione collection
                result[rel_name] = [serialize_object(item) for item in related_data]
            else:
                # Gestione oggetto singolo
                result[rel_name] = serialize_object(related_data)
        
        # Elimina il record dopo averlo serializzato
        session.delete(record)
        session.commit()
        
        return result
    except Exception as e:
        import libs.lb_log as lb_log
        lb_log.warning(e)
        session.rollback()
        raise e
    finally:
        # Chiudi la sessione dopo aver finito
        session.close()

def serialize_object(obj):
    """Serializza un oggetto SQLAlchemy."""
    if obj is None:
        return None
    
    # Gestione oggetti non-SQLAlchemy
    if not hasattr(obj, '__table__'):
        return obj
    
    # Serializzazione base
    serialized = {}
    for column in obj.__table__.columns:
        serialized[column.name] = getattr(obj, column.name)
    
    return serialized