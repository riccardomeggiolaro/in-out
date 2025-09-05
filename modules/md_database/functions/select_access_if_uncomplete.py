from sqlalchemy import func
from modules.md_database.md_database import SessionLocal, InOut, Access

def select_access_if_uncomplete(access_id: int):
	session = SessionLocal()
	try:
		# Trova la prenotazione per id
		access = session.query(Access).filter(Access.id == access_id).first()
		
		# Verifica che la prenotazione esista
		if not access:
			raise ValueError(f"Access with ID {access_id} not found")
		
		# Conta le pesate correlate a questa prenotazione
		weighing_count = session.query(func.count(InOut.id)).filter(
			InOut.idAccess == access_id
		).scalar()

		if weighing_count == access.number_in_out and access.in_out[-1].idWeight2:
			# Numero di pesate uguale o superiore al previsto, genera errore
			raise ValueError(f"Access {access_id} already is just closed")

		elif access.selected == True:
			raise ValueError(f"Access with ID {access_id} is already in use by another weigher")

		# Imposta selected a True
		access.selected = True
		session.commit()
		return access
            
	except Exception as e:
		session.rollback()
		raise e
	finally:
		session.close()