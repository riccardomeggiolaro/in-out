from pydantic import validator, BaseModel, ValidationError, root_validator
from typing import Optional, Union, List
from libs.lb_system import Connection, SerialPort, Tcp
from libs.lb_utils import CustomBaseModel
from modules.md_weigher.types import SetupWeigher
from modules.md_weigher.globals import terminalsClasses
from libs.lb_database import CustomerDTO, SupplierDTO, VehicleDTO, MaterialDTO, get_data_by_id
from pydantic import root_validator
from modules.md_weigher.types import Cam, DataInExecution

class DataInExecutionDTO(CustomBaseModel):
	customer: Optional[CustomerDTO] = CustomerDTO(**{})
	supplier: Optional[SupplierDTO] = SupplierDTO(**{})
	vehicle: Optional[VehicleDTO] = VehicleDTO(**{})
	material: Optional[MaterialDTO] = MaterialDTO(**{})
	note: Optional[str] = None

	@root_validator(pre=True)
	def check_only_one_attribute_set(cls, values):
		# Contiamo quanti dei 5 attributi opzionali sono impostati
		non_null_values = sum(1 for key, value in values.items() if value is not None)

		if non_null_values > 1:
			raise ValueError("Solo uno dei seguenti attributi deve essere presente: customer, supplier, vehicle, material, note.")

		return values

class IdSelectedDTO(CustomBaseModel):
	id: Optional[int] = None

	@validator('id', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in [None, -1]:
			data = get_data_by_id('weighing', v, True, True)
			if not data:
				raise ValueError('Id not exist in weighings')
		return v

class DataDTO(BaseModel):
    data_in_execution: Optional[DataInExecutionDTO] = DataInExecutionDTO(**{})
    id_selected: Optional[IdSelectedDTO] = IdSelectedDTO(**{})

class WeighingDataDTO(CustomBaseModel):
	id_selected: Optional[int] = None
	plate: Optional[str] = None
	data_in_execution: Optional[DataInExecution] = None

	@root_validator(pre=True)
	def check_only_one_attribute_set(cls, values):
		# Contiamo quanti dei 5 attributi opzionali sono impostati
		non_null_values = sum(1 for key, value in values.items() if value is not None)

		if non_null_values > 1:
			raise ValueError("Solo uno dei seguenti attributi deve essere presente: id o plate.")

		return values

class ChangeSetupWeigherDTO(CustomBaseModel):
	max_weight: Optional[int] = None
	min_weight: Optional[int] = None
	division: Optional[int] = None
	maintaine_session_realtime_after_command: Optional[bool] = None
	diagnostic_has_priority_than_realtime: Optional[bool] = None
	node: Optional[Union[str]] = "undefined"
	terminal: Optional[str] = None
	run: Optional[bool] = None
	name: Optional[str] = None
	cam1: Optional[Union[Cam, dict]] = None
	cam2: Optional[Union[Cam, dict]] = None
	cam3: Optional[Union[Cam, dict]] = None
	cam4: Optional[Union[Cam, dict]] = None

	@root_validator(pre=True)
	def set_node_default(cls, values):
		# Check if 'node' is not provided, then set it to "undefined"
		if 'node' not in values:
			values['node'] = "undefined"
		return values

	@validator('max_weight', 'min_weight', 'division', pre=True, always=True)
	def check_positive(cls, v):
		if v is not None and v < 1:
			raise ValueError(f'Value must be greater than or equal to 1')
		return v

	@validator('terminal', pre=True, always=True)
	def check_terminal(cls, v):
		if v is not None and v not in terminalsClasses:
			raise ValueError("Terminal don't exist")
		return v

class SetupWeigherDTO(BaseModel):
	max_weight: int
	min_weight: int
	division: int
	maintaine_session_realtime_after_command: Optional[bool] = True
	diagnostic_has_priority_than_realtime: Optional[bool] = True
	node: Optional[Union[str, None]] = None
	terminal: str
	run: Optional[bool] = True
	name: str
	cam1: Optional[Cam] = None
	cam2: Optional[Cam] = None
	cam3: Optional[Cam] = None
	cam4: Optional[Cam] = None

	@validator('max_weight', 'min_weight', 'division', pre=True, always=True)
	def check_positive(cls, v):
		if v is not None and v < 1:
			raise ValueError('Value must be greater than or equal to 1')
		return v

	@validator('terminal', pre=True, always=True)
	def check_terminal(cls, v, values, **kwargs):
		if v not in terminalsClasses:
			raise ValueError("Terminal don't exist")
		return v

class ConfigurationDTO(CustomBaseModel):
	name: str
	connection: Optional[Union[SerialPort, Tcp, Connection]]
	time_between_actions: Union[int, float]
 
	@validator('connection', pre=True, always=True)
	def check_connection(cls, v, values, **kwargs):
		if v is None:
			v = Connection(**{})
		# Se è un dizionario, prova a crearlo come oggetto del tipo corretto
		# Controlla se è un dizionario
		if isinstance(v, dict):
			if set(v.keys()) == {"serial_port_name", "baudrate", "timeout"}:
				try:
					# Prova a validare come SerialPort
					v = SerialPort(**v)
				except ValueError as e:
					# Solleva una nuova ValidationError con il messaggio originale
					raise e
			elif set(v.keys()) == {"ip", "port", "timeout"}:
				try:
					# Prova a validare come Tcp
					v = Tcp(**v)
				except ValueError as e:
					raise e
			else:
				v = Connection(**{})
		return v

	@validator('time_between_actions', pre=True, always=True)
	def check_time_between_actions(cls, v, values, **kwargs):
		if v <= 0:
			raise ValueError('time_between_actions must to be grater than 0')
		return v