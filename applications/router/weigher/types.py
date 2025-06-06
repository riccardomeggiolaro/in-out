from pydantic import BaseModel
from modules.md_database.interfaces.subject import SubjectDTO
from modules.md_database.interfaces.vector import VectorDTO
from modules.md_database.interfaces.driver import DriverDTO
from modules.md_database.interfaces.vehicle import VehicleDTO
from modules.md_database.interfaces.material import MaterialDTO
from modules.md_database.md_database import TypeWeightEnum
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

class Data(BaseModel):
	data_in_execution: DataInExecution = DataInExecution(**{})
	id_selected: IdSelected = IdSelected(**{})
	number_weighings: Optional[int] = 1
    
class EventAction(BaseModel):
    take_picture: List[int] = []
    set_rele: List[object] = []
    
class Weight(BaseModel):
	weight: Union[int, float] = None
	type: Optional[TypeWeightEnum] = None
	date: Optional[datetime] = None
	pid: Optional[str] = None
    
class ReportVariables(DataInExecution):
	material: MaterialDTO = MaterialDTO(**{})
	weight1: Weight = Weight(**{})
	weight2: Weight = Weight(**{})
	net_weight: Union[int, float] = None