"""GET /cno/audit/stats + total_ms persistence tests."""
from fastapi.testclient import TestClient

from cno.app import app
from cno.pipeline import PIPELINE


client = TestClient(app)


def _run(prompt: str) -> str:
    """Submit through the batch pipeline; return run_id."""
    r = client.post("/cno/process", json={"request": prompt})
    assert r.status_code == 200
    return r.json()["run_id"]


def test_total_ms_persisted_on_batch_pipeline():
    run_id = _run("How long did this take?")
    detail = client.get(f"/cno/audit/{run_id}").json()
    assert detail["header"]["total_ms"] is not None
    assert detail["header"]["total_ms"] >= 0


def test_total_ms_persisted_on_streaming_pipeline():
    with client.stream("POST", "/cno/process/stream", json={"request": "stream timing"}) as resp:
        body = b"".join(resp.iter_bytes())
    # crude SSE parse: pull last JSON blob
    lines = body.decode().splitlines()
    run_id = next(l for l in lines if "complete" in l or "run_id" in l)
    # easier: just hit list endpoint
    runs = client.get("/cno/audit?limit=1").json()["runs"]
    assert runs[0]["total_ms"] is not None
    assert runs[0]["request"] == "stream timing"
    _ = run_id  # silence unused


def test_stats_endpoint_empty_when_no_runs():
    if PIPELINE.audit:
        PIPELINE.audit.reset()
    r = client.get("/cno/audit/stats")
    assert r.status_code == 200
    body = r.json()
    assert body["total_runs"] == 0
    assert body["latency_series"] == []
    assert body["sublayer_distribution"] == []


def test_stats_endpoint_aggregates_runs():
    _run("What is canon #18?")            # question -> Analytical, technical
    _run("Build the codebase now.")        # command -> Output, direct
    _run("Reflect on the deeper meaning.") # reflective -> Reflective, visionary
    _run("Another question?")              # question -> Analytical
    body = client.get("/cno/audit/stats?window=10").json()

    assert body["total_runs"] == 4
    assert body["window_size_actual"] == 4
    assert len(body["latency_series"]) == 4
    assert len(body["clarity_series"]) == 4

    sublayers = {row["sublayer"]: row["count"] for row in body["sublayer_distribution"]}
    assert sublayers.get("Analytical Layer") == 2
    assert sublayers.get("Output Layer") == 1
    assert sublayers.get("Reflective Layer") == 1

    matrix = body["persona_modality_matrix"]
    assert all({"modality", "persona_style", "count"} <= cell.keys() for cell in matrix)
    assert sum(c["count"] for c in matrix) == 4


def test_stats_window_caps_recent_set():
    for i in range(6):
        _run(f"prompt {i}")
    body = client.get("/cno/audit/stats?window=3").json()
    assert body["total_runs"] == 6
    assert body["window_size_actual"] == 3
    assert len(body["latency_series"]) == 3


def test_stats_endpoint_invalid_window_returns_422():
    assert client.get("/cno/audit/stats?window=0").status_code == 422
    assert client.get("/cno/audit/stats?window=99999").status_code == 422
