from pydantic import BaseModel

class SshClientConnectionDTO(BaseModel):
    server: str
    user: str
    password: str
    ssh_port: int
    forwarding_port: int
    local_port: int