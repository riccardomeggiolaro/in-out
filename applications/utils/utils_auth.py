import jwt
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from typing import Optional
import libs.lb_config as lb_config

class TokenData(BaseModel):
	id: int
	username: str
	password: Optional[str] = None
	level: int
	description: str
	printer_name: Optional[str] = None
	exp: datetime

def create_access_token(data: dict, expires_delta: timedelta = timedelta(days=365*100)):
	try:
		to_encode = data.copy()
		expire = datetime.now(timezone.utc) + expires_delta
		to_encode.update({"exp": expire})
		
		return jwt.encode(to_encode, lb_config.g_config["secret_key"], algorithm="HS256")
	except Exception as e:
		return e

level_user = {
	"user": 1,
	"admin": 2,
	"super_admin": 3
}

is_admin = [2, 3]

is_super_admin = [3]

all_level = [1, 2, 3]