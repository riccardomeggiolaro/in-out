from pydantic import validator
from typing import Optional, Union, List
from libs.lb_system import Connection, SerialPort, Tcp
from libs.lb_utils import CustomBaseModel
from modules.md_weigher.types import SetupWeigher
from modules.md_weigher.globals import terminalsClasses
from libs.lb_database import SocialReasonDTO, VehicleDTO, MaterialDTO

class DataInExecutionDTO(CustomBaseModel):
	customer: Optional[SocialReasonDTO] = None
	supplier: Optional[SocialReasonDTO] = None
	vehicle: Optional[VehicleDTO] = None
	material: Optional[MaterialDTO] = None
	note: Optional[str] = None

class ChangeSetupWeigherDTO(CustomBaseModel):
	max_weight: Optional[int] = None
	min_weight: Optional[int] = None
	division: Optional[int] = None
	maintaine_session_realtime_after_command: Optional[bool] = None
	diagnostic_has_priority_than_realtime: Optional[bool] = None
	node: Optional[Union[str, None]] = "undefined"
	terminal: Optional[str] = None
	run: Optional[bool] = None

	@validator('max_weight', 'min_weight', 'division', pre=True, always=True)
	def check_positive(cls, v):
		if v is not None and v < 1:
			raise ValueError(f'Value must be greater than or equal to 1')
		return v

	@validator('terminal', pre=True, always=True)
	def check_terminal(cls, v):
		print(terminalsClasses)
		if v not in terminalsClasses:
			raise ValueError("Terminal don't exist")
		return v

class SetupWeigherDTO(SetupWeigher):
	max_weight: int
	min_weight: int
	division: int
	maintaine_session_realtime_after_command: bool
	diagnostic_has_priority_than_realtime: bool
	node: Optional[Union[str, None]] = None
	terminal: str
	run: bool

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
	connection: Optional[Union[SerialPort, Tcp, Connection]] = Connection(**{})
	time_between_actions: Union[int, float]
 
	@validator('connection', pre=True, always=True)
	def check_connection(cls, v, values, **kwargs):
		if v is None:
			v = Connection(**{})
		return v