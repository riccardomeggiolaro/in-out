from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from typing import Callable


class NoCacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware che aggiunge header HTTP per disabilitare la cache del browser
    su file HTML, CSS e JavaScript, così i client vedono sempre la versione aggiornata.
    """

    NOCACHE_CONTENT_TYPES = ("text/html", "text/css", "application/javascript", "text/javascript")

    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)

        content_type = response.headers.get("content-type", "")

        if any(ct in content_type for ct in self.NOCACHE_CONTENT_TYPES):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response
