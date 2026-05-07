"""
SQLite persistence for CNO audit log.

Two tables:
  runs       — one row per /cno/process call (header summary)
  audit_log  — one row per node crossing within a run (5 rows per run)

Connection-per-call pattern: SQLite opens fast, no pool needed at this volume.
"""
from __future__ import annotations
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path


DEFAULT_DB_PATH = Path(os.environ.get("CNO_DB_PATH", "cno_audit.db"))


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id          TEXT PRIMARY KEY,
    ts              TEXT NOT NULL,
    request         TEXT NOT NULL,
    modality        TEXT,
    request_type    TEXT,
    tone            TEXT,
    sublayer        TEXT,
    persona_style   TEXT,
    clarity_score   INTEGER,
    synthesis_body  TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      TEXT NOT NULL,
    step        INTEGER NOT NULL,
    node        TEXT NOT NULL,
    glyph       TEXT,
    ts          TEXT NOT NULL,
    payload_in  TEXT,
    payload_out TEXT,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_audit_run_id ON audit_log(run_id);
CREATE INDEX IF NOT EXISTS idx_runs_ts      ON runs(ts DESC);
"""


def init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    """Create tables if missing. Idempotent."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


@contextmanager
def get_conn(db_path: Path = DEFAULT_DB_PATH):
    """Yield a row-factory'd sqlite3 connection. Auto-commits on exit."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
