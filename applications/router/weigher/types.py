from pydantic import BaseModel
from libs.lb_database import SocialReasonDTOInit, VectorDTOInit, VehicleDTOInit, MaterialDTOInit, update_data
from typing import Union, Optional, List

class DataInExecution(BaseModel):
	typeSocialReason: Optional[Union[int, str]] = None
	social_reason: SocialReasonDTOInit = SocialReasonDTOInit(**{})
	vector: VectorDTOInit = VectorDTOInit(**{})
	vehicle: VehicleDTOInit = VehicleDTOInit(**{})
	material: MaterialDTOInit = MaterialDTOInit(**{})
	note: Optional[str] = None

class IdSelected(BaseModel):
	id: Optional[int] = None

class Data(BaseModel):
	data_in_execution: DataInExecution = DataInExecution(**{})
	id_selected: IdSelected = IdSelected(**{})
	number_weighings: Optional[int] = 1
    
class EventAction(BaseModel):
    take_picture: List[int] = []
    set_rele: List[object] = []