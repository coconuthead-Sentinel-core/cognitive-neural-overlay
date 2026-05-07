"""
Env-driven settings. Read once at import time so tests can override via env vars
in conftest before importing cno.app.

Defaults are dev-friendly: no auth, open CORS, generous rate limit. Set the
matching env vars in production.
"""
from __future__ import annotations
import os
from dataclasses import dataclass


def _csv(value: str | None) -> list[str]:
    return [v.strip() for v in (value or "").split(",") if v.strip()]


@dataclass(frozen=True)
class Settings:
    api_key:               str | None      # CNO_API_KEY — when set, X-API-Key header required
    allowed_origins:       list[str]       # CNO_ALLOWED_ORIGINS (CSV) — defaults to ["*"]
    rate_limit_per_minute: int             # CNO_RATE_LIMIT_PER_MINUTE — 0 disables
    auth_bypass_paths:     tuple[str, ...] # paths that skip auth + rate-limit (always)


def load_settings() -> Settings:
    api_key = os.environ.get("CNO_API_KEY") or None
    origins = _csv(os.environ.get("CNO_ALLOWED_ORIGINS")) or ["*"]
    try:
        rate_limit = int(os.environ.get("CNO_RATE_LIMIT_PER_MINUTE", "120"))
    except ValueError:
        rate_limit = 120
    return Settings(
        api_key=api_key,
        allowed_origins=origins,
        rate_limit_per_minute=max(0, rate_limit),
        auth_bypass_paths=("/healthz", "/", "/docs", "/redoc", "/openapi.json"),
    )


SETTINGS = load_settings()
