"""
Pydantic schemas for API request/response validation
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, validator, ConfigDict


# Enums
class SyncStatusEnum(str, Enum):
    idle = "idle"
    running = "running"
    paused = "paused"
    error = "error"
    stopped = "stopped"


class SyncTypeEnum(str, Enum):
    local = "local"
    network = "network"
    s3 = "s3"
    azure = "azure"
    gcs = "gcs"
    ftp = "ftp"
    sftp = "sftp"


class FileStatusEnum(str, Enum):
    pending = "pending"
    syncing = "syncing"
    synced = "synced"
    failed = "failed"
    deleted = "deleted"


# Base schemas
class SyncConfigBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Sync configuration name")
    description: Optional[str] = Field(None, description="Description of the sync")
    source_path: str = Field(..., description="Source directory path")
    source_type: SyncTypeEnum = Field(SyncTypeEnum.local, description="Source type")
    destination_path: str = Field(..., description="Destination directory path")
    destination_type: SyncTypeEnum = Field(SyncTypeEnum.network, description="Destination type")
    enabled: bool = Field(True, description="Whether sync is enabled")
    delete_after_sync: bool = Field(True, description="Delete files after successful sync")
    sync_interval: int = Field(5, ge=1, le=86400, description="Sync interval in seconds")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum retry attempts")
    retry_delay: int = Field(10, ge=1, le=3600, description="Delay between retries in seconds")
    batch_size: int = Field(100, ge=1, le=1000, description="Batch size for processing")
    include_patterns: Optional[List[str]] = Field(None, description="File patterns to include")
    exclude_patterns: Optional[List[str]] = Field(None, description="File patterns to exclude")
    min_file_size: Optional[int] = Field(None, ge=0, description="Minimum file size in bytes")
    max_file_size: Optional[int] = Field(None, ge=0, description="Maximum file size in bytes")
    
    @validator('source_path', 'destination_path')
    def validate_paths(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Path cannot be empty")
        return v.strip()
    
    @validator('max_file_size')
    def validate_max_file_size(cls, v, values):
        if v is not None and 'min_file_size' in values and values['min_file_size'] is not None:
            if v < values['min_file_size']:
                raise ValueError("max_file_size must be greater than min_file_size")
        return v


class SyncConfigCreate(SyncConfigBase):
    """Schema for creating a new sync configuration"""
    pass


class SyncConfigUpdate(BaseModel):
    """Schema for updating a sync configuration"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    source_path: Optional[str] = None
    source_type: Optional[SyncTypeEnum] = None
    destination_path: Optional[str] = None
    destination_type: Optional[SyncTypeEnum] = None
    enabled: Optional[bool] = None
    delete_after_sync: Optional[bool] = None
    sync_interval: Optional[int] = Field(None, ge=1, le=86400)
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    retry_delay: Optional[int] = Field(None, ge=1, le=3600)
    batch_size: Optional[int] = Field(None, ge=1, le=1000)
    include_patterns: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None
    min_file_size: Optional[int] = Field(None, ge=0)
    max_file_size: Optional[int] = Field(None, ge=0)


class SyncConfigResponse(SyncConfigBase):
    """Schema for sync configuration response"""
    id: int
    status: SyncStatusEnum
    last_sync: Optional[datetime] = None
    next_sync: Optional[datetime] = None
    total_files_synced: int = 0
    total_bytes_synced: float = 0
    total_errors: int = 0
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class FileResponse(BaseModel):
    """Schema for file response"""
    id: int
    sync_config_id: int
    file_path: str
    file_name: str
    file_size: float
    file_hash: Optional[str] = None
    status: FileStatusEnum
    retry_count: int = 0
    error_message: Optional[str] = None
    detected_at: datetime
    synced_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class SyncHistoryResponse(BaseModel):
    """Schema for sync history response"""
    id: int
    sync_config_id: int
    operation: str
    file_path: Optional[str] = None
    file_size: Optional[float] = None
    success: bool
    error_message: Optional[str] = None
    duration: Optional[float] = None
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SyncStatusResponse(BaseModel):
    """Schema for sync status response"""
    id: int
    name: str
    status: SyncStatusEnum
    enabled: bool = True
    is_running: bool = False
    last_sync: Optional[datetime] = None
    next_sync: Optional[datetime] = None
    queue_size: Optional[int] = None
    retry_queue_size: Optional[int] = None
    stats: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)


class MetricsResponse(BaseModel):
    """Schema for metrics response"""
    timestamp: datetime
    active_syncs: int = 0
    total_syncs: int = 0
    files_in_queue: int = 0
    files_synced_today: int = 0
    bytes_synced_today: float = 0
    total_queued_files: Optional[int] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    disk_usage: Optional[float] = None
    network_throughput: Optional[float] = None
    network_io: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)


class HealthCheckResponse(BaseModel):
    """Schema for health check response"""
    status: str = Field(..., description="Overall health status")
    timestamp: datetime
    checks: Dict[str, str] = Field(..., description="Individual component health checks")
    version: str = Field(..., description="Application version")
    
    model_config = ConfigDict(from_attributes=True)


class BatchOperationResponse(BaseModel):
    """Schema for batch operation response"""
    operation: str
    total: int
    success_count: int
    failed_count: int
    results: Dict[str, List[Any]]
    
    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Schema for error response"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(from_attributes=True)


class WebSocketMessage(BaseModel):
    """Schema for WebSocket messages"""
    type: str = Field(..., description="Message type")
    data: Dict[str, Any] = Field(..., description="Message data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AuthToken(BaseModel):
    """Schema for authentication token"""
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


class CloudCredentials(BaseModel):
    """Schema for cloud storage credentials"""
    provider: str = Field(..., description="Cloud provider: s3, azure, gcs")
    credentials: Dict[str, Any] = Field(..., description="Provider-specific credentials")
    
    @validator('provider')
    def validate_provider(cls, v):
        valid_providers = ["s3", "azure", "gcs"]
        if v.lower() not in valid_providers:
            raise ValueError(f"Provider must be one of {valid_providers}")
        return v.lower()


class NotificationSettings(BaseModel):
    """Schema for notification settings"""
    enabled: bool = Field(True, description="Enable notifications")
    email_enabled: bool = Field(False, description="Send email notifications")
    email_addresses: Optional[List[str]] = Field(None, description="Email addresses for notifications")
    webhook_enabled: bool = Field(False, description="Send webhook notifications")
    webhook_url: Optional[str] = Field(None, description="Webhook URL")
    events: List[str] = Field(
        default=["sync_error", "sync_complete"],
        description="Events to notify on"
    )
    
    @validator('email_addresses')
    def validate_emails(cls, v):
        if v:
            import re
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            for email in v:
                if not re.match(email_regex, email):
                    raise ValueError(f"Invalid email address: {email}")
        return v


class FilterRule(BaseModel):
    """Schema for file filter rules"""
    type: str = Field(..., description="Rule type: include or exclude")
    pattern: str = Field(..., description="File pattern (glob or regex)")
    is_regex: bool = Field(False, description="Whether pattern is regex")
    
    @validator('type')
    def validate_type(cls, v):
        if v not in ["include", "exclude"]:
            raise ValueError("Type must be 'include' or 'exclude'")
        return v


class ScheduleConfig(BaseModel):
    """Schema for sync scheduling configuration"""
    type: str = Field("interval", description="Schedule type: interval, cron, time")
    interval_seconds: Optional[int] = Field(None, ge=1, description="Interval in seconds")
    cron_expression: Optional[str] = Field(None, description="Cron expression")
    time_of_day: Optional[str] = Field(None, description="Time of day (HH:MM)")
    timezone: str = Field("UTC", description="Timezone for scheduling")
    
    @validator('type')
    def validate_type(cls, v):
        if v not in ["interval", "cron", "time"]:
            raise ValueError("Type must be one of: interval, cron, time")
        return v


class SyncStatistics(BaseModel):
    """Schema for detailed sync statistics"""
    sync_id: int
    period: str = Field("day", description="Statistics period: hour, day, week, month")
    start_date: datetime
    end_date: datetime
    total_files: int = 0
    successful_files: int = 0
    failed_files: int = 0
    total_bytes: float = 0
    average_file_size: float = 0
    average_sync_time: float = 0
    error_rate: float = 0
    throughput: float = 0  # bytes per second
    
    model_config = ConfigDict(from_attributes=True)
