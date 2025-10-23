#!/usr/bin/env python3
"""
Sync Manager - Main Application Entry Point
"""

import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import router as api_router
from app.core.config import settings
from app.core.database import init_db
from app.core.logging import setup_logging
from app.core.sync_manager import SyncManager
from app.websocket import websocket_endpoint

# Setup logging
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Global sync manager instance
sync_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global sync_manager
    
    logger.info("Starting Sync Manager Service...")
    
    # Initialize database
    await init_db()
    
    # Initialize sync manager
    sync_manager = SyncManager()
    await sync_manager.start()
    
    # Set sync manager in app state
    app.state.sync_manager = sync_manager
    
    logger.info(f"Sync Manager started on {settings.HOST}:{settings.PORT}")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Sync Manager...")
    if sync_manager:
        await sync_manager.stop()
    logger.info("Sync Manager stopped")


# Create FastAPI app
app = FastAPI(
    title="Sync Manager",
    description="Advanced file synchronization service with REST API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Add WebSocket endpoint
app.add_api_websocket_route("/ws", websocket_endpoint)

# Serve static files for web dashboard (if exists)
static_dir = Path("static")
if static_dir.exists():
    app.mount("/", StaticFiles(directory="static", html=True), name="static")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    sys.exit(0)


def main():
    """Main entry point"""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run server
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=settings.ACCESS_LOG,
    )


if __name__ == "__main__":
    main()
