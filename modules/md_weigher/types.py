from libs.lb_utils import CustomBaseModel
from libs.lb_system import SerialPort, Tcp, Connection, SerialPortWithoutControls, TcpWithoutControls
from typing import Optional, Union, Dict, Any
from pydantic import BaseModel

class PlateWeighing(BaseModel):
	plate: str

class Realtime(BaseModel):
	status: str
	type: str
	net_weight: str 
	gross_weight: str
	tare: str
	unite_measure: str
	potential_net_weight: Optional[Union[int, float]] = None
	over_max_theshold: Optional[bool] = False
	
class Diagnostic(CustomBaseModel):
	status: int
	firmware: str
	model_name: str
	serial_number: str
	vl: str
	rz: str

class Tare(BaseModel):
	value: str = ""
	is_preset_tare: bool = False

class WeightExecuted(BaseModel):
	net_weight: str
	gross_weight: str
	tare: Tare
	unite_misure: str
	pid: str
	bil: str
	status: str
	executed: bool
	log: str
	serial_number: str

class Weight(BaseModel):
	weight_executed: WeightExecuted
	data_assigned: Optional[int] = None

class SetupWeigher(CustomBaseModel):
	max_weight: int
	min_weight: int
	division: int
	maintaine_session_realtime_after_command: bool
	diagnostic_has_priority_than_realtime: bool
	always_execute_realtime_in_undeground: bool
	need_take_of_weight_on_startup: bool
	need_take_of_weight_before_weighing: bool
	node: Optional[str] = None
	terminal: str
	run: bool
	name: Optional[str] = None
	printer_name: Optional[str] = None

class Configuration(CustomBaseModel):
	nodes: Optional[Dict[str, SetupWeigher]] = {}
	connection: Optional[Union[SerialPort, Tcp, Connection]] = Connection(**{})
	time_between_actions: Union[int, float]
 
class ConfigurationWithoutControls(CustomBaseModel):
	nodes: Optional[Dict[str, SetupWeigher]] = {}
	connection: Optional[Union[SerialPortWithoutControls, TcpWithoutControls, Connection]] = Connection(**{})
	time_between_actions: Union[int, float]