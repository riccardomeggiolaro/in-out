from sqlalchemy import func
from modules.md_database.md_database import table_models, SessionLocal, Weighing, Reservation

def get_reservations_with_incomplete_weighings():
	session = SessionLocal()
	try:
		# Subquery per contare il numero di pesate per ogni prenotazione
		weighing_count_subquery = (
			session.query(
				Weighing.idReservation,
				func.count(Weighing.id).label("actual_count")
			)
			.group_by(Weighing.idReservation)
			.subquery()
		)

		# Query principale per trovare prenotazioni con conteggio inferiore
		query = (
			session.query(Reservation)
			.outerjoin(
				weighing_count_subquery,
				Reservation.id == weighing_count_subquery.c.idReservation
			)
			.filter(
				# Caso 1: Nessuna pesata trovata (NULL nella subquery)
				(weighing_count_subquery.c.actual_count == None) & (Reservation.number_weighings > 0) |
				# Caso 2: Numero di pesate inferiore al previsto
				(weighing_count_subquery.c.actual_count < Reservation.number_weighings)
			)
		)

		return query.all()
	finally:
		session.close()