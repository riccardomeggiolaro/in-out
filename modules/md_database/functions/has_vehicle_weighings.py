from sqlalchemy import exists, and_
from sqlalchemy.orm import selectinload
from modules.md_database.md_database import SessionLocal, Reservation, Weighing

def has_vehicle_weighings(id):
    with SessionLocal() as session:
        reservation = session.query(
                Reservation
            ).options(
                selectinload(Reservation.weighings)
            ).filter(
                and_(
                    Reservation.idVehicle == id,
                    exists().where(
                        Weighing.idReservation == Reservation.id
                    )
                )
            ).first()
        return reservation and len(reservation.weighings) > 0