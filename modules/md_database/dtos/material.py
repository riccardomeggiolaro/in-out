from pydantic import BaseModel, validator, root_validator
from typing import Optional

class MaterialDTO(BaseModel):
	name: Optional[str] = None
	id: Optional[int] = None

	@validator('id', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in (None, -1):
			data = get_data_by_id('material', v)
			if not data:
				raise ValueError('Id not exist in material')
			else:
				values['name'] = data.get('name')
		return v

	class Config:
		# Configurazione per consentire l'uso di valori non dichiarati in fase di validazione
		arbitrary_types_allowed = True

class AddMaterialDTO(BaseModel):
    name: Optional[str] = None

    @root_validator(pre=True)
    def check_at_least_one_field(cls, values):
        name = values.get('name')
        if not name:
            raise ValueError('At least one of "name" must be provided.')
        return values

class SetMaterialDTO(BaseModel):
    name: Optional[str] = None
    
    @root_validator(pre=True)
    def check_at_least_one_field(cls, values):
        name = values.get('name')
        if not name:
            raise ValueError('At least one of "name" must be provided.')
        return values
    
class FilterMaterialDTO(BaseModel):
    name: Optional[str] = None