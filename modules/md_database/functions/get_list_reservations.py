from sqlalchemy import func
from sqlalchemy.orm import selectinload
from modules.md_database.md_database import SessionLocal, InOut, Reservation, ReservationStatus, Weighing
from datetime import datetime, date

def get_list_reservations(filters=None, not_closed=True, fromDate=None, toDate=None, limit=None, offset=None, order_by=None):
    """
    Gets a list of reservations with optional filtering for incomplete reservations
    and additional filters on any reservation field or related entities.
    
    Args:
        only_uncomplete (bool): If True, only returns reservations with missing or insufficient weighings.
        filters (dict): Dictionary of filters (column_name: value) for search. Can include nested attributes.
        limit (int): Maximum number of rows to return.
        offset (int): Number of rows to skip.
        fromDate (str or datetime): Start date to filter by date_created. Default is None.
        toDate (str or datetime): End date to filter by date_created. Default is None.
        order_by (tuple): Tuple containing (column_name, direction) for ordering.
            Direction can be 'asc' or 'desc'. Default is (date_created, desc).
            
    Returns:
        tuple: A tuple containing:
            - a list of reservation objects with all relationships loaded
            - the total number of rows that match the criteria
    """
    session = SessionLocal()
    try:
        # Create a subquery that counts weighings for each reservation
        weighing_count_subquery = (
            session.query(
                InOut.idReservation,
                func.count(InOut.id).label("weighing_count")
            )
            .group_by(InOut.idReservation)
            .subquery()
        )
        
        # Start with base query
        query = session.query(Reservation)
        
        query = query.options(
            selectinload(Reservation.subject),
            selectinload(Reservation.vector),
            selectinload(Reservation.driver),
            selectinload(Reservation.vehicle),
            selectinload(Reservation.in_out)
                .selectinload(InOut.weight1)
                .selectinload(Weighing.weighing_pictures),   # <-- aggiungi questa riga
            selectinload(Reservation.in_out)
                .selectinload(InOut.weight2)
                .selectinload(Weighing.weighing_pictures),   # <-- aggiungi questa riga
            selectinload(Reservation.in_out).selectinload(InOut.material)
        )

        # Join with the weighing count subquery
        query = query.outerjoin(
            weighing_count_subquery,
            Reservation.id == weighing_count_subquery.c.idReservation
        )
        
        # Apply additional filters if specified
        if filters:
            for key, value in filters.items():
                # Handle nested attributes (e.g. "subject.social_reason")
                if "." in key:
                    parts = key.split(".")
                    rel_name = parts[0]
                    attr_name = parts[1]
                    
                    # Verify that the relationship exists
                    if not hasattr(Reservation, rel_name):
                        raise ValueError(f"Relationship '{rel_name}' not found in Reservation table.")
                    
                    # Get the related model
                    related_model = Reservation.__mapper__.relationships[rel_name].mapper.class_
                    
                    # Verify that the attribute exists in the related model
                    if not hasattr(related_model, attr_name):
                        raise ValueError(f"Attribute '{attr_name}' not found in relationship '{rel_name}'.")

                    if isinstance(value, str):
                        # For strings, handle % properly for LIKE queries
                        if "%" in value:
                            # It's already a pattern for LIKE
                            query = query.join(getattr(Reservation, rel_name)).filter(
                                getattr(related_model, attr_name).like(value)
                            )
                        else:
                            # Exact match
                            query = query.join(getattr(Reservation, rel_name)).filter(
                                getattr(related_model, attr_name) == value
                            )
                    elif isinstance(value, int):
                        query = query.join(getattr(Reservation, rel_name)).filter(
                            getattr(related_model, attr_name) == value
                        )
                    elif value is None:
                        query = query.join(getattr(Reservation, rel_name)).filter(
                            getattr(related_model, attr_name).is_(None)
                        )
                else:
                    # Handle direct attributes
                    if hasattr(Reservation, key):
                        if isinstance(value, str):
                            # For strings, handle % properly for LIKE queries
                            if "%" in value:
                                # It's already a pattern for LIKE
                                query = query.filter(getattr(Reservation, key).like(value))
                            else:
                                # Exact match if no wildcard
                                query = query.filter(getattr(Reservation, key) == value)
                        elif isinstance(value, int):
                            query = query.filter(getattr(Reservation, key) == value)
                        elif value is None:
                            query = query.filter(getattr(Reservation, key).is_(None))
                    else:
                        raise ValueError(f"Column '{key}' not found in Reservation table.")

        if not_closed:
            query = query.filter(Reservation.status != ReservationStatus.CLOSED)
        
        # Apply date range filters if specified
        if fromDate:
            # Handle various input types and ensure we're dealing with a datetime object
            if fromDate:
                if isinstance(fromDate, dict) or not fromDate:
                    # Skip invalid input
                    pass
                elif isinstance(fromDate, str):
                    try:
                        # Try ISO format first
                        fromDate = datetime.fromisoformat(fromDate)
                        query = query.filter(Reservation.date_created >= fromDate)
                    except ValueError:
                        try:
                            # Then try common date formats
                            formats_to_try = [
                                "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", 
                                "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S"
                            ]
                            
                            for fmt in formats_to_try:
                                try:
                                    fromDate = datetime.strptime(fromDate, fmt)
                                    query = query.filter(Reservation.date_created >= fromDate)
                                    break
                                except ValueError:
                                    continue
                        except Exception:
                            # If all parsing fails, skip this filter
                            pass
                elif isinstance(fromDate, (datetime, date)):
                    # Already a datetime or date object
                    query = query.filter(Reservation.date_created >= fromDate)
            
        if toDate:
            # Handle various input types and ensure we're dealing with a datetime object
            if toDate:
                if isinstance(toDate, dict) or not toDate:
                    # Skip invalid input
                    pass
                elif isinstance(toDate, str):
                    try:
                        # Try ISO format first
                        toDate = datetime.fromisoformat(toDate)
                        query = query.filter(Reservation.date_created <= toDate)
                    except ValueError:
                        try:
                            # Then try common date formats
                            formats_to_try = [
                                "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", 
                                "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S"
                            ]
                            
                            for fmt in formats_to_try:
                                try:
                                    toDate = datetime.strptime(toDate, fmt)
                                    query = query.filter(Reservation.date_created <= toDate)
                                    break
                                except ValueError:
                                    continue
                        except Exception:
                            # If all parsing fails, skip this filter
                            pass
                elif isinstance(toDate, (datetime, date)):
                    # Already a datetime or date object
                    query = query.filter(Reservation.date_created <= toDate)
        
        # Get total count of matching rows
        total_rows = query.count()
        
        # Apply ordering
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
            # Default ordering by creation date descending
            query = query.order_by(Reservation.date_created.desc())
        
        # Apply pagination
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        
        # Execute the query
        reservations = query.all()
        
        return reservations, total_rows
    
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()