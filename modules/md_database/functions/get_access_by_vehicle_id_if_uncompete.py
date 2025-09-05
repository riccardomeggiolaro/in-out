from sqlalchemy import func, and_, or_
from sqlalchemy.orm import joinedload, selectinload
from modules.md_database.md_database import SessionLocal, InOut, Access, Vehicle, TypeAccess, AccessStatus

def get_access_by_vehicle_id_if_uncomplete(id: int):
    session = SessionLocal()
    try:
        weighing_count_subquery = (
            session.query(
                InOut.idAccess,
                func.count(InOut.id).label("weighing_count")
            )
            .group_by(InOut.idAccess)
            .subquery()
        )

        last_inout_subq = (
            session.query(
                InOut.idAccess,
                func.max(InOut.id).label("last_inout_id")
            )
            .group_by(InOut.idAccess)
            .subquery()
        )

        last_inout_weight2_subq = (
            session.query(
                InOut.idAccess,
                InOut.idWeight2
            )
            .join(last_inout_subq, and_(
                InOut.idAccess == last_inout_subq.c.idAccess,
                InOut.id == last_inout_subq.c.last_inout_id
            ))
            .subquery()
        )

        access = session.query(Access).options(
            joinedload(Access.subject),
            joinedload(Access.vector),
            joinedload(Access.driver),
            joinedload(Access.vehicle),
            selectinload(Access.in_out)
        ).join(
            Vehicle, Access.idVehicle == Vehicle.id
        ).outerjoin(
            weighing_count_subquery,
            Access.id == weighing_count_subquery.c.idAccess
        ).outerjoin(
            last_inout_weight2_subq,
            Access.id == last_inout_weight2_subq.c.idAccess
        ).filter(
            Vehicle.id == id,
            Access.type != TypeAccess.TEST.name,
            Access.status != AccessStatus.CLOSED.name,
            or_(
                Access.number_in_out == None,
                # weighing_count is NULL (nessun InOut)
                weighing_count_subquery.c.weighing_count == None,
                # weighing_count < number_in_out
                weighing_count_subquery.c.weighing_count < Access.number_in_out,
                # weighing_count == number_in_out AND last_inout_weight2_subq.c.idWeight2 == None
                and_(
                    weighing_count_subquery.c.weighing_count == Access.number_in_out,
                    last_inout_weight2_subq.c.idWeight2 == None
                ),
            )
        ).order_by(
            Access.date_created.desc()
        ).first()

        if not access:
            return None

        session.commit()
        session.refresh(access)
        return access.__dict__

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()