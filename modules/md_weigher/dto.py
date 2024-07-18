from pydantic import validator
from typing import Optional, Union, List
from lib.lb_system import Connection, SerialPort, Tcp
from modules.md_weigher.globals import terminalsClasses, weighers
from lib.lb_utils import CustomBaseModel

class ChangeSetupWeigherDTO(CustomBaseModel):
	max_weight: Optional[int] = None
	min_weight: Optional[int] = None
	division: Optional[int] = None
	maintaine_session_realtime_after_command: Optional[bool] = None
	diagnostic_has_priority_than_realtime: Optional[bool] = None
	node: Optional[Union[str, None]] = "undefined"
	terminal: Optional[str] = None

	@validator('max_weight', 'min_weight', 'division', pre=True, always=True)
	def check_positive(cls, v):
		if v is not None and v < 1:
			raise ValueError('Value must be greater than or equal to 1')
		return v

	@validator('node', pre=True, always=False)
	def check_node(cls, v, values, **kwargs):
		nodes = [n for n in weighers if n.node == v]
		if len(nodes) > 0:
			raise ValueError('Node just exist')
		return v

	@validator('terminal', pre=True, always=True)
	def check_terminal(cls, v, values, **kwargs):
		for terminal in terminalsClasses:
			if v == terminal["terminal"] or v is None:
				return v
		raise ValueError("Terminal don't exist")

class SetupWeigherDTO(CustomBaseModel):
	max_weight: int
	min_weight: int
	division: int
	maintaine_session_realtime_after_command: bool
	diagnostic_has_priority_than_realtime: bool
	node: Optional[Union[str, None]] = None
	terminal: str

	@validator('max_weight', 'min_weight', 'division', pre=True, always=True)
	def check_positive(cls, v):
		if v is not None and v < 1:
			raise ValueError('Value must be greater than or equal to 1')
		return v

	@validator('node', pre=True, always=False)
	def check_node(cls, v, values, **kwargs):
		nodes = [n for n in weighers if n.node == v]
		if len(nodes) > 0:
			raise ValueError('Node just exist')
		return v

	@validator('terminal', pre=True, always=True)
	def check_terminal(cls, v, values, **kwargs):
		for terminal in terminalsClasses:
			if v == terminal["terminal"]:
				return v
		raise ValueError("Terminal don't exist")
 
class ConfigurationDTO(CustomBaseModel):
	nodes: List[SetupWeigherDTO] = []
	connection: Union[SerialPort, Tcp, Connection, None] = None
	time_between_actions: Union[int, float]

	@validator('connection', pre=True, always=True)
	def check_connection(cls, v):
		if v is None:
			return Connection(**{})
		return v