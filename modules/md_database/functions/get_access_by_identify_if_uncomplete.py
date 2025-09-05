from sqlalchemy import func, and_, or_
from sqlalchemy.orm import selectinload
from modules.md_database.md_database import SessionLocal, InOut, Access, Vehicle, TypeAccess, AccessStatus

def get_access_by_identify_if_uncomplete(identify: str):
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
            selectinload(Access.subject),
            selectinload(Access.vector),
            selectinload(Access.driver),
            selectinload(Access.vehicle),
            selectinload(Access.in_out).selectinload(InOut.weight1),
            selectinload(Access.in_out).selectinload(InOut.weight2),
            selectinload(Access.in_out).selectinload(InOut.material)
        ).join(
            Vehicle, Access.idVehicle == Vehicle.id
        ).outerjoin(
            weighing_count_subquery,
            Access.id == weighing_count_subquery.c.idAccess
        ).outerjoin(
            last_inout_weight2_subq,
            Access.id == last_inout_weight2_subq.c.idAccess
        ).filter(
            or_(
                Access.badge == identify,
                Vehicle.plate == identify
            ),
            Access.type != TypeAccess.TEST.name,
            Access.status != AccessStatus.CLOSED.name,
            or_(
                weighing_count_subquery.c.weighing_count == None,
                weighing_count_subquery.c.weighing_count < Access.number_in_out,
                Access.number_in_out == None,
                and_(
                    weighing_count_subquery.c.weighing_count == Access.number_in_out,
                    last_inout_weight2_subq.c.idWeight2 == None
                )
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