from pydantic import BaseModel, validator, root_validator
from typing import Optional

class VehicleDTO(BaseModel):
	name: Optional[str] = None
	plate: Optional[str] = None
	id: Optional[int] = None

	@validator('id', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in (None, -1):
			data = get_data_by_id('vehicle', v)
			if not data:
				raise ValueError('Id not exist in vehicle')
			else:
				values['plate'] = data.get('plate')
				values['name'] = data.get('name')
		return v

	class Config:
		# Configurazione per consentire l'uso di valori non dichiarati in fase di validazione
		arbitrary_types_allowed = True

class AddVehicleDTO(BaseModel):
    name: Optional[str] = None
    plate: Optional[str] = None

    @root_validator(pre=True)
    def check_at_least_one_field(cls, values):
        name = values.get('name')
        plate = values.get('plate')
        if not name:
            raise ValueError('At least one of "name" or "plate" must be provided.')
        return values

class SetVehicleDTO(BaseModel):
    name: Optional[str] = None
    plate: Optional[str] = None

    @root_validator(pre=True)
    def check_at_least_one_field(cls, values):
        name = values.get('name')
        plate = values.get('plate')
        if not name:
            raise ValueError('At least one of "name" or "plate" must be provided.')
        return values
    
class FilterVehicleDTO(BaseModel):
    name: Optional[str] = None
    plate: Optional[str] = None