from sqlalchemy.orm import selectinload, joinedload
from modules.md_database.md_database import table_models, SessionLocal

def add_data(table_name: str, data):
    """
    Aggiunge un record a una tabella specificata dinamicamente.
    
    Args:
        table_name (str): Il nome della tabella in cui aggiungere i dati.
        data (dict): Un dizionario dei dati da inserire nella tabella.
    
    Returns:
        dict: Dizionario contenente i dati del record inserito, incluse le relazioni.
    
    Raises:
        ValueError: Se la tabella non è trovata.
        SQLAlchemyError: Per errori durante l'inserimento del record.
    """
    # Normalizza il nome della tabella
    table_name = table_name.lower()
    
    # Verifica che il modello esista
    model = table_models.get(table_name)
    if not model:
        raise ValueError(f"Tabella '{table_name}' non trovata.")
    
    # Gestione della sessione con context manager
    with SessionLocal() as session:
        try:
            # Crea una nuova istanza del modello con i dati forniti
            record = model(**data)
            
            # Aggiunge e committa il record
            session.add(record)
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