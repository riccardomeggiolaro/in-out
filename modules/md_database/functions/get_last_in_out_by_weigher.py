from sqlalchemy.orm import selectinload
from modules.md_database.md_database import SessionLocal, Weighing
from modules.md_database.functions.get_data_by_id import get_data_by_id

def get_last_in_out_by_weigher(weigher_name=None):
    """
    Gets a list of InOut records with optional filtering.
    """
    session = SessionLocal()
    try:
        in_out = None
        query = session.query(Weighing
                ).options(
                    selectinload(Weighing.in_out_weight1),
                    selectinload(Weighing.in_out_weight2)
                ).filter(
                    Weighing.weigher == weigher_name
                ).order_by(Weighing.date.desc()).first()
        if query:
            if len(query.in_out_weight1) > 0:
                in_out = get_data_by_id("in_out", query.in_out_weight1[-1].id)
            elif len(query.in_out_weight2) > 0:
                in_out = get_data_by_id("in_out", query.in_out_weight2[-1].id)
        return in_out
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()