from pydantic import BaseModel
from typing import Optional, Union
from modules.md_database.interfaces.operator import Operator

# Model for Weighing table
class Weighing(BaseModel):
    id: Optional[int] = None
    weight: Optional[Union[int, float]] = None
    pid: Optional[str] = None
    weigher: Optional[str] = None
    idOperator: Optional[int] = None
    
    operator: Optional[Operator] = None