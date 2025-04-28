from pydantic import BaseModel, validator, root_validator, field_validator
from typing import Optional, List
from modules.md_database.functions.get_data_by_id import get_data_by_id
from datetime import datetime

class Vehicle(BaseModel):
	plate: Optional[str] = None
	description: Optional[str] = None
	date_created: Optional[datetime] = None
	reservations: List[any] = []
	id: Optional[int] = None

	class Config:
		# Configurazione per consentire l'uso di valori non dichiarati in fase di validazione
		arbitrary_types_allowed = True    

class VehicleDataDTO(BaseModel):
	plate: Optional[str] = None
	description: Optional[str] = None
	id: Optional[int] = None
 
	@validator('id', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in (None, -1):
			if not get_data_by_id('vehicle', v):
				raise ValueError('Id not exist in vehicle')
		return v

class VehicleDTO(BaseModel):
	plate: Optional[str] = None
	description: Optional[str] = None
	id: Optional[int] = None

	@validator('id', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in (None, -1):
			data = get_data_by_id('vehicle', v)
			if not data:
				raise ValueError('Id not exist in vehicle')
			else:
				values['description'] = data.get('description')
				values['plate'] = data.get('plate')
		return v

	class Config:
		# Configurazione per consentire l'uso di valori non dichiarati in fase di validazione
		arbitrary_types_allowed = True

class AddVehicleDTO(BaseModel):
    plate: str
    description: Optional[str] = None

    @field_validator('*', mode='before')
    @classmethod
    def empty_str_to_none(cls, value, info):
        if isinstance(value, str) and value == "":
            return None
        return value

class SetVehicleDTO(BaseModel):
    plate: Optional[str] = None
    description: Optional[str] = None

    @root_validator(pre=True)
    def check_at_least_one_field(cls, values):
        plate = values.get('plate')
        description = values.get('description')
        if not description and not plate:
            raise ValueError('At least one of "description" or "plate" must be provided.')
        return values
    
class FilterVehicleDTO(BaseModel):
    plate: Optional[str] = None
    description: Optional[str] = None