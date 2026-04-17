from pydantic import BaseModel
from typing import Optional
from modules.md_database.interfaces.material import Material
from modules.md_database.interfaces.weighing import Weighing
from modules.md_database.interfaces.card_registry import CardRegistry

class InOut(BaseModel):
    id: Optional[int] = None
    idReservation: Optional[int] = None
    idMaterial: Optional[int] = None
    idWeight1: Optional[int] = None
    idWeight2: Optional[int] = None
    netWeight: Optional[int] = None
    idCardRegistry: Optional[int] = None

    # Relationships
    material: Optional[Material] = None
    weight1: Optional[Weighing] = None
    weight2: Optional[Weighing] = None
    card_registry: Optional[CardRegistry] = None