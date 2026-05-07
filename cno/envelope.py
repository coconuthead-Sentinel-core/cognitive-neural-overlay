"""
CSTM_Lattice v1.0 §6 — Session-state envelope.

Wraps a CNOPipelineResult with session correlation + envelope metadata so
downstream consumers can chain runs, validate dispatch, and trace lineage.

NOTE: best-guess shape. Confirm the actual §6 field set against CSTM_Lattice
v1.0 when the spec text is available. Fields below are derived from what
CNO already tracks plus the language in the parent README ("session-state
envelope on every dispatch").

Open spec questions:
  - Is `session_id` server-generated or client-supplied?
  - What is the canonical envelope_version string?
  - Are `prior_run_ids` capped at N?
  - Is there a §6 signature/checksum requirement?
"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from threading import Lock
from typing import Any


ENVELOPE_VERSION = "1.0"
SPEC_REF         = "CSTM_Lattice v1.0 §6"
PRIOR_RUNS_CAP   = 25


@dataclass
class SessionEnvelope:
    session_id:       str
    envelope_version: str
    spec_ref:         str
    run_id:           str
    ts:               str
    glyph_pipeline:   str
    prior_run_ids:    list[str]
    payload:          dict     # the CNOPipelineResult body
    spec_gaps:        list[str] = field(default_factory=lambda: list(_OPEN_QUESTIONS))


_OPEN_QUESTIONS: tuple[str, ...] = (
    "session_id origin (server vs client)",
    "envelope_version canonical string",
    "prior_run_ids cap",
    "signature/checksum requirement",
)


class SessionRegistry:
    """In-memory session_id -> recent run_ids correlator. Threadsafe."""

    def __init__(self, prior_cap: int = PRIOR_RUNS_CAP):
        self._sessions: dict[str, list[str]] = {}
        self._lock = Lock()
        self._cap = prior_cap

    def session_for(self, supplied: str | None) -> str:
        """Use the supplied session if provided, else mint a fresh one."""
        if supplied:
            return supplied
        return uuid.uuid4().hex

    def append_run(self, session_id: str, run_id: str) -> list[str]:
        """Record run_id under session; return prior run_ids (excluding the new one)."""
        with self._lock:
            history = self._sessions.setdefault(session_id, [])
            prior = list(history)
            history.append(run_id)
            if len(history) > self._cap:
                del history[: len(history) - self._cap]
            return prior

    def history(self, session_id: str) -> list[str]:
        with self._lock:
            return list(self._sessions.get(session_id, []))


REGISTRY = SessionRegistry()


def wrap(payload: dict, *, run_id: str, ts: str, glyph_pipeline: str,
         session_id: str, prior_run_ids: list[str]) -> SessionEnvelope:
    return SessionEnvelope(
        session_id       = session_id,
        envelope_version = ENVELOPE_VERSION,
        spec_ref         = SPEC_REF,
        run_id           = run_id,
        ts               = ts,
        glyph_pipeline   = glyph_pipeline,
        prior_run_ids    = prior_run_ids,
        payload          = payload,
    )


def envelope_to_dict(env: SessionEnvelope) -> dict[str, Any]:
    """JSON-safe dict (the payload is already a dict)."""
    return {
        "session_id":       env.session_id,
        "envelope_version": env.envelope_version,
        "spec_ref":         env.spec_ref,
        "run_id":           env.run_id,
        "ts":               env.ts,
        "glyph_pipeline":   env.glyph_pipeline,
        "prior_run_ids":    env.prior_run_ids,
        "payload":          env.payload,
        "spec_gaps":        env.spec_gaps,
    }
