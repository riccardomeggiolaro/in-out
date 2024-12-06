from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import traceback
from applications.utils.utils_auth import TokenData, is_admin
import jwt
from datetime import datetime

class AdminMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, secret_key: str):
        super().__init__(app)
        self.secret_key = secret_key
        self.algorithm = "HS256"

    async def dispatch(self, request: Request, call_next: Callable):
        try:
            if request.state.user.level in is_admin:
                return await call_next(request)

            return JSONResponse(
                status_code=401, 
                content={"detail": "You are not authorized to perform this action, you are not an admin"}
            )

            # Continue with request
            response = await call_next(request)
            return response
        except Exception as e:
            print(f"Unexpected error: {traceback.format_exc()}")
            return JSONResponse(
                status_code=500, 
                content={"detail": "Internal authentication error"}
            )