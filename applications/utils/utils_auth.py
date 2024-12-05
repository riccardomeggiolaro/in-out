import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel

class TokenData(BaseModel):
    sub: str 
    exp: datetime

def create_access_token(data: dict, secret_key: str, expires_delta: timedelta = timedelta(hours=1)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret_key, algorithm="HS256")