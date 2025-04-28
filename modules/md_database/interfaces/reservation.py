from pydantic import BaseModel, validator
from typing import Optional, List
from modules.md_database.interfaces.subject import Subject, SubjectDataDTO
from modules.md_database.interfaces.vector import Vector, VectorDataDTO
from modules.md_database.interfaces.driver import Driver, DriverDataDTO
from modules.md_database.interfaces.vehicle import Vehicle, VehicleDataDTO
from modules.md_database.interfaces.material import Material
from modules.md_database.interfaces.weighing import Weighing
from datetime import datetime

class Reservation(BaseModel):
    id: Optional[int] = None
    typeSubject: Optional[str] = None
    idSubject: Optional[int] = None
    idVector: Optional[int] = None
    idDriver: Optional[int] = None
    idVehicle: Optional[int] = None
    idMaterial: Optional[int] = None
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
    material: Optional[Material] = None
    weighings: List[Weighing] = []

    class Config:
        # Configurazione per consentire l'uso di valori non dichiarati in fase di validazione
        arbitrary_types_allowed = True

    @validator('weighings', pre=True, always=True)
    def check_weighings(cls, v, values):
        return [Weighing(**weighing).dict() for weighing in v]

# class ReservationDTO(BaseModel):
#     id: Optional[Union[int, str]] = None
#     typeSocialReason: Optional[Union[int, str]] = None
#     idSocialReason: Optional[Union[int, str]] = None
#     idVector:Optional[Union[int, str]] = None
#     idVehicle: Optional[Union[int, str]] = None
#     idMaterial: Optional[Union[int, str]] = None
#     number_weighings: Optional[Union[int, str]] = None
#     note: Optional[str] = None

#     @validator('id', pre=True, always=True)
#     def check_id(cls, v, values):
#         if type(v) == str:
#             if not v.isdigit():
#                 raise ValueError("id must to a digit string or number")
#             else:
#                 v = int(v)
#         if v not in [None, -1]:
#             if type(v) == str and v.isdigit():
#                 v = int(v)
#             data = get_data_by_id('reservation', v)
#             if not data:
#                 raise ValueError('Id not exist in reservation')
#         return v

#     @validator('typeSocialReason', pre=True, always=True)
#     def check_type_social_reason(cls, v, values):
#         if v is not None:
#             if type(v) == str:
#                 if not is_number(v):
#                     raise ValueError("Type social reason must to be a digit string or number")
#                 else:
#                     v = int(v)
#             if v not in [0, 1]:
#                 raise ValueError("Type Social Reason must to be 1 for 'customer', 2 for 'supplier' or void if you don't want to be specic")
#         return v

#     @validator('idSocialReason', pre=True, always=True)
#     def check_customer_id(cls, v, values):
#         if type(v) == str:
#             if not v.isdigit():
#                 raise ValueError("Social Reason must to a digit string or number")
#             else:
#                 v = int(v)
#         if v not in [None, -1]:
#             if type(v) == str and v.isdigit():
#                 v = int(v)
#             data = get_data_by_id('social_reason', v)
#             if not data:
#                 raise ValueError('Id not exist in social reason')
#         return v

#     @validator('idVector', pre=True, always=True)
#     def check_customer_id(cls, v, values):
#         if type(v) == str:
#             if not v.isdigit():
#                 raise ValueError("Vector must to a digit string or number")
#             else:
#                 v = int(v)
#         if v not in [None, -1]:
#             if type(v) == str and v.isdigit():
#                 v = int(v)
#             data = get_data_by_id('social_reason', v)
#             if not data:
#                 raise ValueError('Id not exist in social reason')
#         return v

#     @validator('idVehicle', pre=True, always=True)
#     def check_vehicle_id(cls, v, values):
#         if type(v) == str:
#             if not v.isdigit():
#                 raise ValueError("Vehicle must to a digit string or number")
#             else:
#                 v = int(v)
#         if v not in [None, -1]:
#             if type(v) == str and v.isdigit():
#                 v = int(v)
#             data = get_data_by_id('vehicle', v)
#             if not data:
#                 raise ValueError('Id not exist in vehicle')
#         return v

#     @validator('idMaterial', pre=True, always=True)
#     def check_material_id(cls, v, values):
#         if type(v) == str:
#             if not v.isdigit():
#                 raise ValueError("Material must to a digit string or number")
#             else:
#                 v = int(v)
#         if v not in [None, -1]:
#             data = get_data_by_id('material', v)
#             if not data:
#                 raise ValueError('Id not exist in material')
#         return v

#     @validator('number_weighings', pre=True, always=True)
#     def check_weighings(cls, v, values):
#         if type(v) == str:
#             if not v.isdigit():
#                 raise ValueError("Number weighings must to a digit string or number")
#             else:
#                 v = int(v)
#         if v is not None and v <= 0:
#             raise ValueError('Number weighings must to be greater than 0')
#         return v

class AddReservationDTO(BaseModel):
    typeSubject: str
    subject: Optional[SubjectDataDTO] = SubjectDataDTO(**{})
    vector: Optional[VectorDataDTO] = VectorDataDTO(**{})
    driver: Optional[DriverDataDTO] = DriverDataDTO(**{})
    vehicle: Optional[VehicleDataDTO] = VehicleDataDTO(**{})
    number_weighings: int = 2
    note: Optional[str] = None
    document_reference: Optional[str] = None
    
class SetReservationDTO(BaseModel):
    typeSubject: Optional[str] = None
    subject: Optional[SubjectDataDTO] = SubjectDataDTO(**{})
    vector: Optional[VectorDataDTO] = VectorDataDTO(**{})
    driver: Optional[DriverDataDTO] = DriverDataDTO(**{})
    vehicle: Optional[VehicleDataDTO] = VehicleDataDTO(**{})
    number_weighings: int = 2
    note: Optional[str] = None
    document_reference: Optional[str] = None