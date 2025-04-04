from modules.md_database.md_database import table_models, SessionLocal
from typing import List

# Funzione per caricare l'array di record nel database
def load_datas_into_db(table_name: str, records: List[object]):
	global SessionLocal

	# Verifica che il modello esista nel dizionario dei modelli
	model = table_models.get(table_name.lower())
	if not model:
		raise ValueError(f"Tabella '{table_name}' non trovata.")

	# Crea una sessione e cerca il record
	session = SessionLocal()

	try:
		# Crea un array di oggetti Record da inserire nel DB
		db_records = [model(**record) for record in records]

		# Aggiungi i record al DB
		session.add_all(db_records)
		
		# Esegui il commit delle modifiche
		session.commit()
		session.close()

		return len(records)
	
	except Exception as e:
		session.rollback()  # Rollback in caso di errore
		session.close()
		raise e