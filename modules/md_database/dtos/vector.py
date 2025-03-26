from pydantic import BaseModel, validator
from typing import Optional

class VectorDTO(BaseModel):
	id: Optional[int] = None
	name: Optional[str] = None
	cell: Optional[str] = None
	cfpiva: Optional[str] = None

	@validator('id', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in (None, -1):
			data = get_data_by_id('vector', v)
			if not data:
				raise ValueError('Id not exist in vector')
			else:
				values['name'] = data.get('name')
				values['cell'] = data.get('cell')
				values['cfpiva'] = data.get('cfpiva')
		return v

	class Config:
		# Configurazione per consentire l'uso di valori non dichiarati in fase di validazione
		arbitrary_types_allowed = True

class AddVectorDTO(BaseModel):
    name: Optional[str] = None
    cell: Optional[str] = None
    cfpiva: Optional[str] = None

    @validator('name', 'cell', 'cfpiva', always=True)
    def validate_at_least_one_value(cls, v, values):
        # Check if both name and plate are None
        if not values.get('name') and not values.get('cell') and not values.get('cfpiva'):
            raise ValueError("At least one of name or plate must be provided")
        return v

class SetVectorDTO(BaseModel):
    name: Optional[str] = None
    cell: Optional[str] = None
    cfpiva: Optional[str] = None

    @validator('name', 'cell', 'cfpiva', always=True)
    def validate_at_least_one_value(cls, v, values):
        # Check if both name and plate are None
        if not values.get('name') and not values.get('cell') and not values.get('cfpiva'):
            raise ValueError("At least one of name or plate must be provided")
        return v