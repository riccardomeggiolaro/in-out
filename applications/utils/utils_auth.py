import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional

class SetUserDTO(BaseModel):
    descripotion: Optional[str] = None
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

level_user = {
    "user": 1,
    "admin": 2,
    "super_admin": 3
}

is_admin = [2, 3]

is_super_admin = [3]