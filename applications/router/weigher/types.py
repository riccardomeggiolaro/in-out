from pydantic import BaseModel
from libs.lb_database import CustomerDTOInit, SupplierDTOInit, VehicleDTOInit, MaterialDTOInit, update_data
from typing import Union, Optional, List

class DataInExecution(BaseModel):
	customer: CustomerDTOInit = CustomerDTOInit(**{})
	supplier: SupplierDTOInit = SupplierDTOInit(**{})
	vehicle: VehicleDTOInit = VehicleDTOInit(**{})
	material: MaterialDTOInit = MaterialDTOInit(**{})
	note: Union[str, None] = None

class IdSelected(BaseModel):
	id: Optional[int] = None

class Data(BaseModel):
	data_in_execution: DataInExecution = DataInExecution(**{})
	id_selected: IdSelected = IdSelected(**{})
 
class Cam(BaseModel):
    name: str
    url: str
    
class SetCam(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    
class EventAction(BaseModel):
    take_picture: List[int] = []
    set_rele: List[object] = []