from modules.md_database.functions.get_data_by_attribute import get_data_by_attribute
from pydantic import BaseModel, validator
from typing import Optional
from libs.lb_printer import printer
from libs.lb_utils import hash_password

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

	@validator('password', pre=True, always=True)
	def check_password(cls, v):
		return hash_password(v)

class SetUserDTO(BaseModel):
	password: Optional[str] = None
	printer_name: Optional[str] = None
	
	@validator('password', pre=True, always=True)
	def check_password(cls, v):
		if v is not None and len(v) < 8:
			raise ValueError('Password must be at least 8 characters long')
		if v:
			return hash_password(v)
		return v

	@validator('printer_name', pre=True, always=True)
	def check_printer_name(cls, v):
		if v is not None:
			if v in printer.get_list_printers_name():
				return v
			else:
				raise ValueError('Printer name is not configurated')
		return v