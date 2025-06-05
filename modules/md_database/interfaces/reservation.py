from pydantic import BaseModel, validator
from typing import Optional, List
from modules.md_database.md_database import TypeSubjectEnum
from modules.md_database.interfaces.subject import Subject, SubjectDataDTO
from modules.md_database.interfaces.vector import Vector, VectorDataDTO
from modules.md_database.interfaces.driver import Driver, DriverDataDTO
from modules.md_database.interfaces.vehicle import Vehicle, VehicleDataDTO
from modules.md_database.interfaces.weighing import Weighing
from datetime import datetime

class Reservation(BaseModel):
    id: Optional[int] = None
    typeSubject: Optional[str] = None
    idSubject: Optional[int] = None
    idVector: Optional[int] = None
    idDriver: Optional[int] = None
    idVehicle: Optional[int] = None
    number_weighings: Optional[int] = None
    note: Optional[str] = None
    status: Optional[str] = None
    number_weighings: Optional[int] = None
    document_reference: Optional[str] = None
    date_created: Optional[datetime] = None

    subject: Optional[Subject] = None
    vector: Optional[Vector] = None
    driver: Optional[Driver] = None
    vehicle: Optional[Vehicle] = None
    weighings: List[Weighing] = []

    class Config:
        # Configurazione per consentire l'uso di valori non dichiarati in fase di validazione
        arbitrary_types_allowed = True

    @validator('weighings', pre=True, always=True)
    def check_weighings(cls, v, values):
        return [Weighing(**weighing).dict() for weighing in v]

class AddReservationDTO(BaseModel):
    typeSubject: str = "CUSTOMER"
    subject: SubjectDataDTO = SubjectDataDTO(**{})
    vector: VectorDataDTO = VectorDataDTO(**{})
    driver: DriverDataDTO = DriverDataDTO(**{})
    vehicle: VehicleDataDTO = VehicleDataDTO(**{})
    number_weighings: int = 2
    note: Optional[str] = None
    document_reference: Optional[str] = None

    @validator('typeSubject', pre=True, always=True)
    def check_type_subject(cls, v, values):
        if v in ["CUSTOMER", "SUPPLIER"]:
            return v
        raise ValueError("typeSubject is not a valid string")
    
class SetReservationDTO(BaseModel):
    typeSubject: Optional[str] = None
    subject: SubjectDataDTO = SubjectDataDTO(**{})
    vector: VectorDataDTO = VectorDataDTO(**{})
    driver: DriverDataDTO = DriverDataDTO(**{})
    vehicle: VehicleDataDTO = VehicleDataDTO(**{})
    number_weighings: Optional[int] = None
    note: Optional[str] = None
    document_reference: Optional[str] = None

    @validator('typeSubject', pre=True, always=True)
    def check_type_subject(cls, v, values):
        if v:
            if v in ["CUSTOMER", "SUPPLIER"]:
                return v
            else:
                raise ValueError("typeSubject is not a valid string")
        return v