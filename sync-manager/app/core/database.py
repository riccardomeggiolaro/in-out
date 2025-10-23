"""
Database module for Sync Manager
"""

from datetime import datetime
from typing import Optional, List
import enum

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Float, Text, 
    ForeignKey, Enum, Index, JSON, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import relationship, selectinload
from sqlalchemy import select, update, delete

from app.core.config import settings

# Create base class for models
Base = declarative_base()

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)


class SyncStatus(str, enum.Enum):
    """Sync status enumeration"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


class SyncType(str, enum.Enum):
    """Sync type enumeration"""
    LOCAL = "local"
    NETWORK = "network"
    S3 = "s3"
    AZURE = "azure"
    GCS = "gcs"
    FTP = "ftp"
    SFTP = "sftp"


class FileStatus(str, enum.Enum):
    """File sync status enumeration"""
    PENDING = "pending"
    SYNCING = "syncing"
    SYNCED = "synced"
    FAILED = "failed"
    DELETED = "deleted"


class SyncConfiguration(Base):
    """Sync configuration model"""
    __tablename__ = "sync_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Paths
    source_path = Column(String(500), nullable=False)
    source_type = Column(Enum(SyncType), default=SyncType.LOCAL)
    destination_path = Column(String(500), nullable=False)
    destination_type = Column(Enum(SyncType), default=SyncType.NETWORK)
    
    # Configuration
    enabled = Column(Boolean, default=True)
    delete_after_sync = Column(Boolean, default=True)
    sync_interval = Column(Integer, default=5)  # seconds
    max_retries = Column(Integer, default=3)
    retry_delay = Column(Integer, default=10)  # seconds
    batch_size = Column(Integer, default=100)
    
    # Filters
    include_patterns = Column(JSON, nullable=True)  # List of patterns to include
    exclude_patterns = Column(JSON, nullable=True)  # List of patterns to exclude
    min_file_size = Column(Integer, nullable=True)  # bytes
    max_file_size = Column(Integer, nullable=True)  # bytes
    
    # Status
    status = Column(Enum(SyncStatus), default=SyncStatus.IDLE)
    last_sync = Column(DateTime, nullable=True)
    next_sync = Column(DateTime, nullable=True)
    
    # Statistics
    total_files_synced = Column(Integer, default=0)
    total_bytes_synced = Column(Float, default=0)
    total_errors = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    files = relationship("SyncFile", back_populates="sync_config", cascade="all, delete-orphan")
    history = relationship("SyncHistory", back_populates="sync_config", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_sync_status", "status"),
        Index("idx_sync_enabled", "enabled"),
    )


class SyncFile(Base):
    """File sync tracking model"""
    __tablename__ = "sync_files"
    
    id = Column(Integer, primary_key=True, index=True)
    sync_config_id = Column(Integer, ForeignKey("sync_configurations.id"), nullable=False)
    
    # File information
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Float, default=0)  # bytes
    file_hash = Column(String(64), nullable=True)  # SHA256
    
    # Status
    status = Column(Enum(FileStatus), default=FileStatus.PENDING)
    retry_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow)
    synced_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationship
    sync_config = relationship("SyncConfiguration", back_populates="files")
    
    # Indexes
    __table_args__ = (
        UniqueConstraint("sync_config_id", "file_path", name="uq_sync_file"),
        Index("idx_file_status", "status"),
        Index("idx_file_sync_config", "sync_config_id"),
    )


class SyncHistory(Base):
    """Sync operation history model"""
    __tablename__ = "sync_history"
    
    id = Column(Integer, primary_key=True, index=True)
    sync_config_id = Column(Integer, ForeignKey("sync_configurations.id"), nullable=False)
    
    # Operation details
    operation = Column(String(50), nullable=False)  # sync, delete, error, etc.
    file_path = Column(String(500), nullable=True)
    file_size = Column(Float, nullable=True)
    
    # Status
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    duration = Column(Float, nullable=True)  # seconds
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationship
    sync_config = relationship("SyncConfiguration", back_populates="history")
    
    # Indexes
    __table_args__ = (
        Index("idx_history_sync_config", "sync_config_id"),
        Index("idx_history_timestamp", "timestamp"),
        Index("idx_history_operation", "operation"),
    )


class SystemMetrics(Base):
    """System metrics model"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Metrics
    active_syncs = Column(Integer, default=0)
    total_syncs = Column(Integer, default=0)
    files_in_queue = Column(Integer, default=0)
    files_synced_today = Column(Integer, default=0)
    bytes_synced_today = Column(Float, default=0)
    
    # Performance
    cpu_usage = Column(Float, nullable=True)
    memory_usage = Column(Float, nullable=True)
    disk_usage = Column(Float, nullable=True)
    network_throughput = Column(Float, nullable=True)
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Indexes
    __table_args__ = (
        Index("idx_metrics_timestamp", "timestamp"),
    )


# Database initialization
async def init_db():
    """Initialize database"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """Get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Database helper functions
class DatabaseManager:
    """Database manager with helper functions"""
    
    @staticmethod
    async def create_sync_config(session: AsyncSession, data: dict) -> SyncConfiguration:
        """Create new sync configuration"""
        config = SyncConfiguration(**data)
        session.add(config)
        await session.commit()
        await session.refresh(config)
        return config
    
    @staticmethod
    async def get_sync_config(session: AsyncSession, config_id: int) -> Optional[SyncConfiguration]:
        """Get sync configuration by ID"""
        result = await session.execute(
            select(SyncConfiguration)
            .where(SyncConfiguration.id == config_id)
            .options(selectinload(SyncConfiguration.files))
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all_sync_configs(session: AsyncSession, enabled_only: bool = False) -> List[SyncConfiguration]:
        """Get all sync configurations"""
        query = select(SyncConfiguration)
        if enabled_only:
            query = query.where(SyncConfiguration.enabled == True)
        result = await session.execute(query.order_by(SyncConfiguration.created_at))
        return result.scalars().all()
    
    @staticmethod
    async def update_sync_config(session: AsyncSession, config_id: int, data: dict) -> Optional[SyncConfiguration]:
        """Update sync configuration"""
        result = await session.execute(
            update(SyncConfiguration)
            .where(SyncConfiguration.id == config_id)
            .values(**data, updated_at=datetime.utcnow())
            .returning(SyncConfiguration)
        )
        await session.commit()
        return result.scalar_one_or_none()
    
    @staticmethod
    async def delete_sync_config(session: AsyncSession, config_id: int) -> bool:
        """Delete sync configuration"""
        result = await session.execute(
            delete(SyncConfiguration).where(SyncConfiguration.id == config_id)
        )
        await session.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def add_sync_file(session: AsyncSession, sync_config_id: int, file_data: dict) -> SyncFile:
        """Add file to sync queue"""
        file = SyncFile(sync_config_id=sync_config_id, **file_data)
        session.add(file)
        await session.commit()
        await session.refresh(file)
        return file
    
    @staticmethod
    async def get_pending_files(session: AsyncSession, sync_config_id: int, limit: int = 100) -> List[SyncFile]:
        """Get pending files for sync"""
        result = await session.execute(
            select(SyncFile)
            .where(
                SyncFile.sync_config_id == sync_config_id,
                SyncFile.status == FileStatus.PENDING
            )
            .limit(limit)
            .order_by(SyncFile.detected_at)
        )
        return result.scalars().all()
    
    @staticmethod
    async def update_file_status(session: AsyncSession, file_id: int, status: FileStatus, error_msg: str = None):
        """Update file sync status"""
        update_data = {"status": status}
        if status == FileStatus.SYNCED:
            update_data["synced_at"] = datetime.utcnow()
        elif status == FileStatus.DELETED:
            update_data["deleted_at"] = datetime.utcnow()
        if error_msg:
            update_data["error_message"] = error_msg
        
        await session.execute(
            update(SyncFile)
            .where(SyncFile.id == file_id)
            .values(**update_data)
        )
        await session.commit()
    
    @staticmethod
    async def add_history(session: AsyncSession, sync_config_id: int, history_data: dict):
        """Add history entry"""
        history = SyncHistory(sync_config_id=sync_config_id, **history_data)
        session.add(history)
        await session.commit()
    
    @staticmethod
    async def get_sync_history(
        session: AsyncSession, 
        sync_config_id: int, 
        limit: int = 100,
        offset: int = 0
    ) -> List[SyncHistory]:
        """Get sync history"""
        result = await session.execute(
            select(SyncHistory)
            .where(SyncHistory.sync_config_id == sync_config_id)
            .order_by(SyncHistory.timestamp.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
    
    @staticmethod
    async def record_metrics(session: AsyncSession, metrics_data: dict):
        """Record system metrics"""
        metrics = SystemMetrics(**metrics_data)
        session.add(metrics)
        await session.commit()
    
    @staticmethod
    async def get_latest_metrics(session: AsyncSession) -> Optional[SystemMetrics]:
        """Get latest system metrics"""
        result = await session.execute(
            select(SystemMetrics)
            .order_by(SystemMetrics.timestamp.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
