from modules.md_database.md_database import table_models, SessionLocal
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

def add_data(table_name: str, data):
    """
    Aggiunge un record a una tabella specificata dinamicamente con gestione dei conflitti per SQLite.
    """
    table_name = table_name.lower()
    model = table_models.get(table_name)
    if not model:
        raise ValueError(f"Tabella '{table_name}' non trovata.")
    
    with SessionLocal() as session:
        try:
            record = model(**data)
            session.add(record)
            session.commit()
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
            
            return record.__dict__
        except IntegrityError as e:
            session.rollback()
            error_message = str(e)
            
            # Lista per tenere traccia di tutti i conflitti trovati
            conflicts = []
            
            # Cerchiamo tutti i vincoli di unicità violati
            if "UNIQUE constraint failed:" in error_message:
                # Estrazione della parte dopo "UNIQUE constraint failed:"
                table_part = error_message.split("UNIQUE constraint failed:")[1].strip()
                # Può contenere vincoli multipli separati da virgole
                constraint_parts = table_part.split(',')
                
                for part in constraint_parts:
                    part = part.strip()
                    # Verifichiamo se contiene un punto che separa nome tabella e colonna
                    if '.' in part:
                        table_column = part.split('.')
                        # Assicuriamoci che ci siano abbastanza elementi dopo lo split
                        if len(table_column) >= 2:
                            column_name = table_column[1].strip()
                            if column_name in data:
                                conflicts.append(f"{column_name}: {data[column_name]}")
            
            # Se non siamo riusciti a estrarre i conflitti con il metodo precedente
            # proviamo con un approccio alternativo
            if not conflicts:
                unique_columns = [column.name for column in model.__table__.columns if column.unique]
                for column in unique_columns:
                    if column in data:
                        # Verifichiamo se questo valore esiste già nel database
                        existing = session.query(model).filter(getattr(model, column) == data[column]).first()
                        if existing:
                            conflicts.append(f"{column}: {data[column]}")
            
            if conflicts:
                conflict_details = ', '.join(conflicts)
                raise HTTPException(
                    status_code=400,
                    detail=f"Conflitto sui vincoli di unicità. I seguenti valori sono duplicati: {conflict_details}"
                )
            else:
                # Fallback se non riusciamo a determinare i conflitti specifici
                raise HTTPException(
                    status_code=400,
                    detail=f"Conflitto su uno o più vincoli di unicità. Non puoi duplicare questo record."
                )
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()