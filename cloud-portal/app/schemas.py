from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ==== AUTH ====================================================

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: int
    username: str
    is_super_admin: bool
    site_id: Optional[int] = None
    site_name: Optional[str] = None


# ==== SITES ====================================================

class SiteCreate(BaseModel):
    name: str
    code: str = Field(pattern=r"^[a-z0-9][a-z0-9\-_]{1,63}$")


class SiteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    api_key_prefix: str
    active: bool
    date_created: datetime


class SiteCreatedOut(SiteOut):
    api_key: str  # mostrata una sola volta


class SiteUserCreate(BaseModel):
    username: str
    password: str = Field(min_length=6)


class SiteUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    site_id: Optional[int] = None
    is_super_admin: bool


# ==== INGEST ====================================================

class WeighingIngest(BaseModel):
    external_id: int

    status: Optional[str] = None
    type: Optional[str] = None
    type_subject: Optional[str] = None

    plate: Optional[str] = None
    vehicle_description: Optional[str] = None
    subject_name: Optional[str] = None
    vector_name: Optional[str] = None
    driver_name: Optional[str] = None
    material: Optional[str] = None

    weight1: Optional[float] = None
    weight1_date: Optional[datetime] = None
    weight1_pid: Optional[str] = None

    weight2: Optional[float] = None
    weight2_date: Optional[datetime] = None
    weight2_pid: Optional[str] = None

    net_weight: Optional[float] = None

    document_reference: Optional[str] = None
    note: Optional[str] = None

    date_created: Optional[datetime] = None


class IngestBatchRequest(BaseModel):
    weighings: list[WeighingIngest]


class IngestBatchResponse(BaseModel):
    received: int
    created: int
    updated: int


# ==== WEIGHINGS (query) ====================================================

class WeighingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    site_id: int
    external_id: int

    status: Optional[str] = None
    type: Optional[str] = None
    type_subject: Optional[str] = None

    plate: Optional[str] = None
    vehicle_description: Optional[str] = None
    subject_name: Optional[str] = None
    vector_name: Optional[str] = None
    driver_name: Optional[str] = None
    material: Optional[str] = None

    weight1: Optional[float] = None
    weight1_date: Optional[datetime] = None
    weight2: Optional[float] = None
    weight2_date: Optional[datetime] = None
    net_weight: Optional[float] = None

    document_reference: Optional[str] = None
    note: Optional[str] = None

    date_created: Optional[datetime] = None
    ingested_at: datetime


class WeighingListResponse(BaseModel):
    data: list[WeighingOut]
    total: int
