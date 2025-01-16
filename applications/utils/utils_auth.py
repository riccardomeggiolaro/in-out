import jwt
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from typing import Optional
import bcrypt
from apscheduler.schedulers.blocking import BlockingScheduler
import libs.lb_config as lb_config
from pydantic import validator

class LoginDTO(BaseModel):
	username: str   
	password: str

	@validator('password', pre=True, always=True)
	def check_password(cls, v):
		return hash_password(v)

class SetUserPasswordDTO(BaseModel):
	password: str
	
	@validator('password', pre=True, always=True)
	def check_password(cls, v):
		if v is not None and len(v) < 8:
			raise ValueError('Password must be at least 8 characters long')
		if v:
			return hash_password(v)
		return v

class TokenData(BaseModel):
	id: int
	username: str
	password: str
	level: int
	description: str
	printer_name: Optional[str] = None
	exp: datetime

def create_access_token(data: dict, expires_delta: timedelta = timedelta(days=1)):
	to_encode = data.copy()
	expire = datetime.now(timezone.utc) + expires_delta
	to_encode.update({"exp": expire})
	
	return jwt.encode(to_encode, lb_config.g_config["secret_key"], algorithm="HS256")

def hash_password(password: str):
	# Convert password to bytes and generate salt
	password_bytes = password.encode('utf-8')

	salt = "$2b$12$PAHE4kh6lnXo3w9SF9tj7O".encode('utf-8')

	# Hash the password with the generated salt
	hashed_password = bcrypt.hashpw(password_bytes, salt)

	return hashed_password.decode('utf-8')

def update_password_daily():
	scheduler = BlockingScheduler()

	# Imposta il job per eseguire la funzione `update_password_daily` ogni giorno
	scheduler.add_job(update_password_daily, 'interval', days=1)

	scheduler.start()


level_user = {
	"user": 1,
	"admin": 2,
	"super_admin": 3
}

is_admin = [2, 3]

is_super_admin = [3]

all_level = [1, 2, 3]