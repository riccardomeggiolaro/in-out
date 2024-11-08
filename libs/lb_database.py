from sqlalchemy import create_engine, Column, Integer, String, DateTime, Enum as SQLAlchemyEnum, func, CheckConstraint, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import NoResultFound
import os
from enum import Enum
from typing import Optional
from pydantic import BaseModel, validator

# Connessione al database
Base = declarative_base()
SessionLocal = None

# Modello per la tabella Vehicle
class Vehicle(Base):
	__tablename__ = 'vehicle'
	id = Column(Integer, primary_key=True, index=True)
	plate = Column(String, index=True)
	name = Column(String, index=True)
	selected = Column(Boolean, index=True)

class VehicleDTO(BaseModel):
	id: Optional[int] = None
	plate: Optional[str] = None
	name: Optional[str] = None

	@validator('id', pre=True, always=True)
	def check_id(cls, v):
		if v not in (None, -1):
			data = get_data_by_id('vehicle', v, True)
			if not data:
				raise ValueError('Id not exist in vehicle')
			else:
				plate = data.get('plate')
				name = data.get('name')
		return v

# Modello per la tabella SocialReason
class SocialReason(Base):
	__tablename__ = 'social_reason'
	id = Column(Integer, primary_key=True, index=True)
	name = Column(String, index=True)
	cell = Column(Integer, index=True)
	cfpiva = Column(String, index=True)
	selected = Column(Boolean, index=True)

class SocialReasonDTO(BaseModel):
	id: Optional[int] = None
	name: Optional[str] = None
	cell: Optional[int] = None
	cfpiva: Optional[str] = None

	@validator('id', pre=True, always=True)
	def check_id(cls, v):
		if v not in (None, -1):
			data = get_data_by_id('social_reason', v, True)
			if not data:
				raise ValueError('Id not exist in social reason')
			else:
				name = data.get('name')
				cell = data.get('cell')
				cfpiva = data.get('cfpiva')
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
	selected = Column(Boolean, index=True)

class MaterialDTO(BaseModel):
	id: Optional[int] = None
	name: Optional[str] = None

	@validator('id', pre=True, always=True)
	def check_id(cls, v):
		if v not in (None, -1):
			data = get_data_by_id('material', v, True)
			if not data:
				raise ValueError('Id not exist in material')
			else:
				name = data.get('name')
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

def get_data_by_id(table_name, record_id, set_selected=False):
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
			print(f"Record con ID {record_id} non trovato nella tabella '{table_name}'.")
			return None

		# Imposta l'attributo 'selected' a True e salva la modifica
		if set_selected:
			record.selected = True
		session.commit()

		# Converte il record in un dizionario
		record_dict = {column.name: getattr(record, column.name) for column in model.__table__.columns}
		return record_dict

	except Exception as e:
		print(f"Errore durante il recupero e l'aggiornamento del record: {e}")
		session.rollback()  # Ripristina eventuali modifiche in caso di errore
		return None
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
						print(f"Operatore di ricerca '{value[0]}' non supportato.")
				else:
					print(f"Colonna '{column}' non trovata nella tabella '{table_name}'.")

		# Esegue la query e converte i risultati in una lista di dizionari
		results = query.all()
		result_list = [
			{column.name: getattr(record, column.name) for column in model.__table__.columns}
			for record in results
		]
		return result_list

	except Exception as e:
		print(f"Errore durante la ricerca filtrata: {e}")
		return []
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
		lb_log.error(f"Errore durante l'aggiunta del record: {e}")
		session.rollback()
	finally:
		session.close()

def update_data(table_name, record_id, updated_data):
	"""Aggiorna un record specifico in una tabella.

	Args:
		table_name (str): Il nome della tabella in cui aggiornare i dati.
		record_id (int): L'ID del record da aggiornare.
		updated_data (dict): Un dizionario dei nuovi valori per i campi da aggiornare.
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
			print(f"Record con ID {record_id} non trovato nella tabella '{table_name}'.")
			return
		
		# Aggiorna i campi con i nuovi valori
		for key, value in updated_data.items():
			if hasattr(record, key):  # Verifica che il campo esista
				setattr(record, key, value)
			else:
				print(f"Campo '{key}' non trovato nella tabella '{table_name}' e sarà ignorato.")

		session.commit()
		print(f"Record con ID {record_id} aggiornato con successo nella tabella '{table_name}'.")
	except Exception as e:
		session.rollback()
		print(f"Errore durante l'aggiornamento del record: {e}")
	finally:
		session.close()

def delete_data(table_name, record_id):
	"""Elimina un record specifico da una tabella.

	Args:
		table_name (str): Il nome della tabella da cui eliminare il record.
		record_id (int): L'ID del record da eliminare.
	"""
	# Verifica che il modello esista nel dizionario dei modelli
	model = table_models.get(table_name.lower())
	if not model:
		raise ValueError(f"Tabella '{table_name}' non trovata.")

	# Crea una sessione e elimina il record
	session = SessionLocal()
	try:
		# Recupera il record specifico in base all'ID
		record = session.query(model).filter_by(id=record_id).one_or_none()
		if record is None:
			print(f"Record con ID {record_id} non trovato nella tabella '{table_name}'.")
			return

		# Elimina il record
		session.delete(record)
		session.commit()
		print(f"Record con ID {record_id} eliminato con successo dalla tabella '{table_name}'.")
	except Exception as e:
		session.rollback()
		print(f"Errore durante l'eliminazione del record: {e}")
	finally:
		session.close()