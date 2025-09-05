from modules.md_database.md_database import SessionLocal, Weighing
from datetime import datetime, date

def get_list_weighings(filters=None, weigher_name=None, fromDate=None, toDate=None, limit=None, offset=None, order_by=None):
    """
    Gets a list of accesses with optional filtering for incomplete accesses
    and additional filters on any access field or related entities.
    """
    session = SessionLocal()
    try:
        query = session.query(Weighing)

        # Filtri generici
        if filters:
            for key, value in filters.items():
                if "." in key:
                    parts = key.split(".")
                    rel_name = parts[0]
                    attr_name = parts[1]
                    if not hasattr(Weighing, rel_name):
                        raise ValueError(f"Relationship '{rel_name}' not found in Weighing table.")
                    related_model = Weighing.__mapper__.relationships[rel_name].mapper.class_
                    if not hasattr(related_model, attr_name):
                        raise ValueError(f"Attribute '{attr_name}' not found in relationship '{rel_name}'.")
                    if isinstance(value, str) and "%" in value:
                        query = query.join(getattr(Weighing, rel_name)).filter(
                            getattr(related_model, attr_name).like(value)
                        )
                    else:
                        query = query.join(getattr(Weighing, rel_name)).filter(
                            getattr(related_model, attr_name) == value
                        )
                else:
                    if hasattr(Weighing, key):
                        if isinstance(value, str) and "%" in value:
                            query = query.filter(getattr(Weighing, key).like(value))
                        else:
                            query = query.filter(getattr(Weighing, key) == value)
                    else:
                        raise ValueError(f"Column '{key}' not found in Weighing table.")

        # Filtro per pesa
        if weigher_name:
            if isinstance(weigher_name, str):
                query = query.filter(Weighing.weigher == weigher_name)

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
                query = query.filter(Weighing.date >= fromDate)

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
                query = query.filter(Weighing.date <= toDate)

        # Conta totale risultati
        total_rows = query.count()

        # Ordinamento
        if order_by:
            column_name, direction = order_by
            if not hasattr(Weighing, column_name):
                raise ValueError(f"Column '{column_name}' not found in Access table.")
            column = getattr(Weighing, column_name)
            if direction.lower() == 'asc':
                query = query.order_by(column.asc())
            elif direction.lower() == 'desc':
                query = query.order_by(column.desc())
            else:
                raise ValueError("Direction must be 'asc' or 'desc'.")
        else:
            query = query.order_by(Weighing.date.desc())

        # Paginazione
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)

        accesses = query.all()
        return accesses, total_rows

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()