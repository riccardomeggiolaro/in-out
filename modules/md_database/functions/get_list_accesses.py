from sqlalchemy import func
from sqlalchemy.orm import selectinload, defer
from sqlalchemy.sql import exists, and_, or_
from modules.md_database.md_database import SessionLocal, InOut, Access, AccessStatus, TypeAccess, Weighing, User
from datetime import datetime, date

def get_list_accesses(
    filters=None,
    not_closed=False,
    fromDate=None,
    toDate=None,
    limit=None,
    offset=None,
    order_by=None,
    exclude_test_access=False,
    permanent=None,
    get_is_last_for_vehicle=False,
    permanentIfWeight1=False,
    exclude_manually_access=False,
    load_subject=True,
    load_vector=True,
    load_driver=True,
    load_vehicle=True,
    load_operator=True,
    load_material=True,
    load_weighing_pictures=True,
    load_note=True,
    load_document_reference=True,
    load_date_weight1=True,
    load_pid_weight1=True,
    load_date_weight2=True,
    load_pid_weight2=True
):
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

        access_options = []
        if load_subject:
            access_options.append(selectinload(Access.subject))
        if load_vector:
            access_options.append(selectinload(Access.vector))
        if load_driver:
            access_options.append(selectinload(Access.driver))
        if load_vehicle:
            access_options.append(selectinload(Access.vehicle))
        if not load_note:
            access_options.append(defer(Access.note))
        if not load_document_reference:
            access_options.append(defer(Access.document_reference))

        weighing1_options = [
            selectinload(Weighing.user).load_only(User.username, User.description)
        ]
        if load_weighing_pictures:
            weighing1_options.append(selectinload(Weighing.weighing_pictures))
        if load_operator:
            weighing1_options.append(selectinload(Weighing.operator))
        if not load_date_weight1:
            weighing1_options.append(defer(Weighing.date))
        if not load_pid_weight1:
            weighing1_options.append(defer(Weighing.pid))

        weighing2_options = [
            selectinload(Weighing.user).load_only(User.username, User.description)
        ]
        if load_weighing_pictures:
            weighing2_options.append(selectinload(Weighing.weighing_pictures))
        if load_operator:
            weighing2_options.append(selectinload(Weighing.operator))
        if not load_date_weight2:
            weighing2_options.append(defer(Weighing.date))
        if not load_pid_weight2:
            weighing2_options.append(defer(Weighing.pid))

        inout_options = [
            selectinload(InOut.weight1).options(*weighing1_options),
            selectinload(InOut.weight2).options(*weighing2_options)
        ]
        if load_material:
            inout_options.append(selectinload(InOut.material))

        access_options.append(selectinload(Access.in_out).options(*inout_options))

        query = query.options(*access_options)

        query = query.outerjoin(
            weighing_count_subquery,
            Access.id == weighing_count_subquery.c.idAccess
        )

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

        if not_closed:
            query = query.filter(Access.status != AccessStatus.CLOSED)

        if exclude_test_access:
            query = query.filter(Access.type != TypeAccess.TEST.name)

        if exclude_manually_access:
            query = query.filter(Access.type != TypeAccess.MANUALLY.name)

        if permanent is not None:
            if permanent is True:
                query = query.filter(Access.number_in_out == None)
            elif permanent is False:
                query = query.filter(Access.number_in_out != None)

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

        total_rows = query.count()

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

        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)

        accesses = query.all()
        if get_is_last_for_vehicle:
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