from libs.lb_utils import CustomBaseModel
from typing import Optional
from pydantic import root_validator, validator, BaseModel
from modules.md_database.interfaces.subject import SubjectDTO
from modules.md_database.interfaces.vector import VectorDTO
from modules.md_database.interfaces.driver import DriverDTO
from modules.md_database.interfaces.vehicle import VehicleDTO
from modules.md_database.interfaces.material import MaterialDTO
import os

class PathDTO(BaseModel):
    path: Optional[str] = None

    @validator('path', pre=True, always=True)
    def validate_directory_format(cls, v):
        # Verifica se il percorso ha un formato valido
        # Su Windows, dovremmo avere un formato tipo: "C:\\Users\\user\\Documents" o "\\\\PC_REMOTO\\condivisa"
        # Su Linux, dovremmo avere qualcosa come "/home/user/documents" o "/mnt/nfs/share"
        
        if v is not None:
            # Verifica se la directory è accessibile
            if not os.path.isdir(v):
                raise ValueError(f"The path {v} is not a valid directory or is not accessible.")
            
            # Controlla se la directory è leggibile (accesso in lettura)
            if not os.access(v, os.R_OK):
                raise ValueError(f"The directory {v} is not readable.")
            
            # Verifica se il percorso è relativo o assoluto
            if not os.path.isabs(v):  # Se non è un percorso assoluto
                raise ValueError(f"The directory path '{v}' must be an absolute path.")
            
            # Se è un percorso di rete (in stile Windows), controlla se il formato è valido
            if '\\' in v and not v.startswith('\\\\'):
                raise ValueError(f"The network path '{v}' should start with '\\\\' (double backslash for network shares).")

            # Puoi aggiungere ulteriori controlli di formato qui, se necessario

        return v

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

class DataDTO(BaseModel):
    data_in_execution: Optional[DataInExecutionDTO] = DataInExecutionDTO(**{})
    id_selected: Optional[IdSelectedDTO] = IdSelectedDTO(**{})

class TagDTO(BaseModel):
    identify: str

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