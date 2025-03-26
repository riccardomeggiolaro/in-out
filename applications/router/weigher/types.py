from pydantic import BaseModel
from modules.md_database.dtos.subject import SubjectDTO
from modules.md_database.dtos.vector import VectorDTO
from modules.md_database.dtos.driver import DriverDTO
from modules.md_database.dtos.vehicle import VehicleDTO
from modules.md_database.dtos.material import MaterialDTO
from typing import Union, Optional, List

class DataInExecution(BaseModel):
	typeSocialReason: Optional[Union[int, str]] = None
	subject: SubjectDTO = SubjectDTO(**{})
	vector: DriverDTO = DriverDTO(**{})
	driver: DriverDTO = DriverDTO(**{})
	vehicle: VehicleDTO = VehicleDTO(**{})
	material: MaterialDTO = MaterialDTO(**{})
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