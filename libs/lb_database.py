from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from typing import Optional, List
from pydantic import BaseModel, validator

# Connessione al database
Base = declarative_base()
cwd = os.getcwd()
engine = create_engine(f"sqlite:///{cwd}/database.db", echo=True)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

# Modello per la tabella User
class User(Base):
	__tablename__ = 'user'
	id = Column(Integer, primary_key=True, index=True)
	username = Column(String)
	password = Column(String)
	level = Column(Integer)
	description = Column(String)
	printer_name = Column(String, nullable=True)

class UserDTO(BaseModel):
	username: str
	password: str
	level: int
	description: str
	printer_name: Optional[str] = None
	
	@validator('username', pre=True, always=True)
	def check_username(cls, v):
		data = get_data_by_attribute('user', 'username', v)
		if data:
			raise ValueError('Username already exists')
		return v

	@validator('password', pre=True, always=True)
	def check_password(cls, v):
		if len(v) < 8:
			raise ValueError('Password must be at least 8 characters long')
		return v

	@validator('level', pre=True, always=True)
	def check_level(cls, v):
		if v not in [1, 2]:
			raise ValueError('Level must be 1 or 2')
		return v

class LoginDTO(BaseModel):
	username: str
	password: str

# Modello per la tabella Vehicle
class Vehicle(Base):
	__tablename__ = 'vehicle'
	id = Column(Integer, primary_key=True, index=True)
	plate = Column(String)
	name = Column(String)
	selected = Column(Boolean, default=False)

class ScheletonVehicleDTO(BaseModel):
	plate: Optional[str] = None
	name: Optional[str] = None
	id: Optional[int] = None

	class Config:
		# Configurazione per consentire l'uso di valori non dichiarati in fase di validazione
		arbitrary_types_allowed = True

class VehicleDTO(ScheletonVehicleDTO):
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

class VehicleDTOInit(ScheletonVehicleDTO):
	@validator('id', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in (None, -1):
			data = get_data_by_id('vehicle', v, False, False)
			if not data:
				raise ValueError('Id not exist in vehicle')
			else:
				values['plate'] = data.get('plate')
				values['name'] = data.get('name')
		return v

# Modello per la tabella SocialReason
class SocialReason(Base):
	__abstract__ = True  # Indica che questa tabella non sarà creata direttamente
	id = Column(Integer, primary_key=True, index=True)
	name = Column(String)
	cell = Column(Integer)
	cfpiva = Column(String)
	selected = Column(Boolean, default=False)

class Customer(SocialReason):
	__tablename__ = 'customer'

class Supplier(SocialReason):
	__tablename__ = 'supplier'

class SocialReasonDTO(BaseModel):
	name: Optional[str] = None
	cell: Optional[int] = None
	cfpiva: Optional[str] = None
	id: Optional[int] = None

	@validator('cell', pre=True, always=True)
	def check_cell(cls, v):
		if v not in (None, -1):
			if v < 0:
				raise ValueError("Cell must be greater than or equal to 0")
		return v

class CustomerDTO(SocialReasonDTO):
	@validator('id', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in (None, -1):
			data = get_data_by_id('customer', v, True, True)
			if not data:
				raise ValueError('Id not exist in customer')
			else:
				values['name'] = data.get('name')
				values['cell'] = data.get('cell')
				values['cfpiva'] = data.get('cfpiva')
		return v

class CustomerDTOInit(SocialReasonDTO):
	@validator('id', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in (None, -1):
			data = get_data_by_id('customer', v, False, False)
			if not data:
				raise ValueError('Id not exist in customer')
			else:
				values['name'] = data.get('name')
				values['cell'] = data.get('cell')
				values['cfpiva'] = data.get('cfpiva')
		return v

class SupplierDTO(SocialReasonDTO):
	@validator('id', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in (None, -1):
			data = get_data_by_id('supplier', v, True, True)
			if not data:
				raise ValueError('Id not exist in supplier')
			else:
				values['name'] = data.get('name')
				values['cell'] = data.get('cell')
				values['cfpiva'] = data.get('cfpiva')
		return v

class SupplierDTOInit(SocialReasonDTO):
	@validator('id', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in (None, -1):
			data = get_data_by_id('supplier', v, False, False)
			if not data:
				raise ValueError('Id not exist in supplier')
			else:
				values['name'] = data.get('name')
				values['cell'] = data.get('cell')
				values['cfpiva'] = data.get('cfpiva')
		return v

# Modello per la tabella Material
class Material(Base):
	__tablename__ = 'material'
	id = Column(Integer, primary_key=True, index=True) 
	name = Column(String, index=True)
	selected = Column(Boolean, index=True, default=False)

class ScheletonMaterialDTO(BaseModel):
	name: Optional[str] = None
	id: Optional[int] = None

class MaterialDTO(ScheletonMaterialDTO):
	@validator('id', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in [None, -1]:
			data = get_data_by_id('material', v, True, True)
			if not data:
				raise ValueError('Id not exist in material')
			else:
				values['name'] = data.get('name')
		return v

class MaterialDTOInit(ScheletonMaterialDTO):
	@validator('id', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in [None, -1]:
			data = get_data_by_id('material', v, False, False)
			if not data:
				raise ValueError('Id not exist in material')
			else:
				values['name'] = data.get('name')
		return v

# Modello per la tabella Weighing
class Weighing(Base):
	__tablename__ = 'weighing'
	id = Column(Integer, primary_key=True, index=True, nullable=False)
	plate = Column(String, nullable=True)
	vehicle = Column(String, nullable=True)
	customer = Column(String, nullable=True)  # Utilizzo di Enum
	customer_cell = Column(Integer, nullable=True)
	customer_cfpiva = Column(String, nullable=True)
	supplier = Column(String, nullable=True)
	supplier_cell = Column(Integer, nullable=True)
	supplier_cfpiva = Column(String, nullable=True)
	material = Column(String, nullable=True)
	note = Column(String, nullable=True)
	weight1 = Column(Integer, nullable=True)
	weight2 = Column(Integer, nullable=True)
	net_weight = Column(Integer, nullable=True)
	date1 = Column(DateTime, nullable=True)
	date2 = Column(DateTime, nullable=True)
	card_code = Column(String, nullable=True)
	card_number = Column(Integer, nullable=True)
	pid1 = Column(String, nullable=True)
	pid2 = Column(String, nullable=True)
	weigher = Column(String, nullable=True)
	selected = Column(Boolean, index=True, default=False, nullable=False)

# Dizionario di modelli per mappare nomi di tabella a classi di modelli
table_models = {
	'vehicle': Vehicle,
	'customer': Customer,
	'supplier': Supplier,
	'material': Material,
	'weighing': Weighing,
	'user': User
}

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
		session.close()

		return len(records)
	
	except Exception as e:
		session.rollback()  # Rollback in caso di errore
		session.close()
		raise e

def get_data_by_id(table_name, record_id, if_not_selected=False, set_selected=False):
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

		# Aggiunge una condizione alla query se if_is_selected è True
		if if_not_selected and record.selected:
			raise ValueError(f"Record con ID {record_id} già in uso nella tabella '{table_name}'.")

		# Imposta l'attributo 'selected' a True e salva la modifica
		if set_selected:
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

def get_data_by_attribute(table_name, attribute_name, attribute_value, if_not_selected=False, set_selected=False):
	"""Ottiene un record specifico da una tabella tramite un attributo e imposta 'selected' a True.

	Args:
		table_name (str): Il nome della tabella da cui ottenere il record.
		attribute_name (str): Il nome dell'attributo da usare per la ricerca.
		attribute_value (any): Il valore dell'attributo da cercare.
		if_not_selected (bool): Se True, solleva un errore se il record è già selezionato.
		set_selected (bool): Se True, imposta 'selected' a True prima di restituire il record.

	Returns:
		dict: Un dizionario con i dati del record aggiornato, o None se il record non è trovato.
	"""

	global SessionLocal

	# Verifica che il modello esista nel dizionario dei modelli
	model = table_models.get(table_name.lower())
	if not model:
		raise ValueError(f"Tabella '{table_name}' non trovata.")

	# Verifica che l'attributo esista nel modello
	if not hasattr(model, attribute_name):
		raise ValueError(f"Attributo '{attribute_name}' non trovato nella tabella '{table_name}'.")

	# Crea una sessione e cerca il record
	session = SessionLocal()
	try:
		# Recupera il record specifico in base all'attributo
		record = session.query(model).filter(getattr(model, attribute_name) == attribute_value).one_or_none()

		if record is None:
			raise ValueError(f"Record con {attribute_name} = {attribute_value} non trovato nella tabella '{table_name}'.")

		# Aggiunge una condizione alla query se if_not_selected è True
		if if_not_selected and record.selected:
			raise ValueError(f"Record con {attribute_name} = {attribute_value} già in uso nella tabella '{table_name}'.")

		# Imposta l'attributo 'selected' a True e salva la modifica
		if set_selected:
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
					if type(value) == str:
						query = query.filter(getattr(model, column).like(f'%{value}%'))
					elif type(value) == int:
						query = query.filter(getattr(model, column) == value)
					elif value == None:
						query = query.filter(getattr(model, column).is_(None))
					else:
						raise ValueError(f"Operatore di ricerca '{value[0]}' non supportato.")
				else:
					raise ValueError(f"Colonna '{column}' non trovata nella tabella '{table_name}'.")

		# Esegue la query e converte i risultati in una lista di dizionari
		results = query.all()

		session.close()

		result_list = [
			{column.name: getattr(record, column.name) for column in model.__table__.columns}
			for record in results
		]
		return result_list

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
		session.close()
	except Exception as e:
		session.rollback()
		session.close()
		raise e

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
		session.close()
	except Exception as e:
		session.rollback()
		session.close()
		raise e

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
		session.close()
	except Exception as e:
		session.rollback()
		session.close()
		raise e

def delete_all_data(table_name, if_not_selected=False):
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
		
		# Aggiunge la condizione per eliminare solo i record non selezionati, se richiesto
		if if_not_selected:
			query = query.filter_by(selected=False)
		
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
	"vehicle": {"plate": str, "name": str},
	"customer": {"name": str, "cell": int, "cfpiva": str},
	"supplier": {"name": str, "cell": int, "cfpiva": str},
	"material": {"name": str}
}

required_dtos = {
	"vehicle": VehicleDTO,
	"customer": CustomerDTO,
	"supplier": SupplierDTO,
	"material": MaterialDTO
}