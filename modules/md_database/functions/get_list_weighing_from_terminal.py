from sqlalchemy import func, case, and_, or_
from sqlalchemy.orm import selectinload, defer, load_only
from sqlalchemy.sql import exists, and_, or_
from modules.md_database.md_database import SessionLocal, InOut, Access, AccessStatus, TypeAccess, Weighing, User, WeighingTerminal
from datetime import datetime, date

def get_list_weighing_from_terminal(
    filters=None,
    only_in_out_without_weight2=None,
    only_in_out_with_weight2=None,
    fromDate=None,
    toDate=None,
    limit=None,
    offset=None,
    order_by=None,
    load_subject=True,
    load_vehicle=True,
    load_material=True,
    load_note=True,
    load_date_weight1=True,
    load_pid_weight1=True,
    load_date_weight2=True,
    load_pid_weight2=True
):
    session = SessionLocal()
    try:
        query = session.query(WeighingTerminal)

        # Costruisci dinamicamente la lista delle colonne da caricare
        columns_to_load = ["bil", "net_weight"]
        if load_subject:
            columns_to_load += ["typeSubject", "subject"]
        if load_vehicle:
            columns_to_load.append("plate")
        if load_material:
            columns_to_load.append("material")
        if load_pid_weight1:
            columns_to_load += ["prog1", "pid1", "weight1"]
            if load_note:
                columns_to_load.append("notes1")
        if load_date_weight1:
            columns_to_load.append("date1")
        if load_pid_weight2:
            columns_to_load += ["prog2", "pid2", "weight2"]
            if load_note:
                columns_to_load.append("notes2")
        if load_date_weight2:
            columns_to_load.append("date2")

        # Usa load_only per caricare solo le colonne richieste
        if columns_to_load:
            orm_columns = [getattr(WeighingTerminal, col) for col in columns_to_load]
            query = query.options(load_only(*orm_columns))

        if filters:
            for key, value in filters.items():
                if "." in key:
                    parts = key.split(".")
                    rel_name = parts[0]
                    attr_name = parts[1]
                    if not hasattr(WeighingTerminal, rel_name):
                        raise ValueError(f"Relationship '{rel_name}' not found in WeighingTerminal table.")
                    related_model = WeighingTerminal.__mapper__.relationships[rel_name].mapper.class_
                    if not hasattr(related_model, attr_name):
                        raise ValueError(f"Attribute '{attr_name}' not found in relationship '{rel_name}'.")
                    if isinstance(value, str) and "%" in value:
                        query = query.join(getattr(WeighingTerminal, rel_name)).filter(
                            getattr(related_model, attr_name).like(value)
                        )
                    else:
                        query = query.join(getattr(WeighingTerminal, rel_name)).filter(
                            getattr(related_model, attr_name) == value
                        )
                else:
                    if hasattr(WeighingTerminal, key):
                        if isinstance(value, str) and "%" in value:
                            query = query.filter(getattr(WeighingTerminal, key).like(value))
                        else:
                            query = query.filter(getattr(WeighingTerminal, key) == value)
                    else:
                        raise ValueError(f"Column '{key}' not found in WeighingTerminal table.")

        # Gestione fromDate: usa datetime1 se disponibile, altrimenti datetime2
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
                query = query.filter(
                    or_(
                        and_(WeighingTerminal.datetime1.isnot(None), WeighingTerminal.datetime1 >= fromDate),
                        and_(WeighingTerminal.datetime1.is_(None), WeighingTerminal.datetime2 >= fromDate)
                    )
                )

        # Gestione toDate: usa datetime2 se disponibile, altrimenti datetime1
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
                query = query.filter(
                    or_(
                        and_(WeighingTerminal.datetime2.isnot(None), WeighingTerminal.datetime2 <= toDate),
                        and_(WeighingTerminal.datetime2.is_(None), WeighingTerminal.datetime1 <= toDate)
                    )
                )

        # Escludi record senza nessuna data (caso teorico)
        query = query.filter(
            or_(
                WeighingTerminal.datetime1.isnot(None),
                WeighingTerminal.datetime2.isnot(None)
            )
        )

        total_rows = query.count()

        if order_by:
            column_name, direction = order_by
            if not hasattr(WeighingTerminal, column_name):
                raise ValueError(f"Column '{column_name}' not found in WeighingTerminal table.")
            column = getattr(WeighingTerminal, column_name)
            if direction.lower() == 'asc':
                query = query.order_by(column.asc())
            elif direction.lower() == 'desc':
                query = query.order_by(column.desc())
            else:
                raise ValueError("Direction must be 'asc' or 'desc'.")
        else:
            query = query.order_by(WeighingTerminal.date_created.desc())

        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        if only_in_out_with_weight2:
            query = query.filter(WeighingTerminal.weight2 != None)
        if only_in_out_without_weight2:
            query = query.filter(WeighingTerminal.weight2 == None)

        accesses = query.all()
        return accesses, total_rows

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()