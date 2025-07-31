from sqlalchemy import func, and_, or_
from sqlalchemy.orm import joinedload
from modules.md_database.md_database import SessionLocal, InOut, Reservation, Vehicle, TypeReservation

def get_reservation_by_vehicle_id_if_uncomplete(id: int):
    session = SessionLocal()
    try:
        weighing_count_subquery = (
            session.query(
                InOut.idReservation,
                func.count(InOut.id).label("weighing_count")
            )
            .group_by(InOut.idReservation)
            .subquery()
        )

        last_inout_subq = (
            session.query(
                InOut.idReservation,
                func.max(InOut.id).label("last_inout_id")
            )
            .group_by(InOut.idReservation)
            .subquery()
        )

        last_inout_weight2_subq = (
            session.query(
                InOut.idReservation,
                InOut.idWeight2
            )
            .join(last_inout_subq, and_(
                InOut.idReservation == last_inout_subq.c.idReservation,
                InOut.id == last_inout_subq.c.last_inout_id
            ))
            .subquery()
        )

        reservation = session.query(Reservation).options(
            joinedload(Reservation.subject),
            joinedload(Reservation.vector),
            joinedload(Reservation.driver),
            joinedload(Reservation.vehicle)
        ).join(
            Vehicle, Reservation.idVehicle == Vehicle.id
        ).outerjoin(
            weighing_count_subquery,
            Reservation.id == weighing_count_subquery.c.idReservation
        ).outerjoin(
            last_inout_weight2_subq,
            Reservation.id == last_inout_weight2_subq.c.idReservation
        ).filter(
            Vehicle.id == id,
            Reservation.type != TypeReservation.TEST.name,
            or_(
                Reservation.number_in_out == None,
                # weighing_count is NULL (nessun InOut)
                weighing_count_subquery.c.weighing_count == None,
                # weighing_count < number_in_out
                weighing_count_subquery.c.weighing_count < Reservation.number_in_out,
                # weighing_count == number_in_out AND last_inout_weight2_subq.c.idWeight2 == None
                and_(
                    weighing_count_subquery.c.weighing_count == Reservation.number_in_out,
                    last_inout_weight2_subq.c.idWeight2 == None
                )
            )
        ).order_by(
            Reservation.date_created.desc()
        ).first()

        if not reservation:
            return None

        session.commit()
        session.refresh(reservation)
        return reservation.__dict__

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()