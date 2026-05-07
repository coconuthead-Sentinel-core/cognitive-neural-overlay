"""
Audit log writer + reader.

Append-only. Every /cno/process call generates one `runs` row + 5 `audit_log` rows
(one per node crossing). Backs the GET /cno/audit endpoints and the dashboard.
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .persistence import DEFAULT_DB_PATH, get_conn, init_db


NODE_GLYPHS = {
    "input":   "📥",
    "router":  "🔄",
    "memory":  "🧊",
    "persona": "🥥",
    "synth":   "📤",
}


@dataclass(frozen=True)
class RunHeader:
    run_id:         str
    ts:             str
    request:        str
    modality:       str
    request_type:   str
    tone:           str
    sublayer:       str
    persona_style:  str
    clarity_score:  int
    synthesis_body: str


@dataclass(frozen=True)
class AuditEntry:
    run_id:      str
    step:        int
    node:        str
    glyph:       str
    ts:          str
    payload_in:  dict
    payload_out: dict


class AuditLog:
    """Thin wrapper over the SQLite tables. One instance per app."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        self.db_path = db_path
        init_db(db_path)

    # --- writes ---

    def record_run_header(
        self,
        run_id: str,
        request: str,
        modality: str,
        request_type: str,
        tone: str,
        sublayer: str,
        persona_style: str,
        clarity_score: int,
        synthesis_body: str,
    ) -> None:
        with get_conn(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO runs (run_id, ts, request, modality, request_type,
                                  tone, sublayer, persona_style, clarity_score, synthesis_body)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    datetime.now(timezone.utc).isoformat(),
                    request[:500],
                    modality, request_type, tone,
                    sublayer, persona_style, clarity_score,
                    synthesis_body[:500],
                ),
            )

    def record_node_crossing(
        self,
        run_id: str,
        step: int,
        node: str,
        payload_in: dict,
        payload_out: dict,
    ) -> None:
        with get_conn(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO audit_log (run_id, step, node, glyph, ts, payload_in, payload_out)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id, step, node,
                    NODE_GLYPHS.get(node, ""),
                    datetime.now(timezone.utc).isoformat(),
                    json.dumps(payload_in, default=str),
                    json.dumps(payload_out, default=str),
                ),
            )

    # --- reads ---

    def list_runs(self, limit: int = 50, offset: int = 0) -> list[RunHeader]:
        with get_conn(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM runs ORDER BY ts DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        return [RunHeader(**dict(r)) for r in rows]

    def get_run(self, run_id: str) -> Optional[RunHeader]:
        with get_conn(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
        return RunHeader(**dict(row)) if row else None

    def get_crossings(self, run_id: str) -> list[AuditEntry]:
        with get_conn(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM audit_log WHERE run_id = ? ORDER BY step ASC",
                (run_id,),
            ).fetchall()
        return [
            AuditEntry(
                run_id=r["run_id"], step=r["step"], node=r["node"],
                glyph=r["glyph"], ts=r["ts"],
                payload_in=json.loads(r["payload_in"]) if r["payload_in"] else {},
                payload_out=json.loads(r["payload_out"]) if r["payload_out"] else {},
            )
            for r in rows
        ]

    def reset(self) -> None:
        with get_conn(self.db_path) as conn:
            conn.execute("DELETE FROM audit_log")
            conn.execute("DELETE FROM runs")
