from sqlalchemy import desc
from sqlalchemy.orm import selectinload
from modules.md_database.md_database import SessionLocal, InOut, Weighing, Access, Vehicle

def delete_last_weighing_of_access(access_id):
    """
    Rimuove il riferimento all'ultima pesata solo dall'InOut più recente associato 
    alla prenotazione specificata.
    """
    with SessionLocal() as session:
        try:
            # Trova l'ultimo InOut per la prenotazione
            latest_inout = session.query(InOut).options(
                    selectinload(InOut.access).selectinload(Access.vehicle).selectinload(Vehicle.accesses),
                    selectinload(InOut.weight1).selectinload(Weighing.in_out_weight1),
                    selectinload(InOut.weight1).selectinload(Weighing.in_out_weight2),
                    selectinload(InOut.weight2).selectinload(Weighing.in_out_weight1),
                    selectinload(InOut.weight2).selectinload(Weighing.in_out_weight2)
                ).filter(
                    InOut.idAccess == access_id
                ).order_by(desc(InOut.id)).first()

            if latest_inout.access.vehicle and latest_inout.access.vehicle.accesses[-1].id != access_id:
                raise ValueError(f"E' possibile cancellare l'ultima pesata fatta solo dell'ultimo accesso con la targa '{latest_inout.access.vehicle.plate}'")

            if not latest_inout:
                raise ValueError(f"No InOut records found for access {access_id}")

            if latest_inout.idWeight2:
                latest_inout.idWeight2 = None
                if latest_inout.idWeight1 and latest_inout.weight1.in_out_weight2:
                    latest_inout.idWeight1 = None
            elif latest_inout.idWeight2 is None and latest_inout.idWeight1:
                latest_inout.idWeight1 = None
            
            # Se l'InOut non ha più pesate associate, eliminalo
            if latest_inout.idWeight1 is None and latest_inout.idWeight2 is None:
                # Se la access è MANUALLY elimina anche la access
                # access = session.query(Access).get(latest_inout.idAccess)
                # if access and access.type != TypeAccess.RESERVATION:
                #     session.delete(access)
                session.delete(latest_inout)
            else:
                # Altrimenti, resetta solo il peso netto
                latest_inout.net_weight = None

            session.commit()
            return latest_inout.__dict__

        except Exception as e:
            session.rollback()
            raise e