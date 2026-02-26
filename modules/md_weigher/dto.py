from pydantic import validator, BaseModel, root_validator, AnyUrl
from typing import Optional, Union, Literal
from libs.lb_system import Connection, SerialPort, Tcp
from libs.lb_utils import CustomBaseModel
from modules.md_weigher.globals import terminalsClasses
from pydantic import root_validator

class CamDTO(BaseModel):
	picture: AnyUrl
	live: Optional[AnyUrl] = None
	active: bool

class ReleDTO(BaseModel):
    rele: str
    set: Literal[0, 1]
    order: Optional[int] = 0

class ChangeSetupWeigherDTO(CustomBaseModel):
	name: Optional[str] = "undefined"
	max_weight: Optional[int] = None
	min_weight: Optional[int] = None
	division: Optional[int] = None
	max_theshold: Optional[int] = -1
	maintaine_session_realtime_after_command: Optional[bool] = None
	diagnostic_has_priority_than_realtime: Optional[bool] = None
	always_execute_realtime_in_undeground: Optional[bool] = None
	need_take_of_weight_on_startup: Optional[bool] = None
	need_take_of_weight_before_weighing: Optional[bool] = None
	continuous_transmission: Optional[bool] = None
	node: Optional[str] = "undefined"
	terminal: Optional[str] = None
	run: Optional[bool] = None
	printer_name: Optional[str] = None
	number_of_prints: Optional[int] = 1
	report_on_in: Optional[bool] = None
	report_on_out: Optional[bool] = None
	report_on_generic: Optional[bool] = None
	csv_on_in: Optional[bool] = None
	csv_on_out: Optional[bool] = None
	cams: list[CamDTO] = []
	weighing: list[ReleDTO] = []
	over_min: list[ReleDTO] = []
	under_min: list[ReleDTO] = []

	@root_validator(pre=True)
	def set_node_default(cls, values):
		# Check if 'node' is not provided, then set it to "undefined"
		if 'name' not in values:
			values['name'] = "undefined"
		if 'node' not in values:
			values['node'] = "undefined"
		return values

	@validator('name', pre=True, always=True)
	def check_name_no_spaces(cls, v):
		if v is not None and v != "undefined" and ' ' in v:
			raise ValueError('Il nome non può contenere spazi')
		return v

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
	name: str
	max_weight: int
	min_weight: int
	division: int
	max_theshold: Optional[int] = None
	maintaine_session_realtime_after_command: Optional[bool] = True
	diagnostic_has_priority_than_realtime: Optional[bool] = True
	always_execute_realtime_in_undeground: Optional[bool] = True
	need_take_of_weight_on_startup: Optional[bool] = True
	need_take_of_weight_before_weighing: Optional[bool] = True
	continuous_transmission: Optional[bool] = False
	node: Optional[Union[str, None]] = None
	terminal: str
	run: Optional[bool] = True
	printer_name: Optional[str] = None
	number_of_prints: Optional[int] = 1
	report_on_in: Optional[bool] = True
	report_on_out: Optional[bool] = True
	report_on_generic: Optional[bool] = True
	csv_on_in: Optional[bool] = True
	csv_on_out: Optional[bool] = True
	cams: list[CamDTO] = []
	weighing: list[ReleDTO] = []
	over_min: list[ReleDTO] = []
	under_min: list[ReleDTO] = []

	@validator('name', pre=True, always=True)
	def check_name_no_spaces(cls, v):
		if v is not None and ' ' in v:
			raise ValueError('Il nome non può contenere spazi')
		return v

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