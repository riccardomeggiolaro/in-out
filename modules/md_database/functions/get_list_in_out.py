from sqlalchemy import func, or_, and_
from sqlalchemy.orm import selectinload
from modules.md_database.md_database import SessionLocal, Weighing, InOut, Reservation, ReservationStatus
from datetime import datetime, date

def get_list_in_out(filters=None, not_closed=True, limit=None, offset=None, order_by=None):
    """
    Gets a list of InOut records with optional filtering.
    
    Args:
        filters (dict): Dictionary of filters including:
            - InOut field filters
            - Reservation field filters (e.g. "reservation.subject.social_reason": "Company%")
            - weight1.date_from/weight1.date_to: For first weighing date range
            - weight2.date_from/weight2.date_to: For second weighing date range
        not_closed (bool): If True, only returns pesate for non-closed reservations
        limit (int): Maximum number of rows to return
        offset (int): Number of rows to skip
        order_by (tuple): Tuple containing (column_name, direction) for ordering
    """
    session = SessionLocal()
    try:
        # Base query on InOut with all relationships
        query = session.query(InOut).options(
            selectinload(InOut.reservation).selectinload(Reservation.subject),
            selectinload(InOut.reservation).selectinload(Reservation.vector),
            selectinload(InOut.reservation).selectinload(Reservation.driver),
            selectinload(InOut.reservation).selectinload(Reservation.vehicle),
            selectinload(InOut.weight1),
            selectinload(InOut.weight2),
            selectinload(InOut.material)
        )

        if filters:
            for key, value in filters.items():
                # Handle weighing date filters
                if key.startswith("weight1.date_"):
                    query = query.join(InOut.weight1)
                    if key.endswith("_from"):
                        query = query.filter(Weighing.date >= convert_to_datetime(value))
                    elif key.endswith("_to"):
                        query = query.filter(Weighing.date <= convert_to_datetime(value))
                    continue
                    
                if key.startswith("weight2.date_"):
                    query = query.join(InOut.weight2)
                    if key.endswith("_from"):
                        query = query.filter(Weighing.date >= convert_to_datetime(value))
                    elif key.endswith("_to"):
                        query = query.filter(Weighing.date <= convert_to_datetime(value))
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

        return query.all(), total_rows

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()