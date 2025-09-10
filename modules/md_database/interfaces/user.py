from modules.md_database.functions.get_data_by_attribute import get_data_by_attribute
from pydantic import BaseModel, validator
from typing import Optional
from libs.lb_utils import hash_password

class UserDTO(BaseModel):
	username: str
	password: str
	level: int
	description: str

	@validator('username', pre=True, always=True)
	def check_username(cls, v):
		data = get_data_by_attribute('user', 'username', v)
		if data:
			raise ValueError('Username già esistente')
		return v

	@validator('password', pre=True, always=True)
	def check_password(cls, v):
		if len(v) < 4:
			raise ValueError('La password deve avere almeno 4 caratteri')
		return hash_password(v)

class LoginDTO(BaseModel):
	username: str   
	password: str

	@validator('password', pre=True, always=True)
	def check_password(cls, v):
		return hash_password(v)

class SetUserDTO(BaseModel):
	password: Optional[str] = None
	
	@validator('password', pre=True, always=True)
	def check_password(cls, v):
		if v is not None and len(v) < 4:
			raise ValueError('La password deve avere almeno 4 caratteri')
		if v:
			return hash_password(v)
		return v