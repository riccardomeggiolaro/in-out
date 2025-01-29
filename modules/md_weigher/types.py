from libs.lb_utils import CustomBaseModel
from libs.lb_system import SerialPort, Tcp, Connection, SerialPortWithoutControls, TcpWithoutControls
from typing import Optional, Union, Dict, Any
from pydantic import BaseModel, validator
from datetime import datetime

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
	data_assigned: Optional[Any] = None
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
	name: Optional[str] = None
	cam1: Optional[Cam] = None
	cam2: Optional[Cam] = None
	cam3: Optional[Cam] = None
	cam4: Optional[Cam] = None

class Configuration(CustomBaseModel):
	nodes: Optional[Dict[str, SetupWeigher]] = {}
	connection: Optional[Union[SerialPort, Tcp, Connection]] = Connection(**{})
	time_between_actions: Union[int, float]
 
class ConfigurationWithoutControls(CustomBaseModel):
	nodes: Optional[Dict[str, SetupWeigher]] = {}
	connection: Optional[Union[SerialPortWithoutControls, TcpWithoutControls, Connection]] = Connection(**{})
	time_between_actions: Union[int, float]