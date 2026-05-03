"""End-to-end FastAPI tests for CNO."""
from fastapi.testclient import TestClient
from cno.app import app

client = TestClient(app)


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_root_advertises_5_node_pipeline():
    r = client.get("/")
    body = r.json()
    assert body["canon"] == "#18"
    assert "📥 → 🔄 → 🧊 → 🥥 → 📤" in body["glyph_pipeline"]


def test_process_question_routes_to_analysis():
    r = client.post("/cno/process", json={"request": "What is the meaning of canon #18?"})
    assert r.status_code == 200
    body = r.json()
    assert body["classification"]["request_type"] == "question"
    assert body["routing"]["sublayer"] == "Analytical Layer"
    assert len(body["module_tags"]) == 5


def test_process_command_routes_to_output():
    r = client.post("/cno/process", json={"request": "Build the codebase now."})
    body = r.json()
    assert body["classification"]["request_type"] == "command"
    assert body["routing"]["sublayer"] == "Output Layer"


def test_state_endpoint_returns_anchors():
    client.post("/cno/state/reset")
    client.post("/cno/process", json={"request": "first request"})
    client.post("/cno/process", json={"request": "second request"})
    r = client.get("/cno/state")
    body = r.json()
    assert body["anchor_count"] == 2


def test_modality_hint_accepted():
    r = client.post("/cno/process", json={"request": "test", "modality_hint": "voice"})
    assert r.status_code == 200
    assert r.json()["classification"]["modality"] == "voice"


def test_modality_hint_invalid_returns_422():
    r = client.post("/cno/process", json={"request": "test", "modality_hint": "telepathy"})
    assert r.status_code == 422


def test_openapi_schema_includes_cno_endpoints():
    r = client.get("/openapi.json")
    paths = r.json()["paths"]
    assert "/cno/process" in paths
    assert "/cno/state" in paths
