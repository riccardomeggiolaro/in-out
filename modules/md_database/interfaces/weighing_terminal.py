from pydantic import BaseModel
from typing import Optional, Union
from datetime import datetime

class WeighingTerminal(BaseModel):
    id: Optional[int] = None
    id_terminal: Optional[str] = None
    bil: Optional[int] = None
    badge: Optional[str] = None
    plate: Optional[str] = None
    customer: Optional[str] = None
    supplier: Optional[str] = None
    material: Optional[str] = None
    notes1: Optional[str] = None
    notes2: Optional[str] = None
    datetime1: Optional[datetime] = None
    date1: Optional[str] = None
    time1: Optional[str] = None
    datetime2: Optional[datetime] = None
    date2: Optional[str] = None
    time2: Optional[str] = None
    prog1: Optional[str] = None
    prog2: Optional[str] = None
    weight1: Optional[Union[int, float]] = None
    pid1: Optional[str] = None
    weight2: Optional[Union[int, float]] = None
    pid2: Optional[str] = None
    net_weight: Optional[Union[int, float]] = None
    date_created: Optional[datetime] = None

class FilteredWeightTerminal(BaseModel):
    id_terminal: Optional[str] = None
    bil: Optional[str] = None
    prog1: Optional[str] = None
    prog2: Optional[str] = None
    badge: Optional[str] = None
    plate: Optional[str] = None
    customer: Optional[str] = None
    supplier: Optional[str] = None
    material: Optional[str] = None
    notes1: Optional[str] = None
    notes2: Optional[str] = None
    pid1: Optional[str] = None
    pid2: Optional[str] = None