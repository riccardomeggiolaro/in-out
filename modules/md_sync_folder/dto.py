from pydantic import BaseModel
from typing import Optional
from pydantic import validator

class SyncFolderDTO(BaseModel):
    ip: str
    domain: Optional[str] = ""
    share_name: str
    sub_path: Optional[str] = ""
    username: str
    password: str
    
    @validator('ip', pre=True, always=True)
    def validate_ip(cls, v, values):
        # Basic validation for IP address format
        parts = v.split('.')
        if len(parts) != 4 or not all(part.isdigit() and 0 <= int(part) <= 255 for part in parts):
            raise ValueError('Invalid IP address format')
        return v