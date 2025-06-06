from libs.lb_utils import CustomBaseModel
from typing import Optional
from pydantic import root_validator, validator, BaseModel
from modules.md_database.interfaces.subject import SubjectDTO
from modules.md_database.interfaces.vector import VectorDTO
from modules.md_database.interfaces.driver import DriverDTO
from modules.md_database.interfaces.vehicle import VehicleDTO
from modules.md_database.interfaces.material import MaterialDTO
from modules.md_database.functions.select_reservation_if_uncomplete import select_reservation_if_uncomplete

class DataInExecutionDTO(CustomBaseModel):
	typeSubject: Optional[str] = "CUSTOMER"
	subject: Optional[SubjectDTO] = SubjectDTO(**{})
	vector: Optional[VectorDTO] = VectorDTO(**{})
	driver: Optional[DriverDTO] = DriverDTO(**{})
	vehicle: Optional[VehicleDTO] = VehicleDTO(**{})
	material: Optional[MaterialDTO] = MaterialDTO(**{})
	note: Optional[str] = None
	document_reference: Optional[str] = None

	@root_validator(pre=True)
	def check_only_one_attribute_set(cls, values):
		# Contiamo quanti dei 5 attributi opzionali sono impostati
		non_null_values = sum(1 for key, value in values.items() if value is not None)

		if non_null_values > 1:
			raise ValueError("Solo uno dei seguenti attributi deve essere presente: customer, supplier, vehicle, material, note.")

		return values

	@validator('typeSubject', pre=True, always=True)
	def check_type_social_reason(cls, v, values):
		if v is not None and v not in ["CUSTOMER", "SUPPLIER"]:
			raise ValueError("typeSocialReason può essere solo 'CLIENTE' o 'FORNITORE'")
		return v

class IdSelectedDTO(CustomBaseModel):
	id: Optional[int] = None

	@validator('id', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in [None, -1]:
			data = select_reservation_if_uncomplete(v)
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