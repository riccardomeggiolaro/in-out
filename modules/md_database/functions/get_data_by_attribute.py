from sqlalchemy import func
from modules.md_database.md_database import table_models, SessionLocal

def get_data_by_attribute(table_name, attribute_name, attribute_value):
    """Ottiene un record specifico da una tabella tramite un attributo e imposta 'selected' a True.
    La ricerca non è case sensitive per valori di tipo stringa.

    Args:
        table_name (str): Il nome della tabella da cui ottenere il record.
        attribute_name (str): Il nome dell'attributo da usare per la ricerca.
        attribute_value (any): Il valore dell'attributo da cercare.
        if_not_selected (bool): Se True, solleva un errore se il record è già selezionato.
        set_selected (bool): Se True, imposta 'selected' a True prima di restituire il record.
        
    Returns:
        dict: Un dizionario con i dati del record aggiornato, o None se il record non è trovato.
    """

    # Verifica che il modello esista nel dizionario dei modelli
    model = table_models.get(table_name.lower())
    if not model:
        raise ValueError(f"Tabella '{table_name}' non trovata.")
        
    # Verifica che l'attributo esista nel modello
    if not hasattr(model, attribute_name):
        raise ValueError(f"Attributo '{attribute_name}' non trovato nella tabella '{table_name}'.")
        
    # Crea una sessione e cerca il record
    session = SessionLocal()
    try:
        # Recupera il record specifico in base all'attributo
        query = session.query(model)
        
        # Usa func.lower() per rendere la ricerca case insensitive se il valore è una stringa
        if isinstance(attribute_value, str):
            query = query.filter(func.lower(getattr(model, attribute_name)) == attribute_value.lower())
        else:
            query = query.filter(getattr(model, attribute_name) == attribute_value)
            
        record = query.one_or_none()
        record_dict = None
        
        if record:
            # Converte il record in un dizionario
            record_dict = {column.name: getattr(record, column.name) for column in model.__table__.columns}
            
        session.commit()
        session.close()
        return record_dict
        
    except Exception as e:
        session.rollback()  # Ripristina eventuali modifiche in caso di errore
        session.close()
        raise e