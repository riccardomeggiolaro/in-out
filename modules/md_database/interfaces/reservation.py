from pydantic import BaseModel, validator
from typing import Optional, List
from modules.md_database.interfaces.subject import Subject, SubjectDataDTO
from modules.md_database.interfaces.vector import Vector, VectorDataDTO
from modules.md_database.interfaces.driver import Driver, DriverDataDTO
from modules.md_database.interfaces.vehicle import Vehicle, VehicleDataDTO
from modules.md_database.interfaces.material import MaterialDataDTO
from modules.md_database.interfaces.in_out import InOut
from datetime import datetime
import libs.lb_config as lb_config

class Reservation(BaseModel):
    id: Optional[int] = None
    typeSubject: Optional[str] = None
    idSubject: Optional[int] = None
    idVector: Optional[int] = None
    idDriver: Optional[int] = None
    idVehicle: Optional[int] = None
    number_in_out: Optional[int] = None
    note: Optional[str] = None
    status: Optional[str] = None
    document_reference: Optional[str] = None
    date_created: Optional[datetime] = None
    type: Optional[str] = None
    badge: Optional[str] = None
    hidden: Optional[bool] = None

    subject: Optional[Subject] = None
    vector: Optional[Vector] = None
    driver: Optional[Driver] = None
    vehicle: Optional[Vehicle] = None
    in_out: List[InOut] = []

class AddReservationDTO(BaseModel):
    typeSubject: str = "CUSTOMER"
    subject: SubjectDataDTO = SubjectDataDTO(**{})
    vector: VectorDataDTO = VectorDataDTO(**{})
    driver: DriverDataDTO = DriverDataDTO(**{})
    vehicle: VehicleDataDTO = VehicleDataDTO(**{})
    number_in_out: Optional[int] = None
    note: Optional[str] = None
    document_reference: Optional[str] = None
    type: str = "RESERVATION"
    badge: Optional[str] = None
    permanent: Optional[bool] = False
    hidden: Optional[bool] = False

    @validator('typeSubject', pre=True, always=True)
    def check_type_subject(cls, v, values):
        if v in ["CUSTOMER", "SUPPLIER"]:
            return v
        raise ValueError("typeSubject is not a valid string")

    @validator('type', pre=True, always=True)
    def check_type_type(cls, v, values):
        if v in ['RESERVATION', 'MANUALLY', 'TEST']:
            return v
        raise ValueError("type is not a valid string")

    @validator('badge', pre=True, always=True)
    def check_badge(cls, v, values):
        if lb_config.g_config["app_api"]["use_badge"] == False and v is not None:
            raise ValueError("Mode badge is not enabled")
        return v
    
class SetReservationDTO(BaseModel):
    typeSubject: Optional[str] = None
    subject: SubjectDataDTO = SubjectDataDTO(**{})
    vector: VectorDataDTO = VectorDataDTO(**{})
    driver: DriverDataDTO = DriverDataDTO(**{})
    vehicle: VehicleDataDTO = VehicleDataDTO(**{})
    material: MaterialDataDTO = MaterialDataDTO(**{})
    number_in_out: Optional[int] = None
    note: Optional[str] = None
    document_reference: Optional[str] = None
    badge: Optional[str] = None
    permanent: Optional[bool] = None

    @validator('typeSubject', pre=True, always=True)
    def check_type_subject(cls, v, values):
        if v:
            if v in ["CUSTOMER", "SUPPLIER"]:
                return v
            else:
                raise ValueError("typeSubject is not a valid string")
        return v
    
    @validator('badge', pre=True, always=True)
    def check_badge(cls, v, values):
        if lb_config.g_config["app_api"]["use_badge"] == False and v is not None:
            raise ValueError("Mode badge is not enabled")
        return v