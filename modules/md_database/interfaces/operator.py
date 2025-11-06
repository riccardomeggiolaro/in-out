from pydantic import BaseModel, validator, root_validator
from typing import Optional, List
from modules.md_database.functions.get_data_by_id import get_data_by_id
from datetime import datetime

class Operator(BaseModel):
	description: Optional[str] = None
	date_created: Optional[datetime] = None
	reservations: List[any] = []
	id: Optional[int] = None

	class Config:
		# Configurazione per consentire l'uso di valori non dichiarati in fase di validazione
		arbitrary_types_allowed = True

class OperatorDataDTO(BaseModel):
	description:  Optional[str] = None
	id: Optional[int] = None

	@validator('id', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in (None, -1):
			if not get_data_by_id('operator', v):
				raise ValueError('Id not exist in operator')
		return v

class OperatorDTO(BaseModel):
	description:  Optional[str] = None
	id: Optional[int] = None

	@validator('id', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in (None, -1):
			data = get_data_by_id('operator', v)
			if not data:
				raise ValueError('Id not exist in operator')
			else:
				values['description'] = data.get('description')
		return v

	class Config:
		# Configurazione per consentire l'uso di valori non dichiarati in fase di validazione
		arbitrary_types_allowed = True

class AddOperatorDTO(BaseModel):
    description: Optional[str] = None

    @root_validator(pre=True)
    def check_at_least_one_field(cls, values):
        description = values.get('description')
        if not description: 
            raise ValueError('At least one of "name" must be provided.')
        return values

class SetOperatorDTO(BaseModel):
    description: Optional[str] = None
    
    @root_validator(pre=True)
    def check_at_least_one_field(cls, values):
        description = values.get('description')
        if not description:
            raise ValueError('At least one of "name" must be provided.')
        return values
    
class FilterOperatorDTO(BaseModel):
    description: Optional[str] = None