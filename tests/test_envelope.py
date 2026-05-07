"""CSTM §6 session-state envelope tests."""
import json

from fastapi.testclient import TestClient

from cno.app import app
from cno.envelope import REGISTRY


client = TestClient(app)


def _post(prompt: str, session: str | None = None) -> dict:
    headers = {"X-CNO-Session-Id": session} if session else {}
    r = client.post("/cno/process", json={"request": prompt}, headers=headers)
    assert r.status_code == 200
    return r.json()


def test_envelope_has_required_fields():
    env = _post("hello")
    for field in ("session_id", "envelope_version", "spec_ref", "run_id",
                  "ts", "glyph_pipeline", "prior_run_ids", "payload", "spec_gaps"):
        assert field in env, f"missing: {field}"
    assert env["envelope_version"] == "1.0"
    assert env["spec_ref"].startswith("CSTM_Lattice")


def test_envelope_mints_session_id_when_header_absent():
    env = _post("first")
    assert env["session_id"] and len(env["session_id"]) >= 16
    assert env["prior_run_ids"] == []


def test_envelope_honors_supplied_session_and_chains_runs():
    sid = "test-session-aaa"
    e1 = _post("first run",  session=sid)
    e2 = _post("second run", session=sid)
    e3 = _post("third run",  session=sid)
    assert e1["session_id"] == sid == e2["session_id"] == e3["session_id"]
    assert e1["prior_run_ids"] == []
    assert e2["prior_run_ids"] == [e1["run_id"]]
    assert e3["prior_run_ids"] == [e1["run_id"], e2["run_id"]]


def test_envelope_separates_distinct_sessions():
    a = _post("from a", session="sess-A")
    b = _post("from b", session="sess-B")
    assert a["prior_run_ids"] == []
    assert b["prior_run_ids"] == []
    assert a["session_id"] != b["session_id"]


def test_envelope_payload_carries_pipeline_body():
    env = _post("What is canon #18?")
    payload = env["payload"]
    assert payload["run_id"] == env["run_id"]
    assert payload["classification"]["request_type"] == "question"
    assert payload["routing"]["sublayer"] == "Analytical Layer"
    assert len(payload["module_tags"]) == 5


def test_envelope_in_streaming_complete_event():
    sid = "stream-session-xyz"
    with client.stream("POST", "/cno/process/stream",
                       json={"request": "stream me"},
                       headers={"X-CNO-Session-Id": sid}) as resp:
        body = b"".join(resp.iter_bytes())

    # Parse last "complete" SSE block.
    chunks = body.decode().split("\n\n")
    complete_chunk = next(c for c in chunks if "event: complete" in c)
    data_line = next(l for l in complete_chunk.splitlines() if l.startswith("data:"))
    env = json.loads(data_line[5:].strip())

    assert env["session_id"] == sid
    assert env["envelope_version"] == "1.0"
    assert env["payload"]["run_id"] == env["run_id"]
    assert env["payload"]["total_ms"] is not None


def test_session_registry_caps_history():
    REGISTRY._cap = 3  # type: ignore[attr-defined]
    sid = "capped-session"
    REGISTRY._sessions.pop(sid, None)  # type: ignore[attr-defined]
    runs = [f"run-{i}" for i in range(5)]
    for r in runs:
        REGISTRY.append_run(sid, r)
    assert REGISTRY.history(sid) == runs[-3:]
    REGISTRY._cap = 25  # restore default
