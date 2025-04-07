from datetime import datetime
from modules.md_database.md_database import table_models, SessionLocal

def get_data_by_attributes(table_name, attributes_dict):
	"""Ottiene un record specifico da una tabella tramite più attributi.
	La ricerca non è case sensitive per valori di tipo stringa.
	
	Args:
		table_name (str): Il nome della tabella da cui ottenere il record.
		attributes_dict (dict): Un dizionario di attributi e valori da usare per la ricerca.
		
	Returns:
		dict: Un dizionario con i dati del record, o None se il record non è trovato.
	"""
	
	# Verifica che il modello esista nel dizionario dei modelli
	model = table_models.get(table_name.lower())
	if not model:
		raise ValueError(f"Tabella '{table_name}' non trovata.")
	
	# Verifica che tutti gli attributi esistano nel modello
	for attribute_name in attributes_dict.keys():
		if not hasattr(model, attribute_name):
			raise ValueError(f"Attributo '{attribute_name}' non trovato nella tabella '{table_name}'.")
	
	# Crea una sessione e cerca il record
	session = SessionLocal()
	try:
		# Costruisce la query con tutti gli attributi forniti
		query = session.query(model)
		for attribute_name, attribute_value in attributes_dict.items():
			# Usa func.lower() per rendere la ricerca case insensitive se il valore è una stringa
			if isinstance(attribute_value, str):
				from sqlalchemy import func
				query = query.filter(func.lower(getattr(model, attribute_name)) == attribute_value.lower())
			else:
				query = query.filter(getattr(model, attribute_name) == attribute_value)
		
		# Esegue la query
		record = query.first()
		record_dict = None
		
		if record:
			# Converte il record in un dizionario
			record_dict = {column.name: getattr(record, column.name) for column in model.__table__.columns}
		
		session.commit()
		session.close()
		return record_dict
	
	except Exception as e:
		session.rollback()  # Ripristina eventuali modifiche in caso di errore
		session.close()
		raise e

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
		
def select_reservation_if_incomplete(reservation_id: int):
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