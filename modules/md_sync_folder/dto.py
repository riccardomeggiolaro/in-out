from pydantic import BaseModel
from typing import Optional, Literal
from pydantic import validator

class SyncFolderDTO(BaseModel):
    ip: str
    domain: Optional[str] = ""
    share_name: str
    sub_path: Optional[str] = ""
    username: str
    password: str
    protocol: Literal["samba", "ftp", "sftp"] = "samba"
    port: Optional[int] = None

    @validator('ip', pre=True, always=True)
    def validate_ip(cls, v, values):
        # Basic validation for IP address format
        parts = v.split('.')
        if len(parts) != 4 or not all(part.isdigit() and 0 <= int(part) <= 255 for part in parts):
            raise ValueError('Invalid IP address format')
        return v

    @validator('port', pre=True, always=True)
    def set_default_port(cls, v, values):
        if v is not None:
            return v
        # Set default port based on protocol
        protocol = values.get('protocol', 'samba')
        if protocol == 'samba':
            return 445
        elif protocol == 'ftp':
            return 21
        elif protocol == 'sftp':
            return 22
        return v