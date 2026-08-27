from sqlalchemy.orm import selectinload
from modules.md_database.md_database import SessionLocal, InOut, Access, Weighing

def get_in_out_for_cloud_sync(after_id: int, limit: int = 50, only_closed: bool = True):
    """
    Ritorna i record InOut con id > after_id, ordinati per id crescente, pronti per essere
    inviati al portale cloud. Se only_closed è True, invia solo le pesate con Weight2 presente
    (accesso completato), evitando di sincronizzare pesate ancora in corso.
    """
    session = SessionLocal()
    try:
        query = session.query(InOut).options(
            selectinload(InOut.access).options(
                selectinload(Access.vehicle),
            ),
            selectinload(InOut.subject),
            selectinload(InOut.vector),
            selectinload(InOut.driver),
            selectinload(InOut.material),
            selectinload(InOut.weight1),
            selectinload(InOut.weight2),
        ).filter(InOut.id > after_id)

        if only_closed:
            query = query.filter(InOut.idWeight2.isnot(None))

        return query.order_by(InOut.id.asc()).limit(limit).all()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
