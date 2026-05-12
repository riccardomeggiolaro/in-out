from sqlalchemy import or_
from modules.md_database.md_database import SessionLocal, Access, Vehicle, CardRegistry, AccessStatus

def get_access_by_identify_if_not_closed(identify: str):
    session = SessionLocal()
    try:
        access = session.query(Access).join(
            Vehicle, Access.idVehicle == Vehicle.id
        ).outerjoin(
            CardRegistry, Access.idCardRegistry == CardRegistry.id
        ).filter(
            or_(
                CardRegistry.code == identify,
                Vehicle.plate == identify
            ),
            Access.status != AccessStatus.CLOSED.name
        ).order_by(
            Access.date_created.desc()
        ).first()

        if not access:
            return None

        return {
            "id": access.id,
            "status": access.status,
            "mode": access.mode,
            "type": access.type
        }

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
