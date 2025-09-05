from modules.md_database.md_database import table_models, SessionLocal, Access, Weighing
from sqlalchemy import func

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