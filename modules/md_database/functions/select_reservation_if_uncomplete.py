from sqlalchemy import func
from modules.md_database.md_database import table_models, SessionLocal, Weighing, Reservation

def select_reservation_if_uncomplete(reservation_id: int):
	session = SessionLocal()
	try:
		# Trova la prenotazione per id
		reservation = session.query(Reservation).filter(Reservation.id == reservation_id).first()
		
		# Verifica che la prenotazione esista
		if not reservation:
			raise ValueError(f"Reservation with ID {reservation_id} not found")
		
		# Conta le pesate correlate a questa prenotazione
		weighing_count = session.query(func.count(Weighing.id)).filter(
			Weighing.idReservation == reservation_id
		).scalar()

		# Verifica se il numero di pesate è inferiore al campo number_weighings
		if weighing_count < reservation.number_weighings:
			# Verifica che la prenotazione non sia già in uso da un'altra pesa
			if reservation.selected == True:
				raise ValueError(f"Reservation with ID {reservation_id} is already in use by another weigher")
			# Imposta selected a True
			reservation.selected = True
			session.commit()
			return reservation
		else:
			# Numero di pesate uguale o superiore al previsto, genera errore
			raise ValueError(f"Reservation {reservation_id} already is just closed "
						    f"({weighing_count}/{reservation.number_weighings})")
            
	except Exception as e:
		session.rollback()
		raise e
	finally:
		session.close()

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
            joinedload(Reservation.vehicle),
            joinedload(Reservation.social_reason),
            joinedload(Reservation.vector),
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
            raise ValueError(f"No reservation found with vehicle plate {plate} "
                           f"that has incomplete weighings")
        
        session.commit()
        
        # Esegui refresh per assicurarti che tutti gli attributi siano aggiornati
        session.refresh(reservation)
        return reservation
        
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()