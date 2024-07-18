from lib.lb_utils import CustomBaseModel
from typing import Optional, Union
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