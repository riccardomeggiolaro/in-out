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

def filter_data(table_name, filters=None, limit=None, offset=None):
	"""Esegue una ricerca filtrata su una tabella specifica con supporto per la paginazione
	e popola automaticamente le colonne di riferimenti con i dati delle tabelle correlate,
	incluse tutte le relazioni annidate.
	
	Args:
		table_name (str): Il nome della tabella su cui eseguire la ricerca.
		filters (dict): Dizionario di filtri (nome_colonna: valore) per la ricerca. Default è None.
		limit (int): Numero massimo di righe da visualizzare. Default è None.
		offset (int): Numero di righe da saltare. Default è None.
		
	Returns:
		tuple: Una tupla contenente:
			- una lista di dizionari contenenti i risultati della ricerca,
			- il numero totale di righe nella tabella.
	"""
	# Verifica che il modello esista nel dizionario dei modelli
	model = table_models.get(table_name.lower())
	if not model:
		raise ValueError(f"Tabella '{table_name}' non trovata.")
	
	# Crea una sessione e costruisce la query
	session = SessionLocal()
	try:
		# Inizia la query sulla tabella specificata
		query = session.query(model)
		
		# Carica tutte le relazioni dirette della tabella principale
		for rel_name, rel_obj in model.__mapper__.relationships.items():
			# Carica la relazione diretta e tutte le relazioni annidate
			query = query.options(selectinload(getattr(model, rel_name)).selectinload('*'))
		
		# Aggiungi i filtri, se specificati
		if filters:
			for column, value in filters.items():
				if hasattr(model, column):
					if type(value) == str:
						query = query.filter(getattr(model, column).like(f'%{value}%'))
					elif type(value) == int:
						query = query.filter(getattr(model, column) == value)
					elif value is None:
						query = query.filter(getattr(model, column).is_(None))
					else:
						raise ValueError(f"Operatore di ricerca '{value[0]}' non supportato.")
				else:
					raise ValueError(f"Colonna '{column}' non trovata nella tabella '{table_name}'.")
		
		# Esegui una query separata per ottenere il numero totale di righe
		total_rows = query.count()
		
		# Applica la paginazione se limit e offset sono specificati
		if limit is not None:
			query = query.limit(limit)
		if offset is not None:
			query = query.offset(offset)
		
		# Esegui la query per ottenere i risultati filtrati
		results = query.all()
		
		session.close()
		return results, total_rows
	
	except Exception as e:
		session.close()
		raise e

def add_data(table_name, data):
	"""Aggiunge un record a una tabella specificata dinamicamente.

	Args:
		table_name (str): Il nome della tabella in cui aggiungere i dati.
		data (dict): Un dizionario dei dati da inserire nella tabella.
	"""

	global SessionLocal

	# Verifica che il modello esista nel dizionario dei modelli
	model = table_models.get(table_name.lower())
	if not model:
		raise ValueError(f"Tabella '{table_name}' non trovata.")

	# Crea una sessione e aggiungi i dati
	session = SessionLocal()
	try:
		# Crea una nuova istanza del modello con i dati forniti
		record = model(**data)
		session.add(record)
		session.commit()
		session.refresh(record)
		session.close()
		return record
	except Exception as e:
		session.rollback()
		session.close()
		raise e

def update_data(table_name, record_id, updated_data):
	"""Aggiorna un record specifico in una tabella.

	Args:
		table_name (str): Il nome della tabella in cui aggiornare i dati.
		record_id (int): L'ID del record da aggiornare.
		updated_data (dict): Un dizionario dei nuovi valori per i campi da aggiornare.
		if_is_selected (bool): Se True, aggiunge una condizione addizionale alla query.
	"""
	# Verifica che il modello esista nel dizionario dei modelli
	model = table_models.get(table_name.lower())
	if not model:
		raise ValueError(f"Tabella '{table_name}' non trovata.")

	# Crea una sessione e aggiorna i dati
	session = SessionLocal()
	try:
		# Recupera il record specifico in base all'ID
		record = session.query(model).filter_by(id=record_id).one_or_none()

		if record is None:
			raise ValueError(f"Record con ID {record_id} non trovato nella tabella '{table_name}'.")

		# Aggiorna i campi con i nuovi valori
		for key, value in updated_data.items():
			if hasattr(record, key) and value is not None:  # Verifica che il campo esista
				if "id" in key and value == -1:
					value = None
				setattr(record, key, value)

		session.commit()
		session.refresh(record)
		session.close()
		return record
	except Exception as e:
		session.rollback()
		session.close()
		raise e

def delete_data(table_name, record_id):
	"""Elimina un record specifico da una tabella.

	Args:
		table_name (str): Il nome della tabella da cui eliminare il record.
		record_id (int): L'ID del record da eliminare.
		if_is_selected (bool): Se True, aggiunge una condizione addizionale alla query.
	"""
	# Verifica che il modello esista nel dizionario dei modelli
	model = table_models.get(table_name.lower())
	if not model:
		raise ValueError(f"Tabella '{table_name}' non trovata.")

	# Crea una sessione e elimina il record
	session = SessionLocal()
	try:
		# Costruisce la query di ricerca del record
		record = session.query(model).filter_by(id=record_id).one_or_none()

		if record is None:
			raise ValueError(f"Record con ID {record_id} non trovato nella tabella '{table_name}'.")

		# Elimina il record
		session.delete(record)
		session.commit()
		session.close()
	except Exception as e:
		session.rollback()
		session.close()
		raise e

def delete_all_data(table_name):
	"""Elimina tutti i record da una tabella, con un'opzione per escludere quelli selezionati.

	Args:
		table_name (str): Il nome della tabella da cui eliminare i record.
		if_not_selected (bool): Se True, elimina solo i record non selezionati.
	"""
	# Verifica che il modello esista nel dizionario dei modelli
	model = table_models.get(table_name.lower())
	if not model:
		raise ValueError(f"Tabella '{table_name}' non trovata.")

	# Crea una sessione e verifica i record
	session = SessionLocal()

	try:
		# Verifica che non ci siano record con selected=True
		if session.query(model).filter_by(selected=True).count() > 0:
			raise ValueError("Non è possibile eliminare i record: ci sono record attualmente in uso.")

		# Costruisce la query per selezionare i record da eliminare
		query = session.query(model)
		
		# Elimina tutti i record trovati in una sola operazione
		deleted_count = query.delete(synchronize_session=False)
		
		# Conferma le modifiche nel database
		session.commit()
		session.close()

		return deleted_count  # Restituisce il numero di record eliminati per informazione
		
	except Exception as e:
		session.rollback()
		session.close()
		raise e

required_columns = {
	"vehicle": {"name": str, "plate": str},
	"social_reason": {"name": str, "cell": str, "cfpiva": str},
	"vector": {"name": str, "cell": str, "cfpiva": str},
	"material": {"name": str},
	"weighing": {"weight": float, "date": datetime, "pid": str, "weigher": str},
	"reservation": {"typeSocialReason": int, "idSocialReason": int, "idVector": int, "idVehicle": int, "idMaterial": int, "number_weighings": int, "note": str}
}

#######################################################################
# Funzione specifiche perché contenenti parametri complessi
#######################################################################

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