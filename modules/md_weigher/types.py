from libs.lb_utils import CustomBaseModel
from libs.lb_system import SerialPort, Tcp, Connection
from typing import Optional, Union, List
from pydantic import BaseModel
from libs.lb_database import VehicleDTO, SocialReasonDTO, MaterialDTO
import libs.lb_log as lb_log

class DataInExecution(BaseModel):
	customer: SocialReasonDTO
	supplier: SocialReasonDTO
	vehicle: VehicleDTO
	material: MaterialDTO

	def setAttribute(self, source):
		for key, value in vars(source).items():
			if isinstance(value, object) and value is not None:
				current_attr = getattr(self, key)
				if hasattr(current_attr, 'id') and isinstance(getattr(current_attr, 'id'), int):
					# Verifica se `source` ha qualsiasi altro attributo diverso da `id`				
					if any(sub_key != 'id' for sub_key in vars(source).keys()):
						# Se ci sono altri attributi, resetta tutti gli attributi di `self` a None, tranne `id`
						for attr in vars(current_attr):
							setattr(current_attr, attr, None)
				for sub_key, sub_value in vars(value).items():
					# Se il valore è un tipo primitivo, log e aggiornamento diretto
					if sub_value in ["undefined", -1]:
						sub_value = None
					setattr(current_attr, sub_key, sub_value)

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