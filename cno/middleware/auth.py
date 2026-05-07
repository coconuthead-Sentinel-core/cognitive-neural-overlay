"""
X-API-Key header check. Disabled when CNO_API_KEY is unset (dev default).

Bypass list (always allowed): /healthz, /, /docs, /redoc, /openapi.json, /ui*.
"""
from __future__ import annotations
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class APIKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, api_key: str | None, bypass_paths: tuple[str, ...]):
        super().__init__(app)
        self._api_key = api_key
        self._bypass_paths = bypass_paths

    async def dispatch(self, request: Request, call_next):
        if self._api_key is None:
            return await call_next(request)
        if self._is_bypass(request.url.path):
            return await call_next(request)
        if request.headers.get("X-API-Key") != self._api_key:
            return JSONResponse(
                {"detail": "missing or invalid X-API-Key"},
                status_code=401,
            )
        return await call_next(request)

    def _is_bypass(self, path: str) -> bool:
        if path in self._bypass_paths:
            return True
        return path.startswith("/ui")
