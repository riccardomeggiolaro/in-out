from modules.md_database.md_database import table_models, SessionLocal

def get_data_by_id_if_not_selected(table_name, record_id):
	"""Ottiene un record specifico da una tabella tramite l'ID e imposta 'selected' a True.

	Args:
		table_name (str): Il nome della tabella da cui ottenere il record.
		record_id (int): L'ID del record da ottenere.

	Returns:
		dict: Un dizionario con i dati del record aggiornato, o None se il record non è trovato.
	"""

	# Verifica che il modello esista nel dizionario dei modelli
	model = table_models.get(table_name.lower())
	if not model:
		raise ValueError(f"Tabella '{table_name}' non trovata.")

	# Crea una sessione e cerca il record
	session = SessionLocal()
	try:
		# Recupera il record specifico in base all'ID
		record = session.query(model).filter_by(id=record_id).one_or_none()

		if record is None:
			raise ValueError(f"Record con ID {record_id} non trovato nella tabella '{table_name}'.")

		if record.selected is True:
			raise ValueError(f"Record con ID {record_id} nella tabella '{table_name}' è in uso.")

		record.selected = True

		# Converte il record in un dizionario
		record_dict = {column.name: getattr(record, column.name) for column in model.__table__.columns}

		session.commit()
		session.close()

		return record_dict

	except Exception as e:
		session.rollback()  # Ripristina eventuali modifiche in caso di errore
		session.close()
		raise e