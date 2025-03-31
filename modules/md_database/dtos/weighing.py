from pydantic import BaseModel
from typing import Optional, Union

# Model for Weighing table
class Weighing(BaseModel):
    id: Optional[int] = None
    weight: Optional[Union[int, float]] = None
    date: Optional[date] = None
    pid: Optional[str] = None
    weigher: Optional[str] = None