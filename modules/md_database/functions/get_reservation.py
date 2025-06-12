from sqlalchemy.orm import selectinload
from modules.md_database.md_database import SessionLocal, Reservation, InOut
from typing import Union, Dict

def get_reservation_by_id(reservation_id: int) -> Dict[str, Union[bool, str, dict]]:
    """
    Gets a reservation by its ID with all related data.
    
    Args:
        reservation_id (int): The ID of the reservation to find
        
    Returns:
        dict: A dictionary containing:
            - success (bool): Whether the operation was successful
            - message (str): A message describing the result or error
            - data (dict, optional): The reservation data if found
    """
    session = SessionLocal()
    try:
        # Get the reservation with all relationships loaded
        reservation = (
            session.query(Reservation)
            .options(
                selectinload(Reservation.subject),
                selectinload(Reservation.vector),
                selectinload(Reservation.driver),
                selectinload(Reservation.vehicle),
                selectinload(Reservation.in_out).selectinload(InOut.weight1),
                selectinload(Reservation.in_out).selectinload(InOut.weight2)
            )
            .filter(Reservation.id == reservation_id)
            .first()
        )
        
        return reservation
        
    except Exception as e:
        raise e
    finally:
        session.close()