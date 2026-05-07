"""Per-node isolation endpoint + SSE streaming endpoint tests."""
import json
from fastapi.testclient import TestClient

from cno.app import app


client = TestClient(app)


# --- per-node isolation ---

def test_input_node_isolated():
    r = client.post("/cno/node/input", json={"request": "What is canon #18?"})
    assert r.status_code == 200
    body = r.json()
    assert body["node"] == "input"
    assert body["glyph"] == "📥"
    assert body["output"]["request_type"] == "question"


def test_router_node_isolated():
    r = client.post("/cno/node/router", json={
        "modality": "text", "request_type": "command", "tone": "directive",
    })
    assert r.status_code == 200
    assert r.json()["output"]["sublayer"] == "Output Layer"


def test_memory_node_isolated_and_state_endpoint_sees_anchor():
    r = client.post("/cno/node/memory", json={"summary": "isolated anchor", "tone": "neutral"})
    assert r.status_code == 200
    state = client.get("/cno/state").json()
    assert any(a["summary"] == "isolated anchor" for a in state["recent"])


def test_persona_node_isolated():
    r = client.post("/cno/node/persona", json={
        "classification": {"modality": "text", "request_type": "abstract", "tone": "reflective", "raw_length": 42},
        "routing":        {"sublayer": "Reflective Layer", "rationale": "test"},
    })
    assert r.status_code == 200
    assert r.json()["output"]["style"] == "visionary"


def test_synth_node_isolated():
    r = client.post("/cno/node/synth", json={
        "draft": "A clean response.", "persona_style": "technical",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["output"]["style_applied"] == "technical"
    assert 1 <= body["output"]["clarity_score"] <= 100


def test_unknown_node_returns_404():
    r = client.post("/cno/node/quantum_oracle", json={})
    assert r.status_code == 404


def test_invalid_payload_returns_422():
    r = client.post("/cno/node/router", json={"modality": "telepathy"})
    assert r.status_code == 422


# --- SSE streaming ---

def _parse_sse(body: bytes) -> list[tuple[str, dict]]:
    """Minimal SSE parser: returns list of (event_name, data_dict)."""
    events = []
    for chunk in body.decode("utf-8").split("\n\n"):
        if not chunk.strip():
            continue
        event_name = ""
        data_lines = []
        for line in chunk.split("\n"):
            if line.startswith("event:"):
                event_name = line[len("event:"):].strip()
            elif line.startswith("data:"):
                data_lines.append(line[len("data:"):].strip())
        if data_lines:
            events.append((event_name, json.loads("\n".join(data_lines))))
    return events


def test_stream_emits_start_then_5_nodes_then_complete():
    with client.stream("POST", "/cno/process/stream", json={"request": "What is canon #18?"}) as resp:
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        body = b"".join(resp.iter_bytes())
    events = _parse_sse(body)
    names = [e[0] for e in events]
    assert names[0] == "start"
    assert names[-1] == "complete"
    node_events = [e for e in events if e[0] == "node"]
    assert len(node_events) == 5
    steps = [e[1]["step"] for e in node_events]
    assert steps == [1, 2, 3, 4, 5]
    glyphs = [e[1]["glyph"] for e in node_events]
    assert glyphs == ["📥", "🔄", "🧊", "🥥", "📤"]


def test_stream_persists_run_in_audit_log():
    with client.stream("POST", "/cno/process/stream", json={"request": "stream me"}) as resp:
        body = b"".join(resp.iter_bytes())
    events = _parse_sse(body)
    run_id = next(e[1]["run_id"] for e in events if e[0] == "complete")
    detail = client.get(f"/cno/audit/{run_id}").json()
    assert detail["header"]["run_id"] == run_id
    assert len(detail["crossings"]) == 5


def test_stream_invalid_modality_returns_422():
    r = client.post("/cno/process/stream", json={"request": "x", "modality_hint": "telepathy"})
    assert r.status_code == 422
