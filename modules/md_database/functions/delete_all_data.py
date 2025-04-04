from modules.md_database.md_database import table_models, SessionLocal

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