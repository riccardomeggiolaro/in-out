from libs.lb_utils import CustomBaseModel
from libs.lb_system import SerialPort, Tcp, Connection
from typing import Optional, Union, List
from pydantic import BaseModel

class DataInExecution(BaseModel):
	customer: Optional[str] = None
	supplier: Optional[str] = None
	plate: Optional[str] = None
	vehicle: Optional[str] = None
	material: Optional[str] = None
	
	def setAttribute(self, key, value):
		if hasattr(self, key):
			setattr(self, key, value)

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

class WeightExecuted(BaseModel):
	net_weight: str
	gross_weight: str
	tare: str
	unite_misure: str
	pid: str
	bil: str
	status: str

class Weight(BaseModel):
	weight_executed: WeightExecuted
	data_assigned: Optional[Union[DataInExecution, int]] = None
 
class SetupWeigher(CustomBaseModel):
	max_weight: int
	min_weight: int
	division: int
	maintaine_session_realtime_after_command: bool
	diagnostic_has_priority_than_realtime: bool
	node: Optional[str] = None
	terminal: str
	run: bool

class Configuration(CustomBaseModel):
	nodes: Optional[List[SetupWeigher]] = []
	connection: Optional[Union[SerialPort, Tcp, Connection]] = Connection(**{})
	time_between_actions: Union[int, float]