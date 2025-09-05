from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import exists, and_, or_
from modules.md_database.md_database import SessionLocal, InOut, Access, AccessStatus, TypeAccess, Weighing
from datetime import datetime, date

def get_list_accesses(filters=None, not_closed=False, fromDate=None, toDate=None, limit=None, offset=None, order_by=None, exclude_test_access=False, permanent=None, get_is_last_for_vehicle=False, permanentIfWeight1=False):
    """
    Gets a list of accesses with optional filtering for incomplete accesses
    and additional filters on any access field or related entities.
    """
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

        query = session.query(Access)

        query = query.options(
            selectinload(Access.subject),
            selectinload(Access.vector),
            selectinload(Access.driver),
            selectinload(Access.vehicle),
            selectinload(Access.in_out)
                .selectinload(InOut.weight1)
                .selectinload(Weighing.weighing_pictures),
            selectinload(Access.in_out)
                .selectinload(InOut.weight2)
                .selectinload(Weighing.weighing_pictures),
            selectinload(Access.in_out).selectinload(InOut.material)
        )

        query = query.outerjoin(
            weighing_count_subquery,
            Access.id == weighing_count_subquery.c.idAccess
        )

        # Filtri generici
        if filters:
            for key, value in filters.items():
                if "." in key:
                    parts = key.split(".")
                    rel_name = parts[0]
                    attr_name = parts[1]
                    if not hasattr(Access, rel_name):
                        raise ValueError(f"Relationship '{rel_name}' not found in Access table.")
                    related_model = Access.__mapper__.relationships[rel_name].mapper.class_
                    if not hasattr(related_model, attr_name):
                        raise ValueError(f"Attribute '{attr_name}' not found in relationship '{rel_name}'.")
                    if isinstance(value, str) and "%" in value:
                        query = query.join(getattr(Access, rel_name)).filter(
                            getattr(related_model, attr_name).like(value)
                        )
                    else:
                        query = query.join(getattr(Access, rel_name)).filter(
                            getattr(related_model, attr_name) == value
                        )
                else:
                    if hasattr(Access, key):
                        if isinstance(value, str) and "%" in value:
                            query = query.filter(getattr(Access, key).like(value))
                        else:
                            query = query.filter(getattr(Access, key) == value)
                    else:
                        raise ValueError(f"Column '{key}' not found in Access table.")

        query = query.filter(Access.hidden == False)

        # Filtro per status NOT_CLOSED
        if not_closed:
            query = query.filter(Access.status != AccessStatus.CLOSED)

        # Filtro per exclude_test_access
        if exclude_test_access:
            query = query.filter(Access.type != TypeAccess.TEST.name)

        if permanent is not None:
            if permanent is True:
                query = query.filter(Access.number_in_out == None)
            elif permanent is False:
                query = query.filter(Access.number_in_out != None)

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
                query = query.filter(Access.date_created >= fromDate)

        if permanentIfWeight1:
            query = query.filter(
                or_(
                    Access.number_in_out != None,
                    and_(
                        Access.number_in_out == None,
                        exists().where(
                            and_(
                                InOut.idAccess == Access.id,
                                InOut.idWeight1 != None,
                                InOut.idWeight2 == None
                            )
                        )
                    )
                )
            )

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
                query = query.filter(Access.date_created <= toDate)

        # Conta totale risultati
        total_rows = query.count()

        # Ordinamento
        if order_by:
            column_name, direction = order_by
            if not hasattr(Access, column_name):
                raise ValueError(f"Column '{column_name}' not found in Access table.")
            column = getattr(Access, column_name)
            if direction.lower() == 'asc':
                query = query.order_by(column.asc())
            elif direction.lower() == 'desc':
                query = query.order_by(column.desc())
            else:
                raise ValueError("Direction must be 'asc' or 'desc'.")
        else:
            query = query.order_by(Access.date_created.desc())

        # Paginazione
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)

        accesses = query.all()
        if get_is_last_for_vehicle:
            # Forza la valutazione della hybrid property
            for res in accesses:
                res.__dict__['is_latest_for_vehicle'] = res.is_latest_for_vehicle
                for index, in_out in enumerate(res.in_out):
                    res.__dict__['in_out'][index].__dict__['is_last'] = in_out.is_last
        return accesses, total_rows

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()