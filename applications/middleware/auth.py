from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import traceback
from applications.utils.utils_auth import TokenData
import jwt
from datetime import datetime, timezone
import libs.lb_config as lb_config
from modules.md_database.functions.get_data_by_id import get_data_by_id
from applications.middleware.public_endpoints import PUBLIC_ENDPOINTS

def get_user(token: str):
    try:
        # Verifica se il token è un JWT valido
        payload = jwt.decode(token, lb_config.g_config["secret_key"], algorithms=["HS256"])
    except jwt.PyJWTError:
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid token"}
        )

    token_data = TokenData(**payload)

    if token_data.exp < datetime.now(timezone.utc):
        return JSONResponse(
            status_code=401, 
            content={"detail": "Token expired"}
        )

    user = get_data_by_id("user", token_data.id)

    if not user:
        return JSONResponse(
            status_code=401, 
            content={"detail": "User not found"}
        )

    user["exp"] = token_data.exp
    
    return TokenData(**user)

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable):
        # Skip authentication for specific routes
        if request.url.path in PUBLIC_ENDPOINTS or not request.url.path.startswith("/api"):
            return await call_next(request)

        try:
            # Check Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return JSONResponse(
                    status_code=401, 
                    content={"detail": "Authentication required"}
                )

            # Extract token
            try:
                scheme, token = auth_header.split()
            except ValueError as e:
                return JSONResponse(
                    status_code=401, 
                    content={"detail": "Invalid Authorization header"}
                )

            if scheme.lower() != "bearer":
                return JSONResponse(
                    status_code=401, 
                    content={"detail": "Invalid authentication scheme, expected 'Bearer'"}
                )

            user = get_user(token)

            request.state.user = user

            # Continue with request
            response = await call_next(request)
            return response

        except jwt.PyJWTError:
            return JSONResponse(
                status_code=401, 
                content={"detail": "Invalid token"}
            )
        except Exception as e:
            print(f"Unexpected error: {traceback.format_exc()}")
            return JSONResponse(
                status_code=500, 
                content={"detail": "Internal authentication error"}
            )