"""
Sync Manager - Core synchronization engine
"""

import asyncio
import hashlib
import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
import aiofiles
import psutil

from app.core.config import settings
from app.core.database import (
    AsyncSessionLocal, DatabaseManager,
    SyncConfiguration, SyncFile, SyncStatus, FileStatus
)
from app.core.exceptions import SyncException
from app.utils.file_utils import (
    calculate_file_hash, is_file_match_patterns, get_file_size
)


logger = logging.getLogger(__name__)


class FileEventHandler(FileSystemEventHandler):
    """Handle file system events"""
    
    def __init__(self, sync_id: int, queue: asyncio.Queue):
        self.sync_id = sync_id
        self.queue = queue
        self.processed_files: Set[str] = set()
        
    def on_created(self, event: FileSystemEvent):
        if not event.is_directory:
            asyncio.create_task(self._add_to_queue(event.src_path, "created"))
    
    def on_modified(self, event: FileSystemEvent):
        if not event.is_directory:
            asyncio.create_task(self._add_to_queue(event.src_path, "modified"))
    
    def on_moved(self, event: FileSystemEvent):
        if not event.is_directory:
            asyncio.create_task(self._add_to_queue(event.dest_path, "moved"))
    
    async def _add_to_queue(self, file_path: str, event_type: str):
        """Add file to processing queue"""
        # Avoid duplicate processing
        if file_path not in self.processed_files:
            self.processed_files.add(file_path)
            await self.queue.put({
                "sync_id": self.sync_id,
                "file_path": file_path,
                "event_type": event_type,
                "timestamp": datetime.utcnow()
            })
            # Remove from processed after delay
            await asyncio.sleep(settings.FILE_WATCH_DELAY)
            self.processed_files.discard(file_path)


class SyncWorker:
    """Worker for handling individual sync operations"""
    
    def __init__(self, sync_config: SyncConfiguration):
        self.config = sync_config
        self.is_running = False
        self.retry_queue: List[Dict] = []
        self.stats = {
            "files_synced": 0,
            "bytes_synced": 0,
            "errors": 0,
            "start_time": None
        }
    
    async def sync_file(self, file_path: str) -> bool:
        """Sync a single file"""
        try:
            source = Path(file_path)
            if not source.exists():
                logger.warning(f"File no longer exists: {file_path}")
                return False
            
            # Check file patterns
            if not self._should_sync_file(source):
                logger.debug(f"File excluded by patterns: {file_path}")
                return False
            
            # Calculate destination path
            rel_path = source.relative_to(self.config.source_path)
            dest_path = Path(self.config.destination_path) / rel_path
            
            # Create destination directory
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check network/destination availability
            if not self._is_destination_available():
                raise SyncException(f"Destination not available: {self.config.destination_path}")
            
            # Copy file
            file_size = source.stat().st_size
            await self._copy_file(source, dest_path)
            
            # Verify copy
            if self._verify_copy(source, dest_path):
                # Delete source if configured
                if self.config.delete_after_sync:
                    source.unlink()
                    logger.info(f"File synced and deleted: {file_path}")
                else:
                    logger.info(f"File synced: {file_path}")
                
                # Update stats
                self.stats["files_synced"] += 1
                self.stats["bytes_synced"] += file_size
                
                return True
            else:
                raise SyncException("File verification failed")
                
        except Exception as e:
            logger.error(f"Error syncing file {file_path}: {e}")
            self.stats["errors"] += 1
            raise
    
    async def _copy_file(self, source: Path, destination: Path):
        """Copy file with progress tracking"""
        chunk_size = settings.CHUNK_SIZE
        
        async with aiofiles.open(source, 'rb') as src:
            async with aiofiles.open(destination, 'wb') as dst:
                while chunk := await src.read(chunk_size):
                    await dst.write(chunk)
    
    def _verify_copy(self, source: Path, destination: Path) -> bool:
        """Verify file was copied correctly"""
        if not destination.exists():
            return False
        
        # Compare size
        if source.stat().st_size != destination.stat().st_size:
            return False
        
        # Optional: Compare hash (can be slow for large files)
        if self.config.source_type == "local" and source.stat().st_size < 100 * 1024 * 1024:  # 100MB
            src_hash = calculate_file_hash(source)
            dst_hash = calculate_file_hash(destination)
            return src_hash == dst_hash
        
        return True
    
    def _should_sync_file(self, file_path: Path) -> bool:
        """Check if file should be synced based on patterns and size"""
        # Check size limits
        file_size = file_path.stat().st_size
        if self.config.min_file_size and file_size < self.config.min_file_size:
            return False
        if self.config.max_file_size and file_size > self.config.max_file_size:
            return False
        
        # Check patterns
        return is_file_match_patterns(
            str(file_path),
            self.config.include_patterns or [],
            self.config.exclude_patterns or []
        )
    
    def _is_destination_available(self) -> bool:
        """Check if destination is available"""
        dest_path = Path(self.config.destination_path)
        
        # For local/network paths
        if self.config.destination_type in ["local", "network"]:
            try:
                # Try to write a test file
                test_file = dest_path / ".sync_test"
                test_file.touch()
                test_file.unlink()
                return True
            except:
                return False
        
        # For cloud storage, implement specific checks
        # TODO: Implement cloud storage availability checks
        
        return True
    
    async def process_batch(self, files: List[SyncFile]):
        """Process a batch of files"""
        for file in files:
            try:
                success = await self.sync_file(file.file_path)
                if success:
                    async with AsyncSessionLocal() as session:
                        await DatabaseManager.update_file_status(
                            session, file.id, FileStatus.SYNCED
                        )
            except Exception as e:
                file.retry_count += 1
                if file.retry_count < self.config.max_retries:
                    # Add to retry queue
                    self.retry_queue.append({
                        "file": file,
                        "retry_at": datetime.utcnow() + timedelta(seconds=self.config.retry_delay)
                    })
                else:
                    # Mark as failed
                    async with AsyncSessionLocal() as session:
                        await DatabaseManager.update_file_status(
                            session, file.id, FileStatus.FAILED, str(e)
                        )
    
    async def process_retries(self):
        """Process files in retry queue"""
        current_time = datetime.utcnow()
        retries_to_process = []
        
        # Get files ready for retry
        self.retry_queue = [
            r for r in self.retry_queue
            if r["retry_at"] > current_time or retries_to_process.append(r["file"])
        ]
        
        # Process retries
        if retries_to_process:
            await self.process_batch(retries_to_process)


class SyncManager:
    """Main sync manager controlling all sync operations"""
    
    def __init__(self):
        self.sync_workers: Dict[int, SyncWorker] = {}
        self.observers: Dict[int, Observer] = {}
        self.file_queues: Dict[int, asyncio.Queue] = {}
        self.tasks: Dict[int, List[asyncio.Task]] = {}
        self.is_running = False
        self.metrics_task = None
    
    async def start(self):
        """Start sync manager"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting Sync Manager...")
        
        # Load and start enabled syncs
        async with AsyncSessionLocal() as session:
            configs = await DatabaseManager.get_all_sync_configs(session, enabled_only=True)
            for config in configs:
                await self.start_sync(config.id)
        
        # Start metrics collection
        self.metrics_task = asyncio.create_task(self._collect_metrics())
        
        logger.info(f"Sync Manager started with {len(self.sync_workers)} active syncs")
    
    async def stop(self):
        """Stop sync manager"""
        if not self.is_running:
            return
        
        logger.info("Stopping Sync Manager...")
        
        # Stop all syncs
        for sync_id in list(self.sync_workers.keys()):
            await self.stop_sync(sync_id)
        
        # Cancel metrics task
        if self.metrics_task:
            self.metrics_task.cancel()
            try:
                await self.metrics_task
            except asyncio.CancelledError:
                pass
        
        self.is_running = False
        logger.info("Sync Manager stopped")
    
    async def start_sync(self, sync_id: int):
        """Start a specific sync"""
        if sync_id in self.sync_workers:
            logger.warning(f"Sync {sync_id} is already running")
            return
        
        async with AsyncSessionLocal() as session:
            config = await DatabaseManager.get_sync_config(session, sync_id)
            if not config:
                raise SyncException(f"Sync configuration {sync_id} not found")
            
            if not config.enabled:
                logger.warning(f"Sync {sync_id} is disabled")
                return
            
            # Create worker
            worker = SyncWorker(config)
            self.sync_workers[sync_id] = worker
            
            # Create file queue
            queue = asyncio.Queue()
            self.file_queues[sync_id] = queue
            
            # Start file watcher
            if config.source_type == "local":
                self._start_file_watcher(sync_id, config.source_path)
            
            # Start processing tasks
            tasks = [
                asyncio.create_task(self._process_queue(sync_id)),
                asyncio.create_task(self._periodic_sync(sync_id)),
                asyncio.create_task(self._process_retries(sync_id))
            ]
            self.tasks[sync_id] = tasks
            
            # Update status
            await DatabaseManager.update_sync_config(
                session, sync_id, {"status": SyncStatus.RUNNING}
            )
            
            logger.info(f"Sync {sync_id} started: {config.name}")
    
    async def stop_sync(self, sync_id: int):
        """Stop a specific sync"""
        if sync_id not in self.sync_workers:
            return
        
        logger.info(f"Stopping sync {sync_id}")
        
        # Stop file watcher
        if sync_id in self.observers:
            self.observers[sync_id].stop()
            self.observers[sync_id].join()
            del self.observers[sync_id]
        
        # Cancel tasks
        if sync_id in self.tasks:
            for task in self.tasks[sync_id]:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            del self.tasks[sync_id]
        
        # Clean up
        del self.sync_workers[sync_id]
        del self.file_queues[sync_id]
        
        # Update status
        async with AsyncSessionLocal() as session:
            await DatabaseManager.update_sync_config(
                session, sync_id, {"status": SyncStatus.STOPPED}
            )
        
        logger.info(f"Sync {sync_id} stopped")
    
    async def force_sync(self, sync_id: int):
        """Force immediate sync of all pending files"""
        if sync_id not in self.sync_workers:
            raise SyncException(f"Sync {sync_id} is not running")
        
        worker = self.sync_workers[sync_id]
        
        # Get all pending files
        async with AsyncSessionLocal() as session:
            files = await DatabaseManager.get_pending_files(session, sync_id, limit=1000)
            
            # Process in batches
            for i in range(0, len(files), worker.config.batch_size):
                batch = files[i:i + worker.config.batch_size]
                await worker.process_batch(batch)
    
    def _start_file_watcher(self, sync_id: int, path: str):
        """Start file system watcher"""
        if sync_id in self.observers:
            return
        
        observer = Observer()
        handler = FileEventHandler(sync_id, self.file_queues[sync_id])
        observer.schedule(handler, path, recursive=True)
        observer.start()
        self.observers[sync_id] = observer
        
        logger.info(f"File watcher started for sync {sync_id}: {path}")
    
    async def _process_queue(self, sync_id: int):
        """Process file events from queue"""
        queue = self.file_queues[sync_id]
        worker = self.sync_workers[sync_id]
        
        while sync_id in self.sync_workers:
            try:
                # Get file event with timeout
                event = await asyncio.wait_for(queue.get(), timeout=1.0)
                
                # Process file
                file_path = event["file_path"]
                
                # Add to database
                async with AsyncSessionLocal() as session:
                    file_data = {
                        "file_path": file_path,
                        "file_name": Path(file_path).name,
                        "file_size": get_file_size(file_path),
                        "status": FileStatus.PENDING
                    }
                    file = await DatabaseManager.add_sync_file(
                        session, sync_id, file_data
                    )
                    
                    # Process immediately
                    await worker.process_batch([file])
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing queue for sync {sync_id}: {e}")
    
    async def _periodic_sync(self, sync_id: int):
        """Periodic sync for pending files"""
        worker = self.sync_workers[sync_id]
        
        while sync_id in self.sync_workers:
            try:
                await asyncio.sleep(worker.config.sync_interval)
                
                # Get pending files
                async with AsyncSessionLocal() as session:
                    files = await DatabaseManager.get_pending_files(
                        session, sync_id, limit=worker.config.batch_size
                    )
                    
                    if files:
                        await worker.process_batch(files)
                    
                    # Update next sync time
                    await DatabaseManager.update_sync_config(
                        session, sync_id, {
                            "last_sync": datetime.utcnow(),
                            "next_sync": datetime.utcnow() + timedelta(seconds=worker.config.sync_interval)
                        }
                    )
                    
            except Exception as e:
                logger.error(f"Error in periodic sync for {sync_id}: {e}")
    
    async def _process_retries(self, sync_id: int):
        """Process retry queue for failed files"""
        worker = self.sync_workers[sync_id]
        
        while sync_id in self.sync_workers:
            try:
                await asyncio.sleep(worker.config.retry_delay)
                await worker.process_retries()
            except Exception as e:
                logger.error(f"Error processing retries for sync {sync_id}: {e}")
    
    async def _collect_metrics(self):
        """Collect system metrics periodically"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Collect every minute
                
                # Collect metrics
                metrics = {
                    "active_syncs": len(self.sync_workers),
                    "total_syncs": 0,
                    "files_in_queue": sum(q.qsize() for q in self.file_queues.values()),
                    "files_synced_today": 0,
                    "bytes_synced_today": 0,
                    "cpu_usage": psutil.cpu_percent(),
                    "memory_usage": psutil.virtual_memory().percent,
                    "disk_usage": psutil.disk_usage('/').percent,
                }
                
                # Calculate today's stats
                for worker in self.sync_workers.values():
                    metrics["files_synced_today"] += worker.stats.get("files_synced", 0)
                    metrics["bytes_synced_today"] += worker.stats.get("bytes_synced", 0)
                
                # Save to database
                async with AsyncSessionLocal() as session:
                    await DatabaseManager.record_metrics(session, metrics)
                    
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
    
    async def get_sync_status(self, sync_id: int) -> Dict:
        """Get current status of a sync"""
        if sync_id not in self.sync_workers:
            async with AsyncSessionLocal() as session:
                config = await DatabaseManager.get_sync_config(session, sync_id)
                if config:
                    return {
                        "id": config.id,
                        "name": config.name,
                        "status": config.status,
                        "enabled": config.enabled,
                        "last_sync": config.last_sync,
                        "is_running": False
                    }
                return None
        
        worker = self.sync_workers[sync_id]
        queue_size = self.file_queues[sync_id].qsize()
        
        return {
            "id": sync_id,
            "name": worker.config.name,
            "status": worker.config.status,
            "is_running": True,
            "queue_size": queue_size,
            "stats": worker.stats,
            "retry_queue_size": len(worker.retry_queue),
            "last_sync": worker.config.last_sync,
            "next_sync": worker.config.next_sync
        }
    
    async def get_all_sync_status(self) -> List[Dict]:
        """Get status of all syncs"""
        statuses = []
        
        async with AsyncSessionLocal() as session:
            configs = await DatabaseManager.get_all_sync_configs(session)
            
            for config in configs:
                if config.id in self.sync_workers:
                    status = await self.get_sync_status(config.id)
                else:
                    status = {
                        "id": config.id,
                        "name": config.name,
                        "status": config.status,
                        "enabled": config.enabled,
                        "last_sync": config.last_sync,
                        "is_running": False
                    }
                statuses.append(status)
        
        return statuses
