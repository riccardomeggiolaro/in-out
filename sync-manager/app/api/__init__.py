"""
API Routes for Sync Manager
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import psutil

from app.core.database import get_db, DatabaseManager
from app.schemas import (
    SyncConfigCreate, SyncConfigUpdate, SyncConfigResponse,
    SyncStatusResponse, SyncHistoryResponse, MetricsResponse,
    HealthCheckResponse, FileResponse, BatchOperationResponse
)
from app.core.sync_manager import SyncManager
from app.core.exceptions import SyncException
from app.dependencies import get_sync_manager, verify_api_key

router = APIRouter()


# ==================== Sync Configuration Endpoints ====================

@router.get("/syncs", response_model=List[SyncConfigResponse], tags=["Syncs"])
async def list_syncs(
    enabled_only: bool = Query(False, description="Filter only enabled syncs"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """List all sync configurations"""
    configs = await DatabaseManager.get_all_sync_configs(db, enabled_only)
    return configs[skip:skip + limit]


@router.post("/syncs", response_model=SyncConfigResponse, tags=["Syncs"])
async def create_sync(
    sync_config: SyncConfigCreate,
    db: AsyncSession = Depends(get_db),
    sync_manager: SyncManager = Depends(get_sync_manager),
    _: str = Depends(verify_api_key)
):
    """Create a new sync configuration"""
    try:
        # Create in database
        config = await DatabaseManager.create_sync_config(db, sync_config.dict())
        
        # Start sync if enabled
        if config.enabled:
            await sync_manager.start_sync(config.id)
        
        return config
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/syncs/{sync_id}", response_model=SyncConfigResponse, tags=["Syncs"])
async def get_sync(
    sync_id: int = Path(..., description="Sync configuration ID"),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Get a specific sync configuration"""
    config = await DatabaseManager.get_sync_config(db, sync_id)
    if not config:
        raise HTTPException(status_code=404, detail="Sync configuration not found")
    return config


@router.put("/syncs/{sync_id}", response_model=SyncConfigResponse, tags=["Syncs"])
async def update_sync(
    sync_id: int,
    sync_update: SyncConfigUpdate,
    db: AsyncSession = Depends(get_db),
    sync_manager: SyncManager = Depends(get_sync_manager),
    _: str = Depends(verify_api_key)
):
    """Update a sync configuration"""
    try:
        # Get current config
        current_config = await DatabaseManager.get_sync_config(db, sync_id)
        if not current_config:
            raise HTTPException(status_code=404, detail="Sync configuration not found")
        
        # Update in database
        update_data = sync_update.dict(exclude_unset=True)
        config = await DatabaseManager.update_sync_config(db, sync_id, update_data)
        
        # Restart sync if running and configuration changed
        if sync_id in sync_manager.sync_workers:
            await sync_manager.stop_sync(sync_id)
            if config.enabled:
                await sync_manager.start_sync(sync_id)
        elif config.enabled and not current_config.enabled:
            await sync_manager.start_sync(sync_id)
        
        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/syncs/{sync_id}", tags=["Syncs"])
async def delete_sync(
    sync_id: int,
    db: AsyncSession = Depends(get_db),
    sync_manager: SyncManager = Depends(get_sync_manager),
    _: str = Depends(verify_api_key)
):
    """Delete a sync configuration"""
    try:
        # Stop sync if running
        if sync_id in sync_manager.sync_workers:
            await sync_manager.stop_sync(sync_id)
        
        # Delete from database
        success = await DatabaseManager.delete_sync_config(db, sync_id)
        if not success:
            raise HTTPException(status_code=404, detail="Sync configuration not found")
        
        return {"message": "Sync configuration deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Sync Control Endpoints ====================

@router.post("/syncs/{sync_id}/start", response_model=SyncStatusResponse, tags=["Control"])
async def start_sync(
    sync_id: int,
    sync_manager: SyncManager = Depends(get_sync_manager),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Start a sync operation"""
    try:
        await sync_manager.start_sync(sync_id)
        status = await sync_manager.get_sync_status(sync_id)
        return status
    except SyncException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/syncs/{sync_id}/stop", response_model=SyncStatusResponse, tags=["Control"])
async def stop_sync(
    sync_id: int,
    sync_manager: SyncManager = Depends(get_sync_manager),
    _: str = Depends(verify_api_key)
):
    """Stop a sync operation"""
    try:
        await sync_manager.stop_sync(sync_id)
        status = await sync_manager.get_sync_status(sync_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/syncs/{sync_id}/force", tags=["Control"])
async def force_sync(
    sync_id: int,
    sync_manager: SyncManager = Depends(get_sync_manager),
    _: str = Depends(verify_api_key)
):
    """Force immediate sync of all pending files"""
    try:
        await sync_manager.force_sync(sync_id)
        return {"message": "Forced sync initiated", "sync_id": sync_id}
    except SyncException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/syncs/{sync_id}/pause", tags=["Control"])
async def pause_sync(
    sync_id: int,
    db: AsyncSession = Depends(get_db),
    sync_manager: SyncManager = Depends(get_sync_manager),
    _: str = Depends(verify_api_key)
):
    """Pause a sync operation"""
    if sync_id not in sync_manager.sync_workers:
        raise HTTPException(status_code=400, detail="Sync is not running")
    
    await DatabaseManager.update_sync_config(db, sync_id, {"status": "paused"})
    # Implement pause logic in sync worker
    return {"message": "Sync paused", "sync_id": sync_id}


@router.post("/syncs/{sync_id}/resume", tags=["Control"])
async def resume_sync(
    sync_id: int,
    db: AsyncSession = Depends(get_db),
    sync_manager: SyncManager = Depends(get_sync_manager),
    _: str = Depends(verify_api_key)
):
    """Resume a paused sync operation"""
    config = await DatabaseManager.get_sync_config(db, sync_id)
    if not config:
        raise HTTPException(status_code=404, detail="Sync configuration not found")
    
    if config.status != "paused":
        raise HTTPException(status_code=400, detail="Sync is not paused")
    
    await DatabaseManager.update_sync_config(db, sync_id, {"status": "running"})
    # Implement resume logic in sync worker
    return {"message": "Sync resumed", "sync_id": sync_id}


# ==================== Status and Monitoring Endpoints ====================

@router.get("/syncs/{sync_id}/status", response_model=SyncStatusResponse, tags=["Status"])
async def get_sync_status(
    sync_id: int,
    sync_manager: SyncManager = Depends(get_sync_manager),
    _: str = Depends(verify_api_key)
):
    """Get current status of a sync"""
    status = await sync_manager.get_sync_status(sync_id)
    if not status:
        raise HTTPException(status_code=404, detail="Sync configuration not found")
    return status


@router.get("/status", response_model=List[SyncStatusResponse], tags=["Status"])
async def get_all_status(
    sync_manager: SyncManager = Depends(get_sync_manager),
    _: str = Depends(verify_api_key)
):
    """Get status of all syncs"""
    return await sync_manager.get_all_sync_status()


@router.get("/syncs/{sync_id}/files", response_model=List[FileResponse], tags=["Files"])
async def get_sync_files(
    sync_id: int,
    status: Optional[str] = Query(None, description="Filter by file status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Get files in sync queue"""
    # Implementation to get files from database
    # This would need to be added to DatabaseManager
    return []


@router.get("/syncs/{sync_id}/history", response_model=List[SyncHistoryResponse], tags=["History"])
async def get_sync_history(
    sync_id: int,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Get sync operation history"""
    history = await DatabaseManager.get_sync_history(db, sync_id, limit, offset)
    return history


@router.post("/syncs/{sync_id}/retry", tags=["Files"])
async def retry_failed_files(
    sync_id: int,
    file_ids: Optional[List[int]] = Body(None, description="Specific file IDs to retry"),
    db: AsyncSession = Depends(get_db),
    sync_manager: SyncManager = Depends(get_sync_manager),
    _: str = Depends(verify_api_key)
):
    """Retry failed file syncs"""
    # Implementation to retry failed files
    return {"message": "Retry initiated", "sync_id": sync_id}


# ==================== System Endpoints ====================

@router.get("/metrics", response_model=MetricsResponse, tags=["System"])
async def get_metrics(
    db: AsyncSession = Depends(get_db),
    sync_manager: SyncManager = Depends(get_sync_manager)
):
    """Get system metrics"""
    metrics = await DatabaseManager.get_latest_metrics(db)
    
    # Add real-time metrics
    current_metrics = {
        "timestamp": datetime.utcnow(),
        "active_syncs": len(sync_manager.sync_workers),
        "total_queued_files": sum(q.qsize() for q in sync_manager.file_queues.values()),
        "cpu_usage": psutil.cpu_percent(),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
        "network_io": psutil.net_io_counters()._asdict() if hasattr(psutil.net_io_counters(), '_asdict') else {}
    }
    
    if metrics:
        current_metrics.update(metrics.__dict__)
    
    return current_metrics


@router.get("/health", response_model=HealthCheckResponse, tags=["System"])
async def health_check(
    db: AsyncSession = Depends(get_db),
    sync_manager: SyncManager = Depends(get_sync_manager)
):
    """Health check endpoint"""
    try:
        # Check database
        await db.execute("SELECT 1")
        db_healthy = True
    except:
        db_healthy = False
    
    # Check sync manager
    manager_healthy = sync_manager.is_running
    
    # Check disk space
    disk = psutil.disk_usage('/')
    disk_healthy = disk.percent < 90
    
    # Overall health
    healthy = db_healthy and manager_healthy and disk_healthy
    
    return {
        "status": "healthy" if healthy else "unhealthy",
        "timestamp": datetime.utcnow(),
        "checks": {
            "database": "healthy" if db_healthy else "unhealthy",
            "sync_manager": "healthy" if manager_healthy else "unhealthy",
            "disk_space": f"{100 - disk.percent:.1f}% free"
        },
        "version": "1.0.0"
    }


@router.get("/logs", tags=["System"])
async def get_logs(
    lines: int = Query(100, ge=1, le=1000),
    level: Optional[str] = Query(None, description="Filter by log level"),
    sync_id: Optional[int] = Query(None, description="Filter by sync ID"),
    _: str = Depends(verify_api_key)
):
    """Get application logs"""
    # Implementation to read and filter log files
    return {"logs": [], "message": "Log retrieval not yet implemented"}


@router.post("/batch", response_model=BatchOperationResponse, tags=["Batch"])
async def batch_operation(
    operation: str = Body(..., description="Operation type: start, stop, delete"),
    sync_ids: List[int] = Body(..., description="List of sync IDs"),
    db: AsyncSession = Depends(get_db),
    sync_manager: SyncManager = Depends(get_sync_manager),
    _: str = Depends(verify_api_key)
):
    """Perform batch operations on multiple syncs"""
    results = {"success": [], "failed": []}
    
    for sync_id in sync_ids:
        try:
            if operation == "start":
                await sync_manager.start_sync(sync_id)
            elif operation == "stop":
                await sync_manager.stop_sync(sync_id)
            elif operation == "delete":
                if sync_id in sync_manager.sync_workers:
                    await sync_manager.stop_sync(sync_id)
                await DatabaseManager.delete_sync_config(db, sync_id)
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            results["success"].append(sync_id)
        except Exception as e:
            results["failed"].append({"sync_id": sync_id, "error": str(e)})
    
    return {
        "operation": operation,
        "total": len(sync_ids),
        "success_count": len(results["success"]),
        "failed_count": len(results["failed"]),
        "results": results
    }
