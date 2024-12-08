import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional
import bcrypt
from apscheduler.schedulers.blocking import BlockingScheduler

class LoginDTO(BaseModel):
	username: str
	password: str

class SetUserDTO(BaseModel):
    description: Optional[str] = None
    printer_name: Optional[str] = None

class TokenData(BaseModel):
    sub: str 
    exp: datetime
    level: int

def create_access_token(data: dict, secret_key: str, expires_delta: timedelta = timedelta(hours=1)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret_key, algorithm="HS256")

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