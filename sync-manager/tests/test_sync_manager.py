"""
Tests for Sync Manager
"""

import asyncio
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, AsyncMock

from app.core.sync_manager import SyncManager, SyncWorker
from app.core.database import DatabaseManager, SyncConfiguration, FileStatus
from app.schemas import SyncConfigCreate


# ==================== Fixtures ====================

@pytest.fixture
async def test_db():
    """Create test database"""
    from app.core.database import engine, Base, AsyncSessionLocal
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Provide session
    async with AsyncSessionLocal() as session:
        yield session
    
    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing"""
    with tempfile.TemporaryDirectory() as source_dir:
        with tempfile.TemporaryDirectory() as dest_dir:
            yield Path(source_dir), Path(dest_dir)


@pytest.fixture
async def sync_config(test_db, temp_dirs):
    """Create test sync configuration"""
    source_dir, dest_dir = temp_dirs
    
    config_data = {
        "name": "Test Sync",
        "source_path": str(source_dir),
        "destination_path": str(dest_dir),
        "enabled": True,
        "delete_after_sync": True,
        "sync_interval": 5,
        "max_retries": 3,
        "retry_delay": 1,
        "batch_size": 10
    }
    
    config = await DatabaseManager.create_sync_config(test_db, config_data)
    yield config
    
    # Cleanup
    await DatabaseManager.delete_sync_config(test_db, config.id)


@pytest.fixture
async def sync_manager():
    """Create sync manager instance"""
    manager = SyncManager()
    yield manager
    
    # Cleanup
    if manager.is_running:
        await manager.stop()


# ==================== Database Tests ====================

class TestDatabase:
    
    @pytest.mark.asyncio
    async def test_create_sync_config(self, test_db, temp_dirs):
        """Test creating sync configuration"""
        source_dir, dest_dir = temp_dirs
        
        config_data = {
            "name": "Test Config",
            "source_path": str(source_dir),
            "destination_path": str(dest_dir),
            "enabled": True,
            "delete_after_sync": False,
            "sync_interval": 10
        }
        
        config = await DatabaseManager.create_sync_config(test_db, config_data)
        
        assert config.id is not None
        assert config.name == "Test Config"
        assert config.source_path == str(source_dir)
        assert config.destination_path == str(dest_dir)
        assert config.enabled is True
        assert config.delete_after_sync is False
    
    @pytest.mark.asyncio
    async def test_get_sync_config(self, test_db, sync_config):
        """Test retrieving sync configuration"""
        config = await DatabaseManager.get_sync_config(test_db, sync_config.id)
        
        assert config is not None
        assert config.id == sync_config.id
        assert config.name == sync_config.name
    
    @pytest.mark.asyncio
    async def test_update_sync_config(self, test_db, sync_config):
        """Test updating sync configuration"""
        update_data = {
            "name": "Updated Name",
            "sync_interval": 30,
            "enabled": False
        }
        
        updated = await DatabaseManager.update_sync_config(
            test_db, sync_config.id, update_data
        )
        
        assert updated.name == "Updated Name"
        assert updated.sync_interval == 30
        assert updated.enabled is False
    
    @pytest.mark.asyncio
    async def test_delete_sync_config(self, test_db, temp_dirs):
        """Test deleting sync configuration"""
        source_dir, dest_dir = temp_dirs
        
        config = await DatabaseManager.create_sync_config(test_db, {
            "name": "To Delete",
            "source_path": str(source_dir),
            "destination_path": str(dest_dir)
        })
        
        deleted = await DatabaseManager.delete_sync_config(test_db, config.id)
        assert deleted is True
        
        # Verify deletion
        config = await DatabaseManager.get_sync_config(test_db, config.id)
        assert config is None
    
    @pytest.mark.asyncio
    async def test_add_sync_file(self, test_db, sync_config):
        """Test adding file to sync queue"""
        file_data = {
            "file_path": "/test/file.txt",
            "file_name": "file.txt",
            "file_size": 1024,
            "status": FileStatus.PENDING
        }
        
        file = await DatabaseManager.add_sync_file(
            test_db, sync_config.id, file_data
        )
        
        assert file.id is not None
        assert file.file_path == "/test/file.txt"
        assert file.file_size == 1024
        assert file.status == FileStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_get_pending_files(self, test_db, sync_config):
        """Test retrieving pending files"""
        # Add multiple files
        for i in range(5):
            await DatabaseManager.add_sync_file(test_db, sync_config.id, {
                "file_path": f"/test/file{i}.txt",
                "file_name": f"file{i}.txt",
                "file_size": 100 * i,
                "status": FileStatus.PENDING
            })
        
        # Get pending files
        files = await DatabaseManager.get_pending_files(test_db, sync_config.id, limit=3)
        
        assert len(files) == 3
        assert all(f.status == FileStatus.PENDING for f in files)


# ==================== Sync Worker Tests ====================

class TestSyncWorker:
    
    @pytest.mark.asyncio
    async def test_sync_file_success(self, sync_config, temp_dirs):
        """Test successful file sync"""
        source_dir, dest_dir = temp_dirs
        
        # Create test file
        test_file = source_dir / "test.txt"
        test_file.write_text("test content")
        
        # Create worker
        worker = SyncWorker(sync_config)
        
        # Sync file
        result = await worker.sync_file(str(test_file))
        
        assert result is True
        
        # Check destination
        dest_file = dest_dir / "test.txt"
        assert dest_file.exists()
        assert dest_file.read_text() == "test content"
        
        # Check source was deleted (if delete_after_sync is True)
        if sync_config.delete_after_sync:
            assert not test_file.exists()
    
    @pytest.mark.asyncio
    async def test_sync_file_with_subdirectory(self, sync_config, temp_dirs):
        """Test syncing file in subdirectory"""
        source_dir, dest_dir = temp_dirs
        
        # Create subdirectory and file
        sub_dir = source_dir / "subdir"
        sub_dir.mkdir()
        test_file = sub_dir / "test.txt"
        test_file.write_text("subdirectory content")
        
        # Update config paths
        sync_config.source_path = str(source_dir)
        sync_config.destination_path = str(dest_dir)
        
        # Create worker
        worker = SyncWorker(sync_config)
        
        # Sync file
        result = await worker.sync_file(str(test_file))
        
        assert result is True
        
        # Check destination
        dest_file = dest_dir / "subdir" / "test.txt"
        assert dest_file.exists()
        assert dest_file.read_text() == "subdirectory content"
    
    @pytest.mark.asyncio
    async def test_sync_file_nonexistent(self, sync_config):
        """Test syncing non-existent file"""
        worker = SyncWorker(sync_config)
        
        result = await worker.sync_file("/nonexistent/file.txt")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_file_patterns(self, sync_config, temp_dirs):
        """Test file pattern matching"""
        source_dir, dest_dir = temp_dirs
        
        # Set patterns
        sync_config.include_patterns = ["*.txt"]
        sync_config.exclude_patterns = ["*.tmp"]
        
        worker = SyncWorker(sync_config)
        
        # Create test files
        txt_file = source_dir / "test.txt"
        tmp_file = source_dir / "test.tmp"
        doc_file = source_dir / "test.doc"
        
        for f in [txt_file, tmp_file, doc_file]:
            f.write_text("content")
        
        # Test pattern matching
        assert worker._should_sync_file(txt_file) is True  # Included
        assert worker._should_sync_file(tmp_file) is False  # Excluded
        assert worker._should_sync_file(doc_file) is False  # Not included


# ==================== Sync Manager Tests ====================

class TestSyncManager:
    
    @pytest.mark.asyncio
    async def test_start_stop(self, sync_manager):
        """Test starting and stopping sync manager"""
        await sync_manager.start()
        assert sync_manager.is_running is True
        
        await sync_manager.stop()
        assert sync_manager.is_running is False
    
    @pytest.mark.asyncio
    async def test_start_sync(self, sync_manager, sync_config, test_db):
        """Test starting individual sync"""
        await sync_manager.start()
        
        await sync_manager.start_sync(sync_config.id)
        
        assert sync_config.id in sync_manager.sync_workers
        assert sync_config.id in sync_manager.file_queues
        
        # Cleanup
        await sync_manager.stop_sync(sync_config.id)
    
    @pytest.mark.asyncio
    async def test_stop_sync(self, sync_manager, sync_config, test_db):
        """Test stopping individual sync"""
        await sync_manager.start()
        await sync_manager.start_sync(sync_config.id)
        
        await sync_manager.stop_sync(sync_config.id)
        
        assert sync_config.id not in sync_manager.sync_workers
        assert sync_config.id not in sync_manager.file_queues
    
    @pytest.mark.asyncio
    async def test_get_sync_status(self, sync_manager, sync_config, test_db):
        """Test getting sync status"""
        await sync_manager.start()
        await sync_manager.start_sync(sync_config.id)
        
        status = await sync_manager.get_sync_status(sync_config.id)
        
        assert status is not None
        assert status['id'] == sync_config.id
        assert status['name'] == sync_config.name
        assert status['is_running'] is True
        
        # Cleanup
        await sync_manager.stop_sync(sync_config.id)
    
    @pytest.mark.asyncio
    async def test_force_sync(self, sync_manager, sync_config, test_db, temp_dirs):
        """Test force sync"""
        source_dir, dest_dir = temp_dirs
        
        # Create test files
        for i in range(3):
            file = source_dir / f"test{i}.txt"
            file.write_text(f"content {i}")
            
            # Add to database as pending
            await DatabaseManager.add_sync_file(test_db, sync_config.id, {
                "file_path": str(file),
                "file_name": file.name,
                "file_size": file.stat().st_size,
                "status": FileStatus.PENDING
            })
        
        await sync_manager.start()
        await sync_manager.start_sync(sync_config.id)
        
        # Force sync
        await sync_manager.force_sync(sync_config.id)
        
        # Wait a bit for processing
        await asyncio.sleep(1)
        
        # Check files were synced
        for i in range(3):
            dest_file = dest_dir / f"test{i}.txt"
            assert dest_file.exists()
            assert dest_file.read_text() == f"content {i}"
        
        # Cleanup
        await sync_manager.stop_sync(sync_config.id)


# ==================== API Tests ====================

class TestAPI:
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test health check endpoint"""
        from httpx import AsyncClient
        from main import app
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data
    
    @pytest.mark.asyncio
    async def test_create_sync_endpoint(self, temp_dirs):
        """Test create sync endpoint"""
        from httpx import AsyncClient
        from main import app
        
        source_dir, dest_dir = temp_dirs
        
        sync_data = {
            "name": "API Test Sync",
            "source_path": str(source_dir),
            "destination_path": str(dest_dir),
            "enabled": False
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/v1/syncs", json=sync_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "API Test Sync"
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_list_syncs_endpoint(self):
        """Test list syncs endpoint"""
        from httpx import AsyncClient
        from main import app
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/syncs")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


# ==================== Utility Tests ====================

class TestUtilities:
    
    def test_calculate_file_hash(self, tmp_path):
        """Test file hash calculation"""
        from app.utils.file_utils import calculate_file_hash
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        hash1 = calculate_file_hash(test_file)
        assert len(hash1) == 64  # SHA256 hash length
        
        # Same content should produce same hash
        hash2 = calculate_file_hash(test_file)
        assert hash1 == hash2
        
        # Different content should produce different hash
        test_file.write_text("different content")
        hash3 = calculate_file_hash(test_file)
        assert hash1 != hash3
    
    def test_file_pattern_matching(self):
        """Test file pattern matching"""
        from app.utils.file_utils import is_file_match_patterns
        
        # Test include patterns
        assert is_file_match_patterns(
            "/test/file.txt",
            include_patterns=["*.txt"],
            exclude_patterns=[]
        ) is True
        
        assert is_file_match_patterns(
            "/test/file.doc",
            include_patterns=["*.txt"],
            exclude_patterns=[]
        ) is False
        
        # Test exclude patterns
        assert is_file_match_patterns(
            "/test/file.tmp",
            include_patterns=[],
            exclude_patterns=["*.tmp"]
        ) is False
        
        # Test both include and exclude
        assert is_file_match_patterns(
            "/test/file.txt",
            include_patterns=["*.txt", "*.doc"],
            exclude_patterns=["test*"]
        ) is False  # Excluded even though included
    
    def test_format_bytes(self):
        """Test byte formatting"""
        from app.utils.file_utils import format_bytes
        
        assert format_bytes(512) == "512.00 B"
        assert format_bytes(1024) == "1.00 KB"
        assert format_bytes(1048576) == "1.00 MB"
        assert format_bytes(1073741824) == "1.00 GB"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
