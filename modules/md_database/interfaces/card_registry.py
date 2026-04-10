from pydantic import BaseModel, validator, root_validator
from typing import Optional
from datetime import datetime


class CardRegistry(BaseModel):
    id: Optional[int] = None
    number: Optional[str] = None
    code: Optional[str] = None
    date_created: Optional[datetime] = None

    class Config:
        arbitrary_types_allowed = True


class AddCardRegistryDTO(BaseModel):
    number: str
    code: str

    @root_validator(pre=True)
    def check_fields(cls, values):
        number = values.get('number')
        code = values.get('code')
        if not number:
            raise ValueError('"number" è obbligatorio.')
        if not code:
            raise ValueError('"code" è obbligatorio.')
        return values


class SetCardRegistryDTO(BaseModel):
    number: Optional[str] = None
    code: Optional[str] = None

    @root_validator(pre=True)
    def check_at_least_one(cls, values):
        if not values.get('number') and not values.get('code'):
            raise ValueError('Almeno uno tra "number" e "code" deve essere fornito.')
        return values
