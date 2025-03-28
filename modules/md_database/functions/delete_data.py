from modules.md_database.md_database import table_models, SessionLocal

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

		# Funzione di supporto per serializzare oggetti
		def serialize_object(obj):
			if obj is None:
				return None
			
			# Gestione oggetti singoli
			if not hasattr(obj, '__table__'):
				return obj
			
			# Serializzazione base
			serialized = {}
			for column in obj.__table__.columns:
				serialized[column.name] = getattr(obj, column.name)
			
			return serialized
		
		# Preparazione del risultato
		result = {}
		
		# Serializzazione attributi base
		for column in model.__table__.columns:
			result[column.name] = getattr(record, column.name)
		
		# Serializzazione relazioni
		for rel_name, rel_obj in model.__mapper__.relationships.items():
			related_data = getattr(record, rel_name)
			
			if related_data is None:
				result[rel_name] = None
			elif hasattr(related_data, '__iter__') and not isinstance(related_data, str):
				# Gestione collection
				result[rel_name] = [
					serialize_object(item) for item in related_data
				]
			else:
				# Gestione oggetto singolo
				result[rel_name] = serialize_object(related_data)
		
		return result
	except Exception as e:
		session.rollback()
		session.close()
		raise e