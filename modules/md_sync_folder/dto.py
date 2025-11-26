from pydantic import BaseModel
from typing import Optional, Literal
from pydantic import validator

class SyncFolderDTO(BaseModel):
    protocol: Literal['samba', 'ftp', 'sftp'] = 'samba'
    ip: str
    port: Optional[int] = None
    domain: Optional[str] = ""
    share_name: Optional[str] = ""
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

    @validator('port', pre=True, always=True)
    def validate_port(cls, v, values):
        # Set default port based on protocol
        if v is None and 'protocol' in values:
            protocol = values['protocol']
            if protocol == 'ftp':
                return 21
            elif protocol == 'sftp':
                return 22
            elif protocol == 'samba':
                return 445
        return v

    @validator('share_name', pre=True, always=True)
    def validate_share_name(cls, v, values):
        # share_name is required only for samba
        if 'protocol' in values and values['protocol'] == 'samba' and not v:
            raise ValueError('share_name is required for samba protocol')
        return v if v else ""