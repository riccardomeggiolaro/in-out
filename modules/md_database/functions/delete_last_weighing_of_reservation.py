from sqlalchemy import desc
from modules.md_database.md_database import SessionLocal, InOut, Weighing, Reservation, TypeReservation

def delete_last_weighing_of_reservation(reservation_id):
    """
    Rimuove il riferimento all'ultima pesata solo dall'InOut più recente associato 
    alla prenotazione specificata.
    """
    with SessionLocal() as session:
        try:
            # Trova l'ultimo InOut per la prenotazione
            latest_inout = session.query(InOut).filter(
                InOut.idReservation == reservation_id
            ).order_by(desc(InOut.id)).first()

            if not latest_inout:
                raise ValueError(f"No InOut records found for reservation {reservation_id}")
            
            # Ottieni gli ID delle pesate (weight1 e weight2)
            weight1_id = latest_inout.idWeight1
            weight2_id = latest_inout.idWeight2
            
            # Determina quale è l'ultima pesata basandosi sulla data
            last_weight = None
            last_weight_field = None
            if weight1_id and weight2_id:
                weight1 = session.query(Weighing).get(weight1_id)
                weight2 = session.query(Weighing).get(weight2_id)
                if weight2.date > weight1.date:
                    last_weight = weight2
                    last_weight_field = 'idWeight2'
                else:
                    last_weight = weight1
                    last_weight_field = 'idWeight1'
            elif weight1_id:
                last_weight = session.query(Weighing).get(weight1_id)
                last_weight_field = 'idWeight1'
            elif weight2_id:
                last_weight = session.query(Weighing).get(weight2_id)
                last_weight_field = 'idWeight2'
            else:
                raise ValueError("No weighings found for this InOut")

            # Salva i dati della pesata prima di rimuovere il riferimento
            deleted_weighing = {
                'id': last_weight.id,
                'weight': last_weight.weight,
                'date': last_weight.date,
                'pid': last_weight.pid,
                'weigher': last_weight.weigher
            }
            
            # Rimuovi il riferimento solo dall'ultimo InOut
            if last_weight_field == 'idWeight1':
                latest_inout.idWeight1 = None
            elif last_weight_field == 'idWeight2':
                latest_inout.idWeight2 = None

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
            return deleted_weighing

        except Exception as e:
            session.rollback()
            raise e