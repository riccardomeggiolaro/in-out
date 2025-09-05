from sqlalchemy import func, alias, case
from sqlalchemy.orm import selectinload
from modules.md_database.md_database import SessionLocal, Weighing, InOut

def get_in_out_by_id_access(id):
    """
    Gets the latest InOut record based on weigher_name.
    """
    session = SessionLocal()
    try:
        # Alias per le tabelle di pesate
        weight1_alias = alias(Weighing, name='w1')
        weight2_alias = alias(Weighing, name='w2')

        # CTE per l'ultimo InOut per ogni access
        latest_inout = session.query(
            InOut.idAccess,
            func.max(InOut.id).label('latest_id')
        ).group_by(InOut.idAccess).cte('latest_inout')

        # Query base per ottenere l'ultimo InOut
        query = session.query(
            InOut,
            case(
                (InOut.id == latest_inout.c.latest_id, True),
                else_=False
            ).label('is_last')
        ).options(
            selectinload(InOut.weight1),
            selectinload(InOut.weight2)
        ).outerjoin(
            latest_inout,
            InOut.idAccess == latest_inout.c.idAccess
        ).join(
            InOut.weight1
        ).filter(
            InOut.id == id
        ).order_by(Weighing.date.desc())  # Ordinamento per data di pesata

        # Seleziona solo il record più recente
        query = query.limit(1)  # Limitiamo a un solo record (l'ultimo)

        # Eseguiamo la query
        result = query.first()

        # Se troviamo un risultato, ritorniamo l'oggetto InOut
        if result:
            inout, _ = result
            return inout
        else:
            return None  # Se non troviamo nessun risultato, ritorniamo None

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()