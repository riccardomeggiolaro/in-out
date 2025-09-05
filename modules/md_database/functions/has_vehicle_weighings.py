from sqlalchemy import exists, and_
from sqlalchemy.orm import selectinload
from modules.md_database.md_database import SessionLocal, Access, InOut

def has_vehicle_weighings(id):
    with SessionLocal() as session:
        access = session.query(
                Access
            ).options(
                selectinload(Access.in_out)
            ).filter(
                and_(
                    Access.idVehicle == id,
                    exists().where(
                        InOut.idAccess == Access.id
                    )
                )
            ).first()
        return access and len(access.in_out) > 0