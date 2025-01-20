from pydantic import BaseModel

class G(BaseModel):
    a: bytes
    
d = G(a=b'')

d.a = b''