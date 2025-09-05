from sqlalchemy.orm import selectinload
from modules.md_database.md_database import SessionLocal, Access, InOut
from typing import Union, Dict

def get_access_by_id(access_id: int) -> Dict[str, Union[bool, str, dict]]:
    """
    Gets a access by its ID with all related data.
    
    Args:
        access_id (int): The ID of the access to find
        
    Returns:
        dict: A dictionary containing:
            - success (bool): Whether the operation was successful
            - message (str): A message describing the result or error
            - data (dict, optional): The access data if found
    """
    session = SessionLocal()
    try:
        # Get the access with all relationships loaded
        access = (
            session.query(Access)
            .options(
                selectinload(Access.subject),
                selectinload(Access.vector),
                selectinload(Access.driver),
                selectinload(Access.vehicle),
                selectinload(Access.in_out).selectinload(InOut.weight1),
                selectinload(Access.in_out).selectinload(InOut.weight2),
                selectinload(Access.in_out).selectinload(InOut.material)
            )
            .filter(Access.id == access_id)
            .first()
        )

        if access:
            access.__dict__['is_latest_for_vehicle'] = access.is_latest_for_vehicle
        
        return access
        
    except Exception as e:
        raise e
    finally:
        session.close()