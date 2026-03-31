from sqlalchemy.orm import Session
from modules.md_database.md_database import SessionLocal, table_models
from typing import Dict, Union

def add_anagrafic_if_not_exists(table_name: str, name: str, value: str) -> Dict[str, Union[bool, str]]:
    """
    Checks if a record exists based on a dynamic column.
    If it doesn't exist, creates a new one.

    Args:
        table_name (str): Table name
        name (str): Column name to filter on
        value (str): Value to search/insert

    Returns:
        dict: The existing or newly created record
    """
    session = SessionLocal()
    try:
        model_anagrafic = table_models.get(table_name)

        if not model_anagrafic:
            return {
                "success": False,
                "message": f"Model '{table_name}' not found",
                "data": None,
                "created": False
            }

        # Colonna dinamica
        column = getattr(model_anagrafic, name)

        # Check if exists
        anagrafic = session.query(model_anagrafic).filter(
            column.ilike(value.strip())
        ).first()

        if anagrafic:
            return anagrafic.__dict__

        # Create new record
        new_anagrafic = model_anagrafic(**{
            name: value.strip()
        })

        session.add(new_anagrafic)
        session.commit()
        session.refresh(new_anagrafic)

        return new_anagrafic.__dict__

    except Exception as e:
        session.rollback()
        return {
            "success": False,
            "message": f"Error processing record: {str(e)}",
            "data": None,
            "created": False
        }
    finally:
        session.close()