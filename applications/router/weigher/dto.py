from libs.lb_utils import CustomBaseModel, is_number
from libs.lb_database import SocialReasonDTO, VectorDTO, VehicleDTO, MaterialDTO, get_data_by_id, get_data_by_id_if_is_selected, update_data, select_reservation_if_incomplete
from typing import Optional, Union
from pydantic import root_validator, validator, BaseModel
from applications.router.weigher.types import DataInExecution

class DataInExecutionDTO(CustomBaseModel):
	typeSocialReason: Optional[Union[int, str]] = None
	social_reason: Optional[SocialReasonDTO] = SocialReasonDTO(**{})
	vector: Optional[VectorDTO] = VectorDTO(**{})
	vehicle: Optional[VehicleDTO] = VehicleDTO(**{})
	material: Optional[MaterialDTO] = MaterialDTO(**{})
	note: Optional[str] = None

	@root_validator(pre=True)
	def check_only_one_attribute_set(cls, values):
		# Contiamo quanti dei 5 attributi opzionali sono impostati
		non_null_values = sum(1 for key, value in values.items() if value is not None)

		if non_null_values > 1:
			raise ValueError("Solo uno dei seguenti attributi deve essere presente: customer, supplier, vehicle, material, note.")

		return values

	@validator('typeSocialReason', pre=True, always=True)
	def check_type_social_reason(cls, v, values):
		if v is not None:
			if type(v) == str:
				if not is_number(v):
					raise ValueError("Type social reason must to be a digit string or number")
				else:
					v = int(v)
			if v not in [0, 1, -1]:
				raise ValueError("Type Social Reason must to be 1 for 'customer', 2 for 'supplier' or void if you don't want to be specic")
		return v

class IdSelectedDTO(CustomBaseModel):
	id: Optional[int] = None

	@validator('id', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in [None, -1]:
			data = select_reservation_if_incomplete(v)
			import libs.lb_log as lb_log
			lb_log.warning(data)
		return v

class DataDTO(BaseModel):
    data_in_execution: Optional[DataInExecutionDTO] = DataInExecutionDTO(**{})
    id_selected: Optional[IdSelectedDTO] = IdSelectedDTO(**{})

class PlateDTO(BaseModel):
    plate: str

class CamDTO(BaseModel):
    name: str
    url: str
    
class SetCamDTO(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None

class ReleDTO(BaseModel):
    name: str
    status: Optional[int] = 0
    
    @validator('status', pre=True, always=True)
    def check_status(cls, v, values):
        if v not in [0, 1]:
            raise ValueError("Status must to be 1 or 2")
        return v
    
class EVentDTO(BaseModel):
    event: str
    
    @validator('event', pre=True, always=True)
    def check_event(cls, v, values):
        if v not in ["over_min", "under_min", "weight1", "weight2"]:
            raise ValueError("Event not exist")
        return v
    
class CamEventDTO(EVentDTO):
    cam: str

class ReleEventDTO(EVentDTO):
	rele: ReleDTO