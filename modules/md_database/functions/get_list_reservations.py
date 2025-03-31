from sqlalchemy import func
from sqlalchemy.orm import joinedload, selectinload
from modules.md_database.md_database import table_models, SessionLocal, Weighing, Reservation

def get_list_reservations(only_uncomplete=False, filters=None, limit=None, offset=None, order_by=None):
    """
    Gets a list of reservations with optional filtering for incomplete reservations
    and additional filters on any reservation field or related entities.
    
    Args:
        only_uncomplete (bool): If True, only returns reservations with missing or insufficient weighings.
        filters (dict): Dictionary of filters (column_name: value) for search. Can include nested attributes.
        limit (int): Maximum number of rows to return.
        offset (int): Number of rows to skip.
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
                Weighing.idReservation,
                func.count(Weighing.id).label("weighing_count")
            )
            .group_by(Weighing.idReservation)
            .subquery()
        )
        
        # Start with base query
        query = session.query(Reservation)
        
        # Load all relationships including weighings
        for rel_name, rel_obj in Reservation.__mapper__.relationships.items():
            # Use selectinload to efficiently load all relationships and nested relationships
            query = query.options(selectinload(getattr(Reservation, rel_name)))
        
        # Join with the weighing count subquery
        query = query.outerjoin(
            weighing_count_subquery,
            Reservation.id == weighing_count_subquery.c.idReservation
        )
        
        # Apply filter for incomplete reservations if only_uncomplete is True
        if only_uncomplete:
            query = query.filter(
                (
                    ((weighing_count_subquery.c.weighing_count == None) & (Reservation.number_weighings > 0)) |
                    (weighing_count_subquery.c.weighing_count < Reservation.number_weighings)
                )
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