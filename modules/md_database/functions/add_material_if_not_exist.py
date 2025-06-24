from sqlalchemy.orm import Session
from modules.md_database.md_database import SessionLocal, Material
from typing import Dict, Union

def add_material_if_not_exists(description: str) -> Dict[str, Union[bool, str, Material]]:
    """
    Checks if a material with the given description exists.
    If it doesn't exist, creates a new one.
    
    Args:
        description (str): The description of the material to find or create
        
    Returns:
        dict: A dictionary containing:
            - success (bool): Whether the operation was successful
            - message (str): A message describing the result or error
            - data (Material): The existing or newly created material
            - created (bool): Whether a new material was created
    """
    session = SessionLocal()
    try:
        # Check if material exists
        material = session.query(Material).filter(
            Material.description.ilike(description.strip())
        ).first()
        
        if material:
            return material.__dict__
            
        # Create new material if it doesn't exist
        new_material = Material(
            description=description.strip()
        )
        session.add(new_material)
        session.commit()
        session.refresh(new_material)

        return new_material.__dict__
        
    except Exception as e:
        session.rollback()
        return {
            "success": False,
            "message": f"Error processing material: {str(e)}",
            "data": None,
            "created": False
        }
    finally:
        session.close()