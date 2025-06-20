from sqlalchemy import func, or_, and_, alias, case, literal, select, exists
from sqlalchemy.orm import selectinload, aliased
from modules.md_database.md_database import SessionLocal, Weighing, InOut, Reservation, ReservationStatus
from datetime import datetime, date

def get_list_in_out(filters=None, not_closed=True, fromDate=None, toDate=None, limit=None, offset=None, order_by=None, is_last=False):
    """
    Gets a list of InOut records with optional filtering.
    
    Args:
        filters (dict): Dictionary of filters including:
            - InOut field filters
            - Reservation field filters (e.g. "reservation.subject.social_reason": "Company%")
            - weight1.date_from/weight1.date_to: For first weighing date range
            - weight2.date_from/weight2.date_to: For second weighing date range
        not_closed (bool): If True, only returns pesate for non-closed reservations
        fromDate (datetime): Start date to filter weighings (applies to weight1 if exists, otherwise weight2)
        toDate (datetime): End date to filter weighings (applies to weight2 if exists, otherwise weight1)
        limit (int): Maximum number of rows to return
        offset (int): Number of rows to skip
        order_by (tuple): Tuple containing (column_name, direction) for ordering
    """
    session = SessionLocal()
    try:
        # Create aliases for the weighing tables
        weight1_alias = alias(Weighing, name='w1')
        weight2_alias = alias(Weighing, name='w2')
        
        # Create a CTE for the latest InOut per reservation
        latest_inout = session.query(
            InOut.idReservation,
            func.max(InOut.id).label('latest_id')
        ).group_by(InOut.idReservation).cte('latest_inout')

        # Create base query that includes is_last in the main SELECT
        query = session.query(
            InOut,
            case(
                (InOut.id == latest_inout.c.latest_id, True),
                else_=False
            ).label('is_last')
        ).outerjoin(
            latest_inout,
            InOut.idReservation == latest_inout.c.idReservation
        )

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

        # Handle fromDate filter
        if fromDate:
            query = query.outerjoin(weight1_alias, InOut.idWeight1 == weight1_alias.c.id)\
                        .outerjoin(weight2_alias, InOut.idWeight2 == weight2_alias.c.id)
            query = query.filter(
                or_(
                    and_(InOut.idWeight1.isnot(None), weight1_alias.c.date >= fromDate),
                    and_(InOut.idWeight1.is_(None), InOut.idWeight2.isnot(None), weight2_alias.c.date >= fromDate)
                )
            )

        # Handle toDate filter
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

        # Filter for non-closed reservations if requested
        if not_closed:
            query = query.join(InOut.reservation).filter(Reservation.status != ReservationStatus.CLOSED)

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

        # Execute query and transform results
        results = query.all()
        data = []
        for inout, is_last in results:
            inout_dict = inout
            inout_dict.is_last = is_last
            data.append(inout_dict)
            
        return data, total_rows

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()