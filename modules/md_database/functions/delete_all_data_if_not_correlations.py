from sqlalchemy import inspect
from modules.md_database.md_database import table_models, SessionLocal, engine

def delete_all_data_if_not_correlations(table_name):
    """
    Elimina tutti i record da una tabella che non hanno connessioni con accesses.
    
    Args:
        table_name (str): Il nome della tabella da cui eliminare i record.
    
    Returns:
        deleted_count (int):  Numero di record eliminati
        preserved_count (int):  Numero di record non eliminati
        total_records (int): Numero di record totali
    """
    # Verifica che il modello esista nel dizionario dei modelli
    model = table_models.get(table_name.lower())
    if not model:
        raise ValueError(f"Tabella '{table_name}' non trovata.")
    
    # Crea una sessione
    session = SessionLocal()
    
    try:
        # Ottieni l'inspector per analizzare le relazioni
        inspector = inspect(engine)
        
        # Trova i nomi delle foreign key che potrebbero collegarsi a accesses
        foreign_keys = inspector.get_foreign_keys(table_name)
        
        # Conta il numero totale di record
        total_records = session.query(model).count()
        
        # Costruisci la query per i record da eliminare
        delete_query = session.query(model)
        
        # Costruisci la query per i record da preservare
        preserve_query = session.query(model)
        
        # Se ci sono foreign key, aggiungi condizioni per escludere record correlati a accesses
        for fk in foreign_keys:
            local_col = fk['local_columns'][0]
            remote_col = fk['referred_columns'][0]
            remote_table = fk['referred_table']
            
            # Se la foreign key punta a accesses, filtra di conseguenza
            if remote_table == 'accesses':
                delete_query = delete_query.outerjoin(
                    table_models['accesses'], 
                    getattr(model, local_col) == getattr(table_models['accesses'], remote_col)
                ).filter(table_models['accesses'].id.is_(None))
                
                preserve_query = preserve_query.join(
                    table_models['accesses'], 
                    getattr(model, local_col) == getattr(table_models['accesses'], remote_col)
                )
        
        # Conta i record che verranno preservati
        preserved_count = preserve_query.count()
        
        # Elimina i record senza connessioni a accesses
        deleted_count = delete_query.delete(synchronize_session=False)
        
        # Conferma le modifiche nel database
        session.commit()
        
        return deleted_count, preserved_count, total_records    
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()