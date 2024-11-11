from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from typing import Optional, List
from pydantic import BaseModel, validator

# Connessione al database
Base = declarative_base()
SessionLocal = None

# Modello per la tabella Vehicle
class Vehicle(Base):
	__tablename__ = 'vehicle'
	id = Column(Integer, primary_key=True, index=True)
	plate = Column(String)
	name = Column(String)
	selected = Column(Boolean, default=False)

class VehicleDTO(BaseModel):
	plate: Optional[str] = None
	name: Optional[str] = None
	id: Optional[int] = None

	@validator('id', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in (None, -1):
			data = get_data_by_id('vehicle', v, True, True)
			if not data:
				raise ValueError('Id not exist in vehicle')
			else:
				values['plate'] = data.get('plate')
				values['name'] = data.get('name')
		return v

	class Config:
		# Configurazione per consentire l'uso di valori non dichiarati in fase di validazione
		arbitrary_types_allowed = True

# Modello per la tabella SocialReason
class SocialReason(Base):
	__tablename__ = 'social_reason'
	id = Column(Integer, primary_key=True, index=True)
	name = Column(String)
	cell = Column(Integer)
	cfpiva = Column(String)
	selected = Column(Boolean, default=False)

class SocialReasonDTO(BaseModel):
	name: Optional[str] = None
	cell: Optional[int] = None
	cfpiva: Optional[str] = None
	id: Optional[int] = None

	@validator('id', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in (None, -1):
			data = get_data_by_id('social_reason', v, True)
			if not data:
				raise ValueError('Id not exist in social reason')
			else:
				values['name'] = data.get('name')
				values['cell'] = data.get('cell')
				values['cfpiva'] = data.get('cfpiva')
		return v

	@validator('cell', pre=True, always=True)
	def check_cell(cls, v):
		if v not in (None, -1):
			if v < 0:
				raise ValueError("Cell must be greater than or equal to 0")
		return v

# Modello per la tabella Material
class Material(Base):
	__tablename__ = 'material'
	id = Column(Integer, primary_key=True, index=True) 
	name = Column(String, index=True)
	selected = Column(Boolean, index=True, default=False)

class MaterialDTO(BaseModel):
	name: Optional[str] = None
	id: Optional[int] = None

	@validator('id', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in [None, -1]:
			data = get_data_by_id('material', v, True)
			if not data:
				raise ValueError('Id not exist in material')
			else:
				values['name'] = data.get('name')
		return v

# Modello per la tabella Weighing
class Weighing(Base):
	__tablename__ = 'weighing'
	id = Column(Integer, primary_key=True, index=True)
	plate = Column(String)
	vehicle = Column(String)
	customer = Column(String)  # Utilizzo di Enum
	customer_cell = Column(Integer)
	customer_cfpiva = Column(String)
	supplier = Column(String)
	supplier_cell = Column(Integer)
	supplier_cfpiva = Column(String)
	material = Column(String)
	weight1 = Column(Integer)
	weight2 = Column(Integer)
	net_weight = Column(Integer)
	date = Column(DateTime, default=func.now())
	card_code = Column(String)
	card_number = Column(Integer)

# Dizionario di modelli per mappare nomi di tabella a classi di modelli
table_models = {
	'vehicle': Vehicle,
	'social_reason': SocialReason,
	'material': Material,
	'weighing': Weighing,
}

def init():
	global SessionLocal

	engine = create_engine(f'sqlite:///{os.getcwd()}/database.db', echo=True)
	SessionLocal = sessionmaker(bind=engine)
	# Creazione delle tabelle
	Base.metadata.create_all(engine)

# Funzione per caricare l'array di record nel database
def load_records_into_db(table_name: str, records: List[object]):
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

		return len(records)
	
	except Exception as e:
		raise e
		session.rollback()  # Rollback in caso di errore

	finally:
		# Chiusura della sessione
		session.close()

def get_data_by_id(table_name, record_id, if_not_selected=False, set_selected=False):
	"""Ottiene un record specifico da una tabella tramite l'ID e imposta 'selected' a True.

	Args:
		table_name (str): Il nome della tabella da cui ottenere il record.
		record_id (int): L'ID del record da ottenere.

	Returns:
		dict: Un dizionario con i dati del record aggiornato, o None se il record non è trovato.
	"""

	global SessionLocal

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

		# Aggiunge una condizione alla query se if_is_selected è True
		if if_not_selected and record.selected:
			raise ValueError(f"Record con ID {record_id} già in uso nella tabella '{table_name}'.")

		# Imposta l'attributo 'selected' a True e salva la modifica
		if set_selected:
			record.selected = True
		session.commit()

		# Converte il record in un dizionario
		record_dict = {column.name: getattr(record, column.name) for column in model.__table__.columns}
		return record_dict

	except Exception as e:
		raise e
		session.rollback()  # Ripristina eventuali modifiche in caso di errore
	finally:
		session.close()

def filter_data(table_name, filters=None):
	"""Esegue una ricerca filtrata su una tabella specifica e restituisce una lista di risultati.

	Args:
		table_name (str): Il nome della tabella su cui eseguire la ricerca.
		filters (dict): Dizionario di filtri (nome_colonna: valore) per la ricerca. Default è None.

	Returns:
		list: Lista di dizionari contenenti i risultati della ricerca, o lista vuota se nessun risultato.
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
		
		# Aggiunge i filtri, se specificati
		if filters:
			for column, value in filters.items():
				if hasattr(model, column):
					if value[0] == "==":
						query = query.filter(getattr(model, column) == value[1])
					elif value[0] == ">":
						query = query.filter(getattr(model, column) > value[1])
					elif value[0] == ">=":
						query = query.filter(getattr(model, column) >= value[1])
					elif value[0] == "<":
						query = query.filter(getattr(model, column) < value[1])
					elif value[0] == "<=":
						query = query.filter(getattr(model, column) <= value[1])
					elif value[0] == "like":
						query = query.filter(getattr(model, column).like(f'%{value[1]}%'))
					else:
						raise ValueError(f"Operatore di ricerca '{value[0]}' non supportato.")
				else:
					raise ValueError(f"Colonna '{column}' non trovata nella tabella '{table_name}'.")

		# Esegue la query e converte i risultati in una lista di dizionari
		results = query.all()
		result_list = [
			{column.name: getattr(record, column.name) for column in model.__table__.columns}
			for record in results
		]
		return result_list

	except Exception as e:
		raise e
	finally:
		session.close()

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
	except Exception as e:
		raise e
		session.rollback()
	finally:
		session.close()

def update_data(table_name, record_id, updated_data, if_not_selected=False):
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

		# Aggiunge una condizione alla query se if_is_selected è True
		if if_not_selected and record.selected:
			raise ValueError(f"Record con ID {record_id} è in uso nella tabella '{table_name}'.")

		# Aggiorna i campi con i nuovi valori
		for key, value in updated_data.items():
			if hasattr(record, key) and value is not None:  # Verifica che il campo esista
				setattr(record, key, value)

		session.commit()
	except Exception as e:
		raise e
		session.rollback()
	finally:
		session.close()

def delete_data(table_name, record_id, if_not_selected=False):
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

		if if_not_selected and record.selected:
			raise ValueError(f"Record con ID {record_id} è in uso nella tabella '{table_name}'.")

		# Elimina il record
		session.delete(record)
		session.commit()
	except Exception as e:
		raise e
		session.rollback()
	finally:
		session.close()

required_columns = {
	"vehicle": {"plate": str, "name": str},
	"social_reason": {"name": str, "cell": int, "cfpiva": str},
	"material": {"name": str}
}

required_dtos = {
	"vehicle": VehicleDTO,
	"social_reason": SocialReasonDTO,
	"material": MaterialDTO
}