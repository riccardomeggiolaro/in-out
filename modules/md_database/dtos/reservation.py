from pydantic import BaseModel, validator, root_validator
from typing import Optional, List
from modules.md_database.functions.get_data_by_id import get_data_by_id
from modules.md_database.dtos.subject import Subject
from modules.md_database.dtos.vector import Vector
from modules.md_database.dtos.driver import Driver
from modules.md_database.dtos.vehicle import Vehicle
from modules.md_database.dtos.material import Material
from modules.md_database.dtos.weighing import Weighing

class Reservation(BaseModel):
    id: Optional[int] = None
    typeSubject: Optional[int] = None
    idSubject: Optional[int] = None
    idVector: Optional[int] = None
    idDriver: Optional[int] = None
    idVehicle: Optional[int] = None
    idMaterial: Optional[int] = None
    number_weighings: Optional[int] = None
    note: Optional[str] = None
    status: Optional[str] = None
    document_reference: Optional[str] = None
    subject: Optional[Subject] = Subject(**{})
    vector: Optional[Vector] = Vector(**{})
    driver: Optional[Driver] = Driver(**{})
    vehicle: Optional[Vehicle] = Vehicle(**{})
    material: Optional[Material] = Material(**{})
    weighings: List[Weighing] = []

    class Config:
        # Configurazione per consentire l'uso di valori non dichiarati in fase di validazione
        arbitrary_types_allowed = True

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