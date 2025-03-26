from sqlalchemy.orm import selectinload
from modules.md_database.md_database import table_models, SessionLocal

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