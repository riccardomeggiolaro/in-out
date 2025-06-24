from pydantic import BaseModel
from typing import Optional
from modules.md_database.interfaces.material import Material
from modules.md_database.interfaces.weighing import Weighing

class InOut(BaseModel):
    id: Optional[int] = None
    idReservation: Optional[int] = None
    idMaterial: Optional[int] = None
    idWeight1: Optional[int] = None
    idWeight2: Optional[int] = None
    netWeight: Optional[int] = None

    # Relationships
    material: Optional[Material] = None
    weight1: Optional[Weighing] = None
    weight2: Optional[Weighing] = None