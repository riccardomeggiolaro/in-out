"""
Configuration module for Sync Manager
"""

import os
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Server settings
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    WORKERS: int = Field(default=4, env="WORKERS")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/sync_manager.db",
        env="DATABASE_URL"
    )
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: Optional[str] = Field(default="logs/sync_manager.log", env="LOG_FILE")
    LOG_MAX_SIZE: int = Field(default=10485760, env="LOG_MAX_SIZE")  # 10MB
    LOG_BACKUP_COUNT: int = Field(default=5, env="LOG_BACKUP_COUNT")
    ACCESS_LOG: bool = Field(default=True, env="ACCESS_LOG")
    
    # Sync settings
    DEFAULT_SYNC_INTERVAL: int = Field(default=5, env="DEFAULT_SYNC_INTERVAL")
    MAX_RETRIES: int = Field(default=3, env="MAX_RETRIES")
    RETRY_DELAY: int = Field(default=10, env="RETRY_DELAY")
    BATCH_SIZE: int = Field(default=100, env="BATCH_SIZE")
    FILE_WATCH_DELAY: float = Field(default=0.5, env="FILE_WATCH_DELAY")
    
    # Paths
    DATA_DIR: Path = Field(default=Path("data"), env="DATA_DIR")
    TEMP_DIR: Path = Field(default=Path("/tmp/sync_manager"), env="TEMP_DIR")
    
    # Security
    SECRET_KEY: str = Field(
        default="change-this-secret-key-in-production",
        env="SECRET_KEY"
    )
    API_KEY_ENABLED: bool = Field(default=False, env="API_KEY_ENABLED")
    API_KEY: Optional[str] = Field(default=None, env="API_KEY")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    
    # Monitoring
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    ENABLE_HEALTH: bool = Field(default=True, env="ENABLE_HEALTH")
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = Field(default=30, env="WS_HEARTBEAT_INTERVAL")
    WS_MAX_CONNECTIONS: int = Field(default=100, env="WS_MAX_CONNECTIONS")
    
    # Performance
    MAX_WORKERS_PER_SYNC: int = Field(default=5, env="MAX_WORKERS_PER_SYNC")
    CHUNK_SIZE: int = Field(default=8192, env="CHUNK_SIZE")
    
    # Cloud storage (optional)
    ENABLE_S3: bool = Field(default=False, env="ENABLE_S3")
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = Field(default="us-east-1", env="AWS_REGION")
    
    ENABLE_AZURE: bool = Field(default=False, env="ENABLE_AZURE")
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = Field(
        default=None, env="AZURE_STORAGE_CONNECTION_STRING"
    )
    
    ENABLE_GCS: bool = Field(default=False, env="ENABLE_GCS")
    GCS_CREDENTIALS_PATH: Optional[str] = Field(
        default=None, env="GCS_CREDENTIALS_PATH"
    )
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("DATA_DIR", "TEMP_DIR")
    def create_directories(cls, v):
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @validator("LOG_FILE")
    def create_log_directory(cls, v):
        if v:
            log_path = Path(v)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            return str(log_path)
        return v


# Create settings instance
settings = Settings()

# Create necessary directories
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)

if settings.LOG_FILE:
    Path(settings.LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
