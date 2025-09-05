from sqlalchemy.orm import selectinload
from modules.md_database.md_database import SessionLocal, Weighing, InOut, Access

def get_last_in_out_by_weigher(weigher_name=None):
    """
    Gets a list of InOut records with optional filtering.
    """
    session = SessionLocal()
    id_in_out = None
    in_out = None
    try:
        query = session.query(Weighing
                ).options(
                    selectinload(Weighing.in_out_weight1),
                    selectinload(Weighing.in_out_weight2)
                ).filter(
                    Weighing.weigher == weigher_name
                ).order_by(Weighing.date.desc()).first()
        if query:
            if len(query.in_out_weight1) > 0:
                id_in_out = query.in_out_weight1[-1].id
            elif len(query.in_out_weight2) > 0:
                id_in_out = query.in_out_weight2[-1].id
        if id_in_out:
            in_out = session.query(InOut
                    ).options(
                        selectinload(InOut.access).options(
                            selectinload(Access.vehicle),
                            selectinload(Access.driver),
                            selectinload(Access.subject),
                            selectinload(Access.vector)
                        ),
                        selectinload(InOut.material),
                        selectinload(InOut.weight1),
                        selectinload(InOut.weight2)
                    ).filter(
                        InOut.id == id_in_out
                    ).first()
        return in_out
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()