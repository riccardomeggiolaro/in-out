from sqlalchemy import exists, and_
from sqlalchemy.orm import selectinload
from modules.md_database.md_database import SessionLocal, Reservation, InOut

def has_vehicle_weighings(id):
    with SessionLocal() as session:
        reservation = session.query(
                Reservation
            ).options(
                selectinload(Reservation.in_out)
            ).filter(
                and_(
                    Reservation.idVehicle == id,
                    exists().where(
                        InOut.idReservation == Reservation.id
                    )
                )
            ).first()
        return reservation and len(reservation.in_out) > 0