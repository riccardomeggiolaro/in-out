from sqlalchemy import func
from sqlalchemy.orm import joinedload
from modules.md_database.md_database import SessionLocal, Weighing, Reservation, Vehicle

def get_reservation_by_plate_if_incomplete(plate: str):
    session = SessionLocal()
    try:
        # Crea una subquery che conta le pesate per ogni prenotazione
        weighing_count_subquery = (
            session.query(
                Weighing.idReservation,
                func.count(Weighing.id).label("weighing_count")
            )
            .group_by(Weighing.idReservation)
            .subquery()
        )
        
        # Trova la prenotazione tramite la targa e che soddisfa i criteri di pesate
        reservation = session.query(Reservation).options(
            joinedload(Reservation.subject),
            joinedload(Reservation.vector),
            joinedload(Reservation.driver),
            joinedload(Reservation.vehicle),
            joinedload(Reservation.material)
        ).join(
            Vehicle, Reservation.idVehicle == Vehicle.id
        ).outerjoin(  # Utilizziamo outerjoin per includere prenotazioni senza pesate
            weighing_count_subquery,
            Reservation.id == weighing_count_subquery.c.idReservation
        ).filter(
            Vehicle.plate == plate,
            Reservation.selected == False,  # Non già selezionata
            # Filtro per il numero di pesate: o nessuna pesata (NULL) o conteggio < number_weighings
            (
                (weighing_count_subquery.c.weighing_count == None) & (Reservation.number_weighings > 0) |
                (weighing_count_subquery.c.weighing_count < Reservation.number_weighings)
            )
        ).order_by(
            Reservation.date_created.desc()  # Ordina per data di creazione decrescente
        ).first()
        
        # Verifica che la prenotazione esista
        if not reservation:
            # raise ValueError(f"No reservation found with vehicle plate {plate} that has incomplete weighings")
            return None
        
        session.commit()
        
        # Esegui refresh per assicurarti che tutti gli attributi siano aggiornati
        session.refresh(reservation)
        return reservation
        
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()