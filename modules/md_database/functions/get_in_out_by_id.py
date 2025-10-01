from sqlalchemy.orm import selectinload
from modules.md_database.md_database import SessionLocal, InOut, Access, Weighing

def get_last_in_out_by_id(id):
    """
    Gets a list of InOut records with optional filtering.
    """
    session = SessionLocal()
    try:
        in_out = session.query(InOut
                ).options(
                    selectinload(InOut.access).options(
                        selectinload(Access.vehicle),
                        selectinload(Access.driver),
                        selectinload(Access.subject),
                        selectinload(Access.vector)
                    ),
                    selectinload(InOut.weight1).options(
                        selectinload(Weighing.weighing_pictures),
                        selectinload(Weighing.user),
                        selectinload(Weighing.operator)
                    ),
                    selectinload(InOut.weight2).options(
                        selectinload(Weighing.weighing_pictures),
                        selectinload(Weighing.user),
                        selectinload(Weighing.operator)
                    ),
                    selectinload(InOut.material)
                ).filter(
                    InOut.id == id
                ).first()
        return in_out
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()