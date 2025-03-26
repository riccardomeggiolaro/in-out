from pydantic import BaseModel, validator, root_validator
from typing import Optional

class DriverDTO(BaseModel):
	id: Optional[int] = None
	social_reason:  Optional[str] = None
	telephone: Optional[str] = None
	cfpiva: Optional[str] = None

	@validator('id', pre=True, always=True)
	def check_id(cls, v, values):
		if v not in (None, -1):
			data = get_data_by_id('driver', v)
			if not data:
				raise ValueError('Id not exist in driver')
			else:
				values['social_reason'] = data.get('social_reason')
				values['telephone'] = data.get('telephone')
				values['cfpiva'] = data.get('cfpiva')
		return v

	class Config:
		# Configurazione per consentire l'uso di valori non dichiarati in fase di validazione
		arbitrary_types_allowed = True

class AddDriverDTO(BaseModel):
    social_reason:  Optional[str] = None
    telephone: Optional[str] = None
    cfpiva: Optional[str] = None

    @root_validator(pre=True)
    def check_at_least_one_field(cls, values):
        social_reason = values.get('social_reason')
        telephone = values.get('telephone')
        cfpiva = values.get('cfpiva')
        if not social_reason and not telephone and not cfpiva:
            raise ValueError('At least one of "social_reason", "telephone" or "cfpiva" must be provided.')
        return values

class SetDriverDTO(BaseModel):
    social_reason:  Optional[str] = None
    telephone: Optional[str] = None
    cfpiva: Optional[str] = None

    @root_validator(pre=True)
    def check_at_least_one_field(cls, values):
        social_reason = values.get('social_reason')
        telephone = values.get('telephone')
        cfpiva = values.get('cfpiva')
        if not social_reason and not telephone and not cfpiva:
            raise ValueError('At least one of "social_reason", "telephone" or "cfpiva" must be provided.')
        return values
    
class FilterDriverDTO(BaseModel):
    social_reason:  Optional[str] = None
    telephone: Optional[str] = None
    cfpiva: Optional[str] = None