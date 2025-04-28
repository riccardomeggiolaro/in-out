from modules.md_database.md_database import table_models, SessionLocal
from sqlalchemy.exc import IntegrityError
from sqlalchemy import insert
from fastapi import HTTPException

def add_data(table_name: str, data):
    """
    Aggiunge un record a una tabella specificata dinamicamente con gestione dei conflitti per SQLite.
    """
    table_name = table_name.lower()
    
    model = table_models.get(table_name)
    if not model:
        raise ValueError(f"Tabella '{table_name}' non trovata.")

    unique_columns = [column.name for column in model.__table__.columns if column.unique]
    
    with SessionLocal() as session:
        try:
            stmt = insert(model).values(data)
            session.execute(stmt)
            session.commit()
            
            return data
        
        except IntegrityError as e:
            conflict_columns = [col for col in unique_columns if col in data]
            conflict_data = {col: data[col] for col in conflict_columns}
            conflict_details = ', '.join([f"{k}: {v}" for k, v in conflict_data.items()])
            
            session.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Conflitto sui vincoli di unicità. I seguenti dati esistono già: {conflict_details}. Non puoi duplicarli."
            )
        except Exception as e:
            session.rollback()
            raise e