from libs.lb_utils import CustomBaseModel
from libs.lb_system import SerialPort, Tcp, Connection, SerialPortWithoutControls, TcpWithoutControls
from typing import Optional, Union, List
from pydantic import BaseModel, validator
from libs.lb_database import VehicleDTOInit, CustomerDTOInit, SupplierDTOInit, MaterialDTOInit
from libs.lb_database import update_data
from datetime import datetime

class DataInExecution(BaseModel):
	customer: CustomerDTOInit = CustomerDTOInit(**{})
	supplier: SupplierDTOInit = SupplierDTOInit(**{})
	vehicle: VehicleDTOInit = VehicleDTOInit(**{})
	material: MaterialDTOInit = MaterialDTOInit(**{})
	note: Union[str, None] = None

	def setAttribute(self, source):
		# Per ogni chiave dei nuovi dati passati controlla se è un oggetto o None
		for key, value in vars(source).items():

			if isinstance(value, str):
				if value in ["", "undefined", -1]:
					value = None
				setattr(self, key, value)
			elif isinstance(value, object) and value is not None:

				current_attr = getattr(self, key)
				current_id = getattr(current_attr, 'id')
				source_value_id = getattr(value, 'id')
				# Verifica se `source` ha qualsiasi altro attributo diverso da `id`
				other_source_values = any(sub_key != 'id' for sub_key in vars(source).keys())

				# Preparazione dei dati correnti prima di aggiungere le modifiche
				# Serve per gestire il cambio di selected sul database nel caso fosse in uso una anagrafica del database
				# Se l'id corrente è un numero
				if isinstance(current_id, int):
					# Controlla se é stato passato un nuovo id e se oltre a quello sono stati passati altri valori
					if source_value_id is None and other_source_values:
						# Se ci sono altri attributi, resetta tutti gli attributi correnti a None
						for sub_key, sub_value in vars(current_attr).items():
							setattr(current_attr, sub_key, None)
					# Setta l'id corrente nel database a selected False siccome è stato cambiato passando l'id, o altri attributi o entrambi
					update_data(key, current_id, {"selected": False})

				# Modifica dei valori
				for sub_key, sub_value in vars(value).items():
					if sub_value is not None or current_id is not None:
						# Se il valore è un tipo primitivo, aggiorna il nuovo valore
						if sub_value in ["", "undefined", -1]:
							sub_value = None
						setattr(current_attr, sub_key, sub_value)

	def deleteAttribute(self):
		# Per ogni chiave dei dati correnti
		for key, attr in vars(self).items():
			if isinstance(attr, str):
				setattr(self, key, None)
			elif isinstance(attr, object):
				if hasattr(attr, 'id'):
					# Ottiene l'id corrente dell'oggetto inerente alla chiave
					current_attr_id = getattr(attr, 'id')
					# Se l'id corrente non é None allora setta selected False dell'id sul database
					if current_attr_id is not None:
						update_data(key, current_attr_id, {"selected": False})
				if hasattr(attr, '__dict__'):
					# Resetta tutti gli attributi dell'oggetto corrente a None
					for sub_key, sub_value in attr.__dict__.items():
						setattr(attr, sub_key, None)

class IdSelected(BaseModel):
	id: Optional[int] = None

	def setAttribute(self, new_id):
		if new_id is not None:
			if new_id == -1:
				new_id = None
			if hasattr(self, 'id') and getattr(self, 'id') is not None:
				current_id = getattr(self, 'id')
				update_data('weighing', current_id, {"selected": False})
			setattr(self, 'id', new_id)
	
	def deleteAttribute(self):
		if hasattr(self, 'id') and getattr(self, 'id') is not None:
			current_id = getattr(self, 'id')
			update_data('weighing', current_id, {"selected": False})
		setattr(self, 'id', None)

class Data(BaseModel):
	data_in_execution: DataInExecution
	id_selected: IdSelected

class PlateWeighing(BaseModel):
	plate: str

class Realtime(BaseModel):
	status: str
	type: str
	net_weight: str 
	gross_weight: str
	tare: str
	unite_measure: str
	
class Diagnostic(CustomBaseModel):
	status: int
	firmware: str
	model_name: str
	serial_number: str
	vl: str
	rz: str

class Cam(BaseModel):
	camera_url: str
	username: str
	password: str

class WeightExecuted(BaseModel):
	net_weight: str
	gross_weight: str
	tare: str
	unite_misure: str
	pid: str
	bil: str
	status: str
	executed: bool

class ImageCaptured(BaseModel):
    date: Optional[datetime] = None
    image: Optional[bytes] = None
    size: Optional[float] = None
    status: Optional[str] = None

class Weight(BaseModel):
	weight_executed: WeightExecuted
	data_assigned: Optional[DataInExecution] = None
	image1: Optional[ImageCaptured] = None
	image2: Optional[ImageCaptured] = None
	image3: Optional[ImageCaptured]	= None
	image4: Optional[ImageCaptured]	= None

class SetupWeigher(CustomBaseModel):
	max_weight: int
	min_weight: int
	division: int
	maintaine_session_realtime_after_command: bool
	diagnostic_has_priority_than_realtime: bool
	always_execute_realtime_in_undeground: bool
	node: Optional[str] = None
	terminal: str
	run: bool
	data: Data
	name: str
	cam1: Optional[Cam] = None
	cam2: Optional[Cam] = None
	cam3: Optional[Cam] = None
	cam4: Optional[Cam] = None

class Configuration(CustomBaseModel):
	nodes: Optional[List[SetupWeigher]] = []
	connection: Optional[Union[SerialPort, Tcp, Connection]] = Connection(**{})
	time_between_actions: Union[int, float]
 
class ConfigurationWithoutControls(CustomBaseModel):
	nodes: Optional[List[SetupWeigher]] = []
	connection: Optional[Union[SerialPortWithoutControls, TcpWithoutControls, Connection]] = Connection(**{})
	time_between_actions: Union[int, float]