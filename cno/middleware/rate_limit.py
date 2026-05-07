"""
Sliding-window rate limit: N requests per 60s, keyed by X-API-Key (or client IP
if no key). Disabled when limit <= 0.

In-memory only — restarts reset the counters. Fine for single-process uvicorn;
swap for Redis if you go multi-worker.
"""
from __future__ import annotations
import time
from collections import deque
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    WINDOW_SECONDS = 60.0

    def __init__(self, app, *, limit_per_minute: int, bypass_paths: tuple[str, ...]):
        super().__init__(app)
        self._limit = limit_per_minute
        self._bypass_paths = bypass_paths
        self._buckets: dict[str, deque[float]] = {}
        self._lock = Lock()

    async def dispatch(self, request: Request, call_next):
        if self._limit <= 0:
            return await call_next(request)
        if self._is_bypass(request.url.path):
            return await call_next(request)

        key = self._key(request)
        now = time.monotonic()
        if not self._allow(key, now):
            retry_after = self._retry_after(key, now)
            return JSONResponse(
                {"detail": f"rate limit: {self._limit}/min"},
                status_code=429,
                headers={"Retry-After": str(int(retry_after) + 1)},
            )
        return await call_next(request)

    def _key(self, request: Request) -> str:
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"key:{api_key}"
        client = request.client.host if request.client else "unknown"
        return f"ip:{client}"

    def _allow(self, key: str, now: float) -> bool:
        with self._lock:
            bucket = self._buckets.setdefault(key, deque())
            cutoff = now - self.WINDOW_SECONDS
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= self._limit:
                return False
            bucket.append(now)
            return True

    def _retry_after(self, key: str, now: float) -> float:
        with self._lock:
            bucket = self._buckets.get(key)
            if not bucket:
                return 0.0
            return max(0.0, bucket[0] + self.WINDOW_SECONDS - now)

    def _is_bypass(self, path: str) -> bool:
        if path in self._bypass_paths:
            return True
        return path.startswith("/ui")
