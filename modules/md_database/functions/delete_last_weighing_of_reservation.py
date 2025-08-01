from sqlalchemy import desc
from sqlalchemy.orm import selectinload
from modules.md_database.md_database import SessionLocal, InOut, Weighing, Reservation, TypeReservation
import libs.lb_log as lb_log

def delete_last_weighing_of_reservation(reservation_id):
    """
    Rimuove il riferimento all'ultima pesata solo dall'InOut più recente associato 
    alla prenotazione specificata.
    """
    with SessionLocal() as session:
        try:
            # Trova l'ultimo InOut per la prenotazione
            latest_inout = session.query(InOut).options(
                    selectinload(InOut.weight1).selectinload(Weighing.in_out_weight1),
                    selectinload(InOut.weight1).selectinload(Weighing.in_out_weight2),
                    selectinload(InOut.weight2).selectinload(Weighing.in_out_weight1),
                    selectinload(InOut.weight2).selectinload(Weighing.in_out_weight2)
                ).filter(
                    InOut.idReservation == reservation_id
                ).order_by(desc(InOut.id)).first()

            # lb_log.warning(latest_inout.weight1.__dict__ if latest_inout.idWeight1 else None)

            if not latest_inout:
                raise ValueError(f"No InOut records found for reservation {reservation_id}")

            if latest_inout.idWeight2:
                latest_inout.idWeight2 = None
                if latest_inout.idWeight1 and latest_inout.weight1.in_out_weight2:
                    latest_inout.idWeight1 = None
            elif latest_inout.idWeight2 is None and latest_inout.idWeight1:
                latest_inout.idWeight1 = None
            
            # Se l'InOut non ha più pesate associate, eliminalo
            if latest_inout.idWeight1 is None and latest_inout.idWeight2 is None:
                # Se la reservation è MANUALLY elimina anche la reservation
                # reservation = session.query(Reservation).get(latest_inout.idReservation)
                # if reservation and reservation.type != TypeReservation.RESERVATION:
                #     session.delete(reservation)
                session.delete(latest_inout)
            else:
                # Altrimenti, resetta solo il peso netto
                latest_inout.net_weight = None

            session.commit()
            return latest_inout.__dict__

        except Exception as e:
            session.rollback()
            raise e