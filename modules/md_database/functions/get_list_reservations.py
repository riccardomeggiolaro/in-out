from sqlalchemy import func
from sqlalchemy.orm import selectinload
from modules.md_database.md_database import SessionLocal, InOut, Reservation, ReservationStatus, TypeReservation, Weighing
from datetime import datetime, date

def get_list_reservations(filters=None, not_closed=False, fromDate=None, toDate=None, limit=None, offset=None, order_by=None, exclude_test_reservation=False, permanent=None, get_is_last_for_vehicle=False):
    """
    Gets a list of reservations with optional filtering for incomplete reservations
    and additional filters on any reservation field or related entities.
    """
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

        query = session.query(Reservation)

        query = query.options(
            selectinload(Reservation.subject),
            selectinload(Reservation.vector),
            selectinload(Reservation.driver),
            selectinload(Reservation.vehicle),
            selectinload(Reservation.in_out)
                .selectinload(InOut.weight1)
                .selectinload(Weighing.weighing_pictures),
            selectinload(Reservation.in_out)
                .selectinload(InOut.weight2)
                .selectinload(Weighing.weighing_pictures),
            selectinload(Reservation.in_out).selectinload(InOut.material)
        )

        query = query.outerjoin(
            weighing_count_subquery,
            Reservation.id == weighing_count_subquery.c.idReservation
        )

        # Filtri generici
        if filters:
            for key, value in filters.items():
                if "." in key:
                    parts = key.split(".")
                    rel_name = parts[0]
                    attr_name = parts[1]
                    if not hasattr(Reservation, rel_name):
                        raise ValueError(f"Relationship '{rel_name}' not found in Reservation table.")
                    related_model = Reservation.__mapper__.relationships[rel_name].mapper.class_
                    if not hasattr(related_model, attr_name):
                        raise ValueError(f"Attribute '{attr_name}' not found in relationship '{rel_name}'.")
                    if isinstance(value, str) and "%" in value:
                        query = query.join(getattr(Reservation, rel_name)).filter(
                            getattr(related_model, attr_name).like(value)
                        )
                    else:
                        query = query.join(getattr(Reservation, rel_name)).filter(
                            getattr(related_model, attr_name) == value
                        )
                else:
                    if hasattr(Reservation, key):
                        if isinstance(value, str) and "%" in value:
                            query = query.filter(getattr(Reservation, key).like(value))
                        else:
                            query = query.filter(getattr(Reservation, key) == value)
                    else:
                        raise ValueError(f"Column '{key}' not found in Reservation table.")

        query = query.filter(Reservation.hidden == False)

        # Filtro per status NOT_CLOSED
        if not_closed:
            query = query.filter(Reservation.status != ReservationStatus.CLOSED)

        # Filtro per exclude_test_reservation
        if exclude_test_reservation:
            query = query.filter(Reservation.type != TypeReservation.TEST.name)

        if permanent is not None:
            if permanent is True:
                query = query.filter(Reservation.number_in_out == None)
            elif permanent is False:
                query = query.filter(Reservation.number_in_out != None)

        # Filtro per data di inizio
        if fromDate:
            if isinstance(fromDate, str):
                try:
                    fromDate = datetime.fromisoformat(fromDate)
                except ValueError:
                    formats_to_try = [
                        "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y",
                        "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S"
                    ]
                    for fmt in formats_to_try:
                        try:
                            fromDate = datetime.strptime(fromDate, fmt)
                            break
                        except ValueError:
                            continue
            if isinstance(fromDate, (datetime, date)):
                query = query.filter(Reservation.date_created >= fromDate)

        # Filtro per data di fine
        if toDate:
            if isinstance(toDate, str):
                try:
                    toDate = datetime.fromisoformat(toDate)
                except ValueError:
                    formats_to_try = [
                        "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y",
                        "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S"
                    ]
                    for fmt in formats_to_try:
                        try:
                            toDate = datetime.strptime(toDate, fmt)
                            break
                        except ValueError:
                            continue
            if isinstance(toDate, (datetime, date)):
                query = query.filter(Reservation.date_created <= toDate)

        # Conta totale risultati
        total_rows = query.count()

        # Ordinamento
        if order_by:
            column_name, direction = order_by
            if not hasattr(Reservation, column_name):
                raise ValueError(f"Column '{column_name}' not found in Reservation table.")
            column = getattr(Reservation, column_name)
            if direction.lower() == 'asc':
                query = query.order_by(column.asc())
            elif direction.lower() == 'desc':
                query = query.order_by(column.desc())
            else:
                raise ValueError("Direction must be 'asc' or 'desc'.")
        else:
            query = query.order_by(Reservation.date_created.desc())

        # Paginazione
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)

        reservations = query.all()
        if get_is_last_for_vehicle:
            # Forza la valutazione della hybrid property
            for res in reservations:
                res.__dict__['is_latest_for_vehicle'] = res.is_latest_for_vehicle
                for index, in_out in enumerate(res.in_out):
                    res.__dict__['in_out'][index].__dict__['is_last'] = in_out.is_last
        return reservations, total_rows

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()