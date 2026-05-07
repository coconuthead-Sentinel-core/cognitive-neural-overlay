"""Audit log + /cno/audit endpoint tests."""
from fastapi.testclient import TestClient

from cno.app import app
from cno.audit import AuditLog
from cno.pipeline import CNOPipeline


client = TestClient(app)


def test_pipeline_writes_run_header_and_5_crossings():
    audit = AuditLog()
    p = CNOPipeline(audit=audit)
    result = p.process("What is canon #18?")
    runs = audit.list_runs()
    assert any(r.run_id == result.run_id for r in runs)
    crossings = audit.get_crossings(result.run_id)
    assert len(crossings) == 5
    assert [c.node for c in crossings] == ["input", "router", "memory", "persona", "synth"]
    assert [c.step for c in crossings] == [1, 2, 3, 4, 5]


def test_run_header_captures_classification_summary():
    audit = AuditLog()
    p = CNOPipeline(audit=audit)
    result = p.process("Build the codebase now.")
    header = audit.get_run(result.run_id)
    assert header is not None
    assert header.request_type == "command"
    assert header.sublayer == "Output Layer"


def test_audit_endpoint_lists_recent_runs():
    client.post("/cno/process", json={"request": "first audited"})
    client.post("/cno/process", json={"request": "second audited"})
    r = client.get("/cno/audit?limit=10")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 2
    assert "run_id" in body["runs"][0]


def test_audit_drill_down_returns_5_crossings():
    r = client.post("/cno/process", json={"request": "drill me down"})
    run_id = r.json()["run_id"]
    detail = client.get(f"/cno/audit/{run_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["header"]["run_id"] == run_id
    assert len(body["crossings"]) == 5
    assert body["crossings"][0]["glyph"] == "📥"
    assert body["crossings"][-1]["glyph"] == "📤"


def test_audit_drill_down_404_for_unknown_run():
    r = client.get("/cno/audit/does-not-exist")
    assert r.status_code == 404


def test_pipeline_without_audit_still_works():
    """audit=None should be valid (e.g., unit-test mode)."""
    p = CNOPipeline(audit=None)
    result = p.process("no audit attached")
    assert result.run_id
    assert len(result.module_tags) == 5
