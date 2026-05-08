"""SQLite backup utility tests."""
import shutil
import sqlite3
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cno.app import app
from cno.audit import AuditLog


client = TestClient(app)


@pytest.fixture
def tmp_dir():
    d = Path(tempfile.mkdtemp(prefix="cno_backup_test_"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_audit_backup_writes_a_valid_sqlite_file(tmp_dir):
    src = tmp_dir / "src.db"
    audit = AuditLog(db_path=src)

    audit.record_run_header(
        run_id="r1", request="hello", modality="text", request_type="question",
        tone="neutral", sublayer="Analytical Layer", persona_style="technical",
        clarity_score=99, synthesis_body="ok", total_ms=12,
    )
    audit.record_node_crossing("r1", 1, "input", {}, {"ok": True})

    dest = tmp_dir / "snapshots" / "snap.db"
    out = audit.backup(dest)
    assert out == dest
    assert dest.exists() and dest.stat().st_size > 0

    # Snapshot must be a valid SQLite DB with the expected rows
    with sqlite3.connect(dest) as conn:
        run_count = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
        log_count = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    assert run_count == 1
    assert log_count == 1


def test_backup_creates_parent_directory(tmp_dir):
    audit = AuditLog(db_path=tmp_dir / "src.db")
    nested = tmp_dir / "deep" / "nested" / "snap.db"
    audit.backup(nested)
    assert nested.exists()


def test_backup_endpoint_returns_path_and_size():
    # uses the singleton PIPELINE.audit (test DB lives in /tmp from conftest)
    client.post("/cno/process", json={"request": "seed for backup"})
    r = client.post("/cno/audit/backup")
    assert r.status_code == 200
    body = r.json()
    assert "backup_path" in body
    assert body["size_bytes"] > 0
    assert Path(body["backup_path"]).exists()
    # cleanup is best-effort — Windows can hold the handle briefly
    try:
        Path(body["backup_path"]).unlink()
    except (PermissionError, FileNotFoundError):
        pass


def test_backup_endpoint_honors_custom_dest(tmp_dir):
    client.post("/cno/process", json={"request": "seed for backup-2"})
    target = tmp_dir / "explicit.db"
    r = client.post(f"/cno/audit/backup?dest={target}")
    assert r.status_code == 200
    assert Path(r.json()["backup_path"]).resolve() == target.resolve()
    assert target.exists()
