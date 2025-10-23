"""
FastAPI dependencies for Sync Manager
"""

from typing import Optional

from fastapi import Depends, HTTPException, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.sync_manager import SyncManager


# Security
security = HTTPBearer(auto_error=False)


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    x_api_key: Optional[str] = Header(None)
) -> str:
    """Verify API key if enabled"""
    if not settings.API_KEY_ENABLED:
        return "no-auth"
    
    # Check Bearer token
    if credentials and credentials.credentials == settings.API_KEY:
        return credentials.credentials
    
    # Check X-API-Key header
    if x_api_key == settings.API_KEY:
        return x_api_key
    
    raise HTTPException(
        status_code=401,
        detail="Invalid or missing API key",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_sync_manager(request: Request) -> SyncManager:
    """Get sync manager instance from app state"""
    if not hasattr(request.app.state, 'sync_manager'):
        raise HTTPException(
            status_code=500,
            detail="Sync manager not initialized"
        )
    return request.app.state.sync_manager


async def check_rate_limit(request: Request) -> bool:
    """Check rate limiting (placeholder)"""
    # TODO: Implement rate limiting
    return True


async def get_current_user(token: str = Depends(verify_api_key)) -> dict:
    """Get current user from token (placeholder)"""
    # TODO: Implement user authentication
    return {"username": "admin", "token": token}
