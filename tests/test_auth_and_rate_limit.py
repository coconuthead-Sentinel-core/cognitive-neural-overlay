"""Auth + rate-limit middleware tests, exercised against fresh app instances."""
from fastapi import FastAPI
from fastapi.testclient import TestClient

from cno.middleware import APIKeyMiddleware, RateLimitMiddleware


BYPASS = ("/healthz", "/")


def _make_app(*, api_key: str | None = None, rate_limit: int = 0) -> FastAPI:
    app = FastAPI()

    @app.get("/healthz")
    def health(): return {"ok": True}

    @app.get("/protected")
    def protected(): return {"ok": True}

    # Order matches cno.app: rate_limit added first (innermost),
    # auth added second (wraps rate_limit).
    app.add_middleware(RateLimitMiddleware, limit_per_minute=rate_limit, bypass_paths=BYPASS)
    app.add_middleware(APIKeyMiddleware,    api_key=api_key,             bypass_paths=BYPASS)
    return app


# --- auth ---

def test_auth_off_by_default_when_no_key():
    client = TestClient(_make_app(api_key=None))
    assert client.get("/protected").status_code == 200


def test_auth_on_rejects_missing_key():
    client = TestClient(_make_app(api_key="sekrit"))
    assert client.get("/protected").status_code == 401


def test_auth_on_rejects_wrong_key():
    client = TestClient(_make_app(api_key="sekrit"))
    r = client.get("/protected", headers={"X-API-Key": "wrong"})
    assert r.status_code == 401


def test_auth_on_accepts_correct_key():
    client = TestClient(_make_app(api_key="sekrit"))
    r = client.get("/protected", headers={"X-API-Key": "sekrit"})
    assert r.status_code == 200


def test_healthz_bypasses_auth():
    client = TestClient(_make_app(api_key="sekrit"))
    assert client.get("/healthz").status_code == 200


# --- rate limit ---

def test_rate_limit_disabled_when_zero():
    client = TestClient(_make_app(rate_limit=0))
    for _ in range(50):
        assert client.get("/protected").status_code == 200


def test_rate_limit_enforced_after_threshold():
    client = TestClient(_make_app(rate_limit=3))
    # First 3 OK, 4th blocked.
    assert client.get("/protected").status_code == 200
    assert client.get("/protected").status_code == 200
    assert client.get("/protected").status_code == 200
    r = client.get("/protected")
    assert r.status_code == 429
    assert "Retry-After" in r.headers


def test_rate_limit_keyed_per_api_key():
    client = TestClient(_make_app(api_key="root", rate_limit=2))
    # 'root' uses 2/2; subsequent must 429.
    assert client.get("/protected", headers={"X-API-Key": "root"}).status_code == 200
    assert client.get("/protected", headers={"X-API-Key": "root"}).status_code == 200
    r = client.get("/protected", headers={"X-API-Key": "root"})
    assert r.status_code == 429


def test_rate_limit_bypasses_healthz():
    client = TestClient(_make_app(rate_limit=2))
    for _ in range(10):
        assert client.get("/healthz").status_code == 200
