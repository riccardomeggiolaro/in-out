from pydantic import BaseModel, validator
from typing import Optional

class UserDTO(BaseModel):
	username: str
	password: str
	level: int
	description: str
	printer_name: Optional[str] = None

	@validator('username', pre=True, always=True)
	def check_username(cls, v):
		data = get_data_by_attribute('user', 'username', v)
		if data:
			raise ValueError('Username already exists')
		if len(v) < 3:
			raise ValueError('Username must be at least 3 characters long')
		return v

	@validator('password', pre=True, always=True)
	def check_password(cls, v):
		if len(v) < 8:
			raise ValueError('Password must be at least 8 characters long')
		return hash_password(v)

class LoginDTO(BaseModel):
	username: str
	password: str