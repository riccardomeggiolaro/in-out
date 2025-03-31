from sqlalchemy.orm import selectinload
from modules.md_database.md_database import table_models, SessionLocal

def filter_data(table_name, filters=None, limit=None, offset=None, order_by=None):
    """Esegue una ricerca filtrata su una tabella specifica con supporto per la paginazione
    e popola automaticamente le colonne di riferimenti con i dati delle tabelle correlate,
    incluse tutte le relazioni annidate.
    
    Args:
        table_name (str): Il nome della tabella su cui eseguire la ricerca.
        filters (dict): Dizionario di filtri (nome_colonna: valore) per la ricerca. Default è None.
        limit (int): Numero massimo di righe da visualizzare. Default è None.
        offset (int): Numero di righe da saltare. Default è None.
        order_by (tuple): Tupla contenente (nome_colonna, direzione) per l'ordinamento.
            Direzione può essere 'asc' o 'desc'. Default è None.
            
    Returns:
        tuple: Una tupla contenente:
            - una lista di dizionari contenenti i risultati della ricerca,
            - il numero totale di righe nella tabella.
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
            query = query.options(selectinload(getattr(model, rel_name)).selectinload('*'))
        
        # Aggiungi i filtri, se specificati
        if filters:
            for key, value in filters.items():
                # Handle nested attributes (e.g. "subject.social_reason")
                if "." in key:
                    parts = key.split(".")
                    rel_name = parts[0]
                    attr_name = parts[1]
                    
                    # Verify that the relationship exists
                    if not hasattr(model, rel_name):
                        raise ValueError(f"Relazione '{rel_name}' non trovata nella tabella '{table_name}'.")
                    
                    # Get the related model
                    related_model = model.__mapper__.relationships[rel_name].mapper.class_
                    
                    # Verify that the attribute exists in the related model
                    if not hasattr(related_model, attr_name):
                        raise ValueError(f"Attributo '{attr_name}' non trovato nella relazione '{rel_name}'.")
                    
                    if isinstance(value, str):
                        # For strings, handle % properly for LIKE queries
                        if "%" in value:
                            # It's already a pattern for LIKE
                            query = query.join(getattr(model, rel_name)).filter(
                                getattr(related_model, attr_name).like(value)
                            )
                        else:
                            # Exact match
                            query = query.join(getattr(model, rel_name)).filter(
                                getattr(related_model, attr_name) == value
                            )
                    elif isinstance(value, int):
                        query = query.join(getattr(model, rel_name)).filter(
                            getattr(related_model, attr_name) == value
                        )
                    elif value is None:
                        query = query.join(getattr(model, rel_name)).filter(
                            getattr(related_model, attr_name).is_(None)
                        )
                else:
                    # Handle direct attributes
                    if hasattr(model, key):
                        if isinstance(value, str):
                            # For strings, handle % properly for LIKE queries
                            if "%" in value:
                                # It's already a pattern for LIKE
                                query = query.filter(getattr(model, key).like(value))
                            else:
                                # Exact match if no wildcard
                                query = query.filter(getattr(model, key) == value)
                        elif isinstance(value, int):
                            query = query.filter(getattr(model, key) == value)
                        elif value is None:
                            query = query.filter(getattr(model, key).is_(None))
                    else:
                        raise ValueError(f"Colonna '{key}' non trovata nella tabella '{table_name}'.")
        
        # Aggiungi l'ordinamento se specificato
        if order_by:
            column_name, direction = order_by
            if not hasattr(model, column_name):
                raise ValueError(f"Colonna '{column_name}' non trovata nella tabella '{table_name}'.")
            
            column = getattr(model, column_name)
            if direction.lower() == 'asc':
                query = query.order_by(column.asc())
            elif direction.lower() == 'desc':
                query = query.order_by(column.desc())
            else:
                raise ValueError("Direzione di ordinamento deve essere 'asc' o 'desc'.")
        
        # Esegui una query separata per ottenere il numero totale di righe
        total_rows = query.count()
        
        # Applica la paginazione se limit e offset sono specificati
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        
        # Esegui la query per ottenere i risultati filtrati
        results = query.all()
        session.close()
        return results, total_rows
    except Exception as e:
        session.close()
        raise e