from sqlalchemy import func, or_, and_, alias
from sqlalchemy.orm import selectinload
from modules.md_database.md_database import SessionLocal, Weighing, InOut, Reservation, ReservationStatus, TypeReservation

def get_list_in_out(
    filters=None,
    not_closed=False,
    only_in_out_with_weight2=False,
    only_in_out_without_weight2=False,
    fromDate=None,
    toDate=None,
    limit=None,
    offset=None,
    order_by=None,
    excludeTestWeighing=False,
    filterDateReservation=False,
    get_is_last=False
):
    """
    Gets a list of InOut records with optional filtering.
    """
    session = SessionLocal()
    try:
        # Create aliases for the weighing tables
        weight1_alias = alias(Weighing, name='w1')
        weight2_alias = alias(Weighing, name='w2')
        
        # Base query semplificata - rimossa la CTE e il case per is_last
        query = session.query(InOut)

        # Add relationships
        query = query.options(
            selectinload(InOut.reservation).selectinload(Reservation.subject),
            selectinload(InOut.reservation).selectinload(Reservation.vector),
            selectinload(InOut.reservation).selectinload(Reservation.driver),
            selectinload(InOut.reservation).selectinload(Reservation.vehicle),
            selectinload(InOut.weight1),
            selectinload(InOut.weight2),
            selectinload(InOut.material)
        )

        # Escludi le reservation di tipo TEST se richiesto
        if excludeTestWeighing:
            query = query.join(InOut.reservation).filter(Reservation.type != TypeReservation.TEST)

        # Gestione filtro data su Reservation.date_created se richiesto
        if filterDateReservation and (fromDate or toDate):
            query = query.join(InOut.reservation)
            if fromDate:
                query = query.filter(Reservation.date_created >= fromDate)
            if toDate:
                query = query.filter(Reservation.date_created <= toDate)
        else:
            # Handle fromDate filter sulle pesate
            if fromDate:
                query = query.outerjoin(weight1_alias, InOut.idWeight1 == weight1_alias.c.id)\
                            .outerjoin(weight2_alias, InOut.idWeight2 == weight2_alias.c.id)
                query = query.filter(
                    or_(
                        and_(InOut.idWeight1.isnot(None), weight1_alias.c.date >= fromDate),
                        and_(InOut.idWeight1.is_(None), InOut.idWeight2.isnot(None), weight2_alias.c.date >= fromDate)
                    )
                )

            # Handle toDate filter sulle pesate
            if toDate:
                if not fromDate:  # Only add joins if not already added
                    query = query.outerjoin(weight2_alias, InOut.idWeight2 == weight2_alias.c.id)\
                                .outerjoin(weight1_alias, InOut.idWeight1 == weight1_alias.c.id)
                query = query.filter(
                    or_(
                        and_(InOut.idWeight2.isnot(None), weight2_alias.c.date <= toDate),
                        and_(InOut.idWeight2.is_(None), InOut.idWeight1.isnot(None), weight1_alias.c.date <= toDate)
                    )
                )

        if filters:
            for key, value in filters.items():
                # Handle weighing date filters
                if key.startswith("weight1.date_"):
                    query = query.join(InOut.weight1)
                    if key.endswith("_from"):
                        query = query.filter(Weighing.date >= value)
                    elif key.endswith("_to"):
                        query = query.filter(Weighing.date <= value)
                    continue
                    
                if key.startswith("weight2.date_"):
                    query = query.join(InOut.weight2)
                    if key.endswith("_from"):
                        query = query.filter(Weighing.date >= value)
                    elif key.endswith("_to"):
                        query = query.filter(Weighing.date <= value)
                    continue

                # Handle nested attributes 
                if "." in key:
                    parts = key.split(".")
                    current_class = InOut
                    
                    # Build the join chain and get the final attribute
                    for i, part in enumerate(parts[:-1]):
                        if not hasattr(current_class, part):
                            raise ValueError(f"Invalid relationship: {part}")
                        query = query.join(getattr(current_class, part))
                        current_class = current_class.__mapper__.relationships[part].mapper.class_

                    # Get the final attribute to filter on
                    final_attr = parts[-1]
                    if not hasattr(current_class, final_attr):
                        raise ValueError(f"Invalid attribute: {final_attr}")
                        
                    if isinstance(value, str) and "%" in value:
                        query = query.filter(getattr(current_class, final_attr).like(value))
                    else:
                        query = query.filter(getattr(current_class, final_attr) == value)
                else:
                    # Direct InOut attributes
                    if not hasattr(InOut, key):
                        raise ValueError(f"Invalid column: {key}")
                    
                    if isinstance(value, str) and "%" in value:
                        query = query.filter(getattr(InOut, key).like(value))
                    else:
                        query = query.filter(getattr(InOut, key) == value)

        if not_closed:
            query = query.join(InOut.reservation).filter(Reservation.status != ReservationStatus.CLOSED)

        # Filter for non-closed reservations if requested
        if only_in_out_with_weight2:
            query = query.filter(InOut.idWeight2 != None)

        # Filter for non-closed reservations if requested
        if only_in_out_without_weight2:
            query = query.filter(InOut.idWeight2 == None)

        total_rows = query.count()

        # Apply ordering
        if order_by:
            column_name, direction = order_by
            if hasattr(InOut, column_name):
                column = getattr(InOut, column_name)
            else:
                # Try ordering by joined table columns
                parts = column_name.split('.')
                current_class = InOut
                for part in parts[:-1]:
                    if not hasattr(current_class, part):
                        raise ValueError(f"Invalid relationship for ordering: {part}")
                    query = query.join(getattr(current_class, part))
                    current_class = current_class.__mapper__.relationships[part].mapper.class_
                column = getattr(current_class, parts[-1])
                
            query = query.order_by(column.asc() if direction.lower() == 'asc' else column.desc())
        else:
            # Default ordering by weighing date descending
            query = query.join(InOut.weight1).order_by(Weighing.date.desc())

        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        # Execute query - ora restituisce direttamente oggetti InOut
        results = query.all()

        if get_is_last:
            # Forza la valutazione delle hybrid properties per la serializzazione
            for inout in results:
                inout.__dict__['is_last'] = inout.is_last
                if inout.reservation:
                    inout.reservation.__dict__['is_latest_for_vehicle'] = inout.reservation.is_latest_for_vehicle

        return results, total_rows

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()