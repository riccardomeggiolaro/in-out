from pydantic import BaseModel, validator
from typing import Optional

class Configuration(BaseModel):
    ip: int
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: Optional[float] = 5
    endpoint: Optional[str] = None

    @validator('timeout', pre=True, always=True)
    def check_status(cls, v, values):
        if v <= 0.1:
            raise ValueError("Timeout need to be greater than 0.1")
        return v
    
class Panel(Configuration):
    max_string_content: int
    
    @validator('max_string_content', pre=True, always=True)
    def check_status(cls, v, values):
        if v <= 0:
            raise ValueError("Max string content need to be greater than 0")
        return v
    
class Siren(Configuration):
    pass