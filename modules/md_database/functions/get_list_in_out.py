from sqlalchemy import func, or_, and_, alias
from sqlalchemy.orm import selectinload, defer
from modules.md_database.md_database import SessionLocal, Weighing, InOut, Access, AccessStatus, TypeAccess, User

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
    filterDateAccess=False,
    get_is_last=False,
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
        weight1_alias = alias(Weighing, name='w1')
        weight2_alias = alias(Weighing, name='w2')
        
        query = session.query(InOut)

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

        load_options = []
        
        if access_options:
            load_options.append(selectinload(InOut.access).options(*access_options))
        else:
            load_options.append(selectinload(InOut.access))
        
        load_options.append(selectinload(InOut.weight1).options(*weighing1_options))
        load_options.append(selectinload(InOut.weight2).options(*weighing2_options))
        
        if load_material:
            load_options.append(selectinload(InOut.material))

        query = query.options(*load_options)

        if excludeTestWeighing:
            query = query.join(InOut.access).filter(Access.type != TypeAccess.TEST)

        if filterDateAccess and (fromDate or toDate):
            query = query.join(InOut.access)
            if fromDate:
                query = query.filter(Access.date_created >= fromDate)
            if toDate:
                query = query.filter(Access.date_created <= toDate)
        else:
            if fromDate:
                query = query.outerjoin(weight1_alias, InOut.idWeight1 == weight1_alias.c.id)\
                            .outerjoin(weight2_alias, InOut.idWeight2 == weight2_alias.c.id)
                query = query.filter(
                    or_(
                        and_(InOut.idWeight1.isnot(None), weight1_alias.c.date >= fromDate),
                        and_(InOut.idWeight1.is_(None), InOut.idWeight2.isnot(None), weight2_alias.c.date >= fromDate)
                    )
                )

            if toDate:
                if not fromDate:
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

                if "." in key:
                    parts = key.split(".")
                    current_class = InOut
                    
                    for i, part in enumerate(parts[:-1]):
                        if not hasattr(current_class, part):
                            raise ValueError(f"Invalid relationship: {part}")
                        query = query.join(getattr(current_class, part))
                        current_class = current_class.__mapper__.relationships[part].mapper.class_

                    final_attr = parts[-1]
                    if not hasattr(current_class, final_attr):
                        raise ValueError(f"Invalid attribute: {final_attr}")
                        
                    if isinstance(value, str) and "%" in value:
                        query = query.filter(getattr(current_class, final_attr).like(value))
                    else:
                        query = query.filter(getattr(current_class, final_attr) == value)
                else:
                    if not hasattr(InOut, key):
                        raise ValueError(f"Invalid column: {key}")
                    
                    if isinstance(value, str) and "%" in value:
                        query = query.filter(getattr(InOut, key).like(value))
                    else:
                        query = query.filter(getattr(InOut, key) == value)

        if not_closed:
            query = query.join(InOut.access).filter(Access.status != AccessStatus.CLOSED)

        if only_in_out_with_weight2:
            query = query.filter(InOut.idWeight2 != None)

        if only_in_out_without_weight2:
            query = query.filter(InOut.idWeight2 == None)

        total_rows = query.count()

        if order_by:
            column_name, direction = order_by
            if hasattr(InOut, column_name):
                column = getattr(InOut, column_name)
            else:
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
            query = query.join(InOut.weight1).order_by(Weighing.date.desc())

        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        results = query.all()

        if get_is_last:
            for inout in results:
                inout.__dict__['is_last'] = inout.is_last
                if inout.access:
                    inout.access.__dict__['is_latest_for_vehicle'] = inout.access.is_latest_for_vehicle

        return results, total_rows

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()