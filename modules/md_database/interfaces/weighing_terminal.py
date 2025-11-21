from pydantic import BaseModel
from typing import Optional

class FilteredWeightTerminal(BaseModel):
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