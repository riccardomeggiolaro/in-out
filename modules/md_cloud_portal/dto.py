from pydantic import BaseModel, validator

class CloudPortalDTO(BaseModel):
    enabled: bool = False
    base_url: str = ""
    api_key: str = ""
    sync_interval_seconds: float = 10.0
    batch_size: int = 50
    only_closed: bool = True
    verify_ssl: bool = True

    @validator('base_url', pre=True, always=True)
    def strip_trailing_slash(cls, v):
        return v.rstrip('/') if v else v

    @validator('sync_interval_seconds', pre=True, always=True)
    def min_interval(cls, v):
        return max(2.0, float(v))

    @validator('batch_size', pre=True, always=True)
    def clamp_batch_size(cls, v):
        return max(1, min(500, int(v)))
