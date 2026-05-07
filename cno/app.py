"""
FastAPI surface for CNO. Exposes the 5-node pipeline + audit log.

Run:
    uvicorn cno.app:app --reload
    open http://localhost:8000/docs
"""

from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .logging_config import configure_logging
from .nodes import Modality
from .pipeline import PIPELINE


configure_logging()
log = logging.getLogger("cno.app")


app = FastAPI(
    title="Cognitive Neural Overlay (CNO)",
    version="0.2.0",
    description=(
        "Front-end overlay implementation of the 5 simulated nodes from "
        "the Sentinel Forge System Core Directive. CSTM_Lattice v1.0 aligned."
    ),
)

# CORS — wide open in dev; tighten via env in prod.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProcessRequest(BaseModel):
    request:        str = Field(..., min_length=1, max_length=10_000)
    draft_response: Optional[str] = ""
    modality_hint:  Optional[str] = None


@app.get("/healthz", tags=["meta"])
def healthz():
    return {"status": "ok", "service": "cno", "version": "0.2.0"}


@app.post("/cno/process", tags=["pipeline"])
def cno_process(req: ProcessRequest):
    modality = None
    if req.modality_hint:
        try:
            modality = Modality(req.modality_hint)
        except ValueError:
            raise HTTPException(status_code=422, detail=f"unknown modality: {req.modality_hint}")
    result = PIPELINE.process(req.request, req.draft_response, modality)
    log.info(
        "pipeline_run",
        extra={
            "run_id": result.run_id,
            "sublayer": result.routing["sublayer"],
            "modality": result.classification["modality"],
        },
    )
    return result


@app.get("/cno/state", tags=["state"])
def get_state():
    """Inspect current memory anchors (live context stack)."""
    anchors = PIPELINE.memory.recent(20)
    return {
        "anchor_count": len(anchors),
        "recent": [
            {"timestamp": a.timestamp, "summary": a.summary, "type": a.request_type, "tone": a.tone}
            for a in anchors
        ],
    }


@app.post("/cno/state/reset", tags=["state"])
def reset_state():
    PIPELINE.memory.reset()
    return {"status": "reset"}


@app.get("/cno/audit", tags=["audit"])
def list_audit_runs(limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)):
    """List recent runs (header summary). Most recent first."""
    if PIPELINE.audit is None:
        raise HTTPException(status_code=503, detail="audit log not configured")
    runs = PIPELINE.audit.list_runs(limit=limit, offset=offset)
    return {
        "count": len(runs),
        "runs": [r.__dict__ for r in runs],
    }


@app.get("/cno/audit/{run_id}", tags=["audit"])
def get_audit_run(run_id: str):
    """Drill-down: full per-node trace for a single run."""
    if PIPELINE.audit is None:
        raise HTTPException(status_code=503, detail="audit log not configured")
    header = PIPELINE.audit.get_run(run_id)
    if header is None:
        raise HTTPException(status_code=404, detail=f"run not found: {run_id}")
    crossings = PIPELINE.audit.get_crossings(run_id)
    return {
        "header": header.__dict__,
        "crossings": [c.__dict__ for c in crossings],
    }


@app.get("/", tags=["meta"])
def root():
    return {
        "service":     "Cognitive Neural Overlay (CNO)",
        "canon":       "#18",
        "parent_spec": "Sentient Quantum Architecture v8.0",
        "endpoints":   [
            "POST /cno/process",
            "GET /cno/state",
            "POST /cno/state/reset",
            "GET /cno/audit",
            "GET /cno/audit/{run_id}",
            "GET /healthz",
            "GET /docs",
            "GET /ui",
        ],
        "glyph_pipeline": "📥 → 🔄 → 🧊 → 🥥 → 📤",
    }


# --- Static frontend mount (only if built) ---
_static_dir = Path(__file__).parent / "static"
if _static_dir.exists() and (_static_dir / "index.html").exists():
    app.mount("/ui", StaticFiles(directory=_static_dir, html=True), name="ui")
