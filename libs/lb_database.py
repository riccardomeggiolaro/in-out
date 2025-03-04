from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, BLOB, Float, ForeignKey, Enum
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
import os
from typing import Optional, List
from pydantic import BaseModel, validator
from applications.utils.utils_auth import hash_password
from libs.lb_printer import printer
from datetime import datetime

# Connessione al database
Base = declarative_base()
cwd = os.getcwd()
engine = create_engine(f"sqlite:///{cwd}/database.db", echo=True)
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
		if len(v) < 3:
			raise ValueError('Username must be at least 3 characters long')
		return v

	@validator('password', pre=True, always=True)
	def check_password(cls, v):
		if len(v) < 8:
			raise ValueError('Password must be at least 8 characters long')
		return hash_password(v)

	@validator('printer_name', pre=True, always=True)
	def check_printer_name(cls, v):
		if v is not None:
			if v in printer.get_list_printers_name():
				return v
			else:
				raise ValueError('Printer name is not configurated')
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
			data = get_data_by_id('vehicle', v)
			if not data:
				raise ValueError('Id not exist in vehicle')
			else:
				values['plate'] = data.get('plate')
				values['name'] = data.get('name')
		return v

class VehicleDTOInit(ScheletonVehicleDTO):
	pass

class SocialReason(Base):
	__tablename__ = 'social_reason'
	id = Column(Integer, primary_key=True, index=True)
	name = Column(String)
	cell = Column(Integer)
	cfpiva = Column(String)

class ScheletonSocialReasonDTO(BaseModel):
	name: Optional[str] = None
	cell: Optional[int] = None
	cfpiva: Optional[str] = None
	id: Optional[int] = None

	class Config:
		arbitrary_types_allowed = True

class SocialReasonDTO(ScheletonSocialReasonDTO):
	@validator('cell', pre=True, always=True)
	def check_cell(cls, v):
		if v not in (None, -1):
			if v < 0:
				raise ValueError("Cell must be greater than or equal to 0")
		return v

	@validator('id', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in (None, -1):
			data = get_data_by_id('customer', v)
			if not data:
				raise ValueError('Id not exist in customer')
			else:
				values['name'] = data.get('name')
				values['cell'] = data.get('cell')
				values['cfpiva'] = data.get('cfpiva')
		return v

class SocialReasonDTOInit(ScheletonSocialReasonDTO):
	pass

# Modello per la tabella Material
class Material(Base):
	__tablename__ = 'material'
	id = Column(Integer, primary_key=True, index=True) 
	name = Column(String, index=True)

class ScheletonMaterialDTO(BaseModel):
	name: Optional[str] = None
	id: Optional[int] = None

class MaterialDTO(ScheletonMaterialDTO):
	@validator('id', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in [None, -1]:
			data = get_data_by_id('material', v)
			if not data:
				raise ValueError('Id not exist in material')
			else:
				values['name'] = data.get('name')
		return v

class MaterialDTOInit(ScheletonMaterialDTO):
	pass

class Booking(Base):
    __tablename__ = 'booking'
    id = Column(Integer, primary_key=True, index=True)
    idSocialReason = Column(Integer, ForeignKey('social_reason.id'), nullable=False)
    idVehicle = Column(Integer, ForeignKey('vehicle.id'), nullable=False)
    idMaterial = Column(Integer, ForeignKey('material.id'), nullable=False)
    weighings = Column(Integer, default=0, nullable=False)
    date_created = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relazioni
    social_reason = relationship("SocialReason", back_populates="bookings")
    vehicle = relationship("Vehicle", back_populates="bookings")
    material = relationship("Material", back_populates="bookings")

# Aggiungere le relazioni inverse alle altre classi
SocialReason.bookings = relationship("Booking", back_populates="social_reason", cascade="all, delete")
Vehicle.bookings = relationship("Booking", back_populates="vehicle", cascade="all, delete")
Material.bookings = relationship("Booking", back_populates="material", cascade="all, delete")

class ScheletonBookingDTO(BaseModel):
    idSocialReason: Optional[int] = None
    idVehicle: Optional[int] = None
    idMaterial: Optional[int] = None
    weighings: Optional[int] = None
    id: Optional[int] = None
    
class BookingDTO(ScheletonBookingDTO):
	@validator('id', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in [None, -1]:
			data = get_data_by_id('booking', v)
			if not data:
				raise ValueError('Id not exist in booking')
		return v

	@validator('idSocialReason', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in [None, -1]:
			data = get_data_by_id('social_reason', v)
			if not data:
				raise ValueError('Id not exist in social reason')
		return v

	@validator('idVehicle', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in [None, -1]:
			data = get_data_by_id('vehicle', v)
			if not data:
				raise ValueError('Id not exist in vehicle')
		return v

	@validator('idMaterial', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in [None, -1]:
			data = get_data_by_id('idMaterial', v)
			if not data:
				raise ValueError('Id not exist in material')
		return v

	@validator('weighings', pre=True, always=True)
	def check_id(cls, v, values):
		if v <= 0:
			raise ValueError('Weighings must to be greater than 0')
		return v

class BookingDTOInit(ScheletonBookingDTO):
	pass

class ImageCaptured(Base):
	__tablename__ = 'image_captured'
	id = Column(Integer, primary_key=True, index=True)
	date = Column(DateTime, nullable=True)
	image = Column(BLOB, nullable=True)
	size = Column(Float, nullable=True)
	status = Column(String, nullable=True)

class ScheletonImageCapturedDTO(BaseModel):
	date: Optional[datetime] = None
	image: Optional[bytes] = None
	size: Optional[float] = None
	status: Optional[str] = None

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
	# Foreign Key references
	in_image_captured1_id = Column(Integer, ForeignKey('image_captured.id'), nullable=True)
	in_image_captured2_id = Column(Integer, ForeignKey('image_captured.id'), nullable=True)
	in_image_captured3_id = Column(Integer, ForeignKey('image_captured.id'), nullable=True)
	in_image_captured4_id = Column(Integer, ForeignKey('image_captured.id'), nullable=True)
	out_image_captured1_id = Column(Integer, ForeignKey('image_captured.id'), nullable=True)
	out_image_captured2_id = Column(Integer, ForeignKey('image_captured.id'), nullable=True)
	out_image_captured3_id = Column(Integer, ForeignKey('image_captured.id'), nullable=True)
	out_image_captured4_id = Column(Integer, ForeignKey('image_captured.id'), nullable=True)
	# Relationships for easy access to related images
	in_image_captured1 = relationship("ImageCaptured", foreign_keys=[in_image_captured1_id])
	in_image_captured2 = relationship("ImageCaptured", foreign_keys=[in_image_captured2_id])
	in_image_captured3 = relationship("ImageCaptured", foreign_keys=[in_image_captured3_id])
	in_image_captured4 = relationship("ImageCaptured", foreign_keys=[in_image_captured4_id])
	out_image_captured1 = relationship("ImageCaptured", foreign_keys=[out_image_captured1_id])
	out_image_captured2 = relationship("ImageCaptured", foreign_keys=[out_image_captured2_id])
	out_image_captured3 = relationship("ImageCaptured", foreign_keys=[out_image_captured3_id])
	out_image_captured4 = relationship("ImageCaptured", foreign_keys=[out_image_captured4_id])

# Dizionario di modelli per mappare nomi di tabella a classi di modelli
table_models = {
	'vehicle': Vehicle,
	'social_reason': SocialReason,
	'material': Material,
	'booking': Booking,
 	'weighing': Weighing,
	'user': User,
	'image_captured': ImageCaptured
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

def get_data_by_id(table_name, record_id):
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

		# Converte il record in un dizionario
		record_dict = {column.name: getattr(record, column.name) for column in model.__table__.columns}

		session.commit()
		session.close()

		return record_dict

	except Exception as e:
		session.rollback()  # Ripristina eventuali modifiche in caso di errore
		session.close()
		raise e

def get_data_by_id_if_is_selected(table_name, record_id):
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

def get_data_by_attribute(table_name, attribute_name, attribute_value):
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
		session.refresh(record)
		session.close()
		return record
	except Exception as e:
		session.rollback()
		session.close()
		raise e

def update_data(table_name, record_id, updated_data):
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

		# Aggiorna i campi con i nuovi valori
		for key, value in updated_data.items():
			if hasattr(record, key) and value is not None:  # Verifica che il campo esista
				setattr(record, key, value)

		session.commit()
		session.refresh(record)
		session.close()
		return record
	except Exception as e:
		session.rollback()
		session.close()
		raise e

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
	except Exception as e:
		session.rollback()
		session.close()
		raise e

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

required_columns = {
	"vehicle": {"plate": str, "name": str},
	"social_reason": {"name": str, "cell": int, "cfpiva": str},
	"material": {"name": str},
	"booking": {"idSocialReason": int, "idVehicle": int, "idMaterial": int, "weighings": int}
}

required_dtos = {
	"vehicle": VehicleDTO,
	"social_reason": SocialReasonDTO,
	"material": MaterialDTO,
	"booking": BookingDTO
}

Base.metadata.create_all(engine)