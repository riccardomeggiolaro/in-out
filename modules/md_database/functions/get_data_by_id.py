from sqlalchemy.orm import selectinload
from modules.md_database.md_database import table_models, SessionLocal

def get_data_by_id(table_name, record_id):
    """Ottiene un record specifico da una tabella tramite l'ID con tutte le relazioni annidate.

    Args:
        table_name (str): Il nome della tabella da cui ottenere il record.
        record_id (int): L'ID del record da ottenere.
        
    Returns:
        dict: Il record trovato con tutte le relazioni annidate, o None se non trovato.
    """
    # Verifica che il modello esista nel dizionario dei modelli
    model = table_models.get(table_name.lower())
    if not model:
        raise ValueError(f"Tabella '{table_name}' non trovata.")
        
    # Crea una sessione e costruisce la query
    session = SessionLocal()
    try:
        # Inizia la query sulla tabella specificata
        query = session.query(model)
        
        # Carica tutte le relazioni dirette della tabella principale
        for rel_name, rel_obj in model.__mapper__.relationships.items():
            # Carica la relazione diretta e tutte le relazioni annidate
            query = query.options(selectinload(getattr(model, rel_name)))
            
        # Cerca il record con l'ID specificato
        record = query.filter(model.id == record_id).one_or_none()
        
        if record is None:
            return None
            
        # Converte il record in un dizionario
        result = {}
        
        # Aggiungi gli attributi di base
        for column in model.__table__.columns:
            result[column.name] = getattr(record, column.name)
            
        # Aggiungi le relazioni
        for rel_name, rel_obj in model.__mapper__.relationships.items():
            related_data = getattr(record, rel_name)
            
            # Gestisci sia relazioni singole che collections
            if related_data is not None:
                if hasattr(related_data, '__iter__') and not isinstance(related_data, str):
                    # Collection di oggetti
                    result[rel_name] = []
                    for item in related_data:
                        item_dict = {}
                        for column in item.__table__.columns:
                            item_dict[column.name] = getattr(item, column.name)
                        result[rel_name].append(item_dict)
                else:
                    # Oggetto singolo
                    result[rel_name] = {}
                    for column in related_data.__table__.columns:
                        result[rel_name][column.name] = getattr(related_data, column.name)
            else:
                result[rel_name] = None
                
        return result
        
    except Exception as e:
        raise e
    finally:
        session.close()  # Assicura che la sessione venga sempre chiusa