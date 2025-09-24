from pydantic import BaseModel
from modules.md_database.interfaces.subject import SubjectDTO
from modules.md_database.interfaces.vector import VectorDTO
from modules.md_database.interfaces.driver import DriverDTO
from modules.md_database.interfaces.vehicle import VehicleDTO
from modules.md_database.interfaces.material import MaterialDTO
from modules.md_database.md_database import TypeAccess
from typing import Union, Optional, List
from datetime import datetime

class DataInExecution(BaseModel):
	typeSubject: Optional[str] = "CUSTOMER"
	subject: SubjectDTO = SubjectDTO(**{})
	vector: VectorDTO = VectorDTO(**{})
	driver: DriverDTO = DriverDTO(**{})
	vehicle: VehicleDTO = VehicleDTO(**{})
	material: MaterialDTO = MaterialDTO(**{})
	note: Optional[str] = None
	document_reference: Optional[str] = None

class IdSelected(BaseModel):
	id: Optional[int] = None
	weight1: Optional[int] = None

class Data(BaseModel):
	data_in_execution: DataInExecution = DataInExecution(**{})
	id_selected: IdSelected = IdSelected(**{})
	number_in_out: Optional[int] = 1
	type: Optional[str] = TypeAccess.MANUALLY.name
    
class EventAction(BaseModel):
    take_picture: List[int] = []
    set_rele: List[object] = []
    
class Weight(BaseModel):
	weight: Union[int, float] = None
	date: Optional[datetime] = None
	pid: Optional[str] = None
    
class Weight1(Weight):
    type: Optional[str] = None

class Weight2(Weight):
    pass
    
class ReportVariables(DataInExecution):
	weight1: Weight1 = Weight1(**{})
	weight2: Weight2 = Weight2(**{})
	net_weight: Union[int, float] = None