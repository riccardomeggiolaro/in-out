from sqlalchemy import func
from modules.md_database.md_database import SessionLocal, InOut, Reservation

def select_reservation_if_uncomplete(reservation_id: int):
	session = SessionLocal()
	try:
		# Trova la prenotazione per id
		reservation = session.query(Reservation).filter(Reservation.id == reservation_id).first()
		
		# Verifica che la prenotazione esista
		if not reservation:
			raise ValueError(f"Reservation with ID {reservation_id} not found")
		
		# Conta le pesate correlate a questa prenotazione
		weighing_count = session.query(func.count(InOut.id)).filter(
			InOut.idReservation == reservation_id
		).scalar()

		if weighing_count == reservation.number_weighings and reservation.in_out[-1].idWeight2:
			# Numero di pesate uguale o superiore al previsto, genera errore
			raise ValueError(f"Reservation {reservation_id} already is just closed")

		elif reservation.selected == True:
			raise ValueError(f"Reservation with ID {reservation_id} is already in use by another weigher")

		# Imposta selected a True
		reservation.selected = True
		session.commit()
		return reservation
            
	except Exception as e:
		session.rollback()
		raise e
	finally:
		session.close()