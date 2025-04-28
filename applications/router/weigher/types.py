from pydantic import BaseModel
from modules.md_database.interfaces.subject import SubjectDTO
from modules.md_database.interfaces.vector import VectorDTO
from modules.md_database.interfaces.driver import DriverDTO
from modules.md_database.interfaces.vehicle import VehicleDTO
from modules.md_database.interfaces.material import MaterialDTO
from typing import Union, Optional, List

class DataInExecution(BaseModel):
	typeSubject: Optional[str] = None
	subject: SubjectDTO = SubjectDTO(**{})
	vector: VectorDTO = VectorDTO(**{})
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