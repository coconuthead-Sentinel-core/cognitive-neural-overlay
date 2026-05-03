"""
FastAPI surface for CNO. Exposes the 5-node pipeline + per-node endpoints.

Run:
    uvicorn cno.app:app --reload
    open http://localhost:8000/docs
"""

from __future__ import annotations
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from .pipeline import PIPELINE
from .nodes import Modality


app = FastAPI(
    title="Cognitive Neural Overlay (CNO)",
    version="0.1.0",
    description=(
        "Front-end overlay implementation of the 5 simulated nodes from "
        "the Sentinel Forge System Core Directive. CSTM_Lattice v1.0 aligned."
    ),
)


class ProcessRequest(BaseModel):
    request:        str = Field(..., min_length=1, max_length=10_000)
    draft_response: Optional[str] = ""
    modality_hint:  Optional[str] = None


@app.get("/healthz", tags=["meta"])
def healthz():
    return {"status": "ok", "service": "cno", "version": "0.1.0"}


@app.post("/cno/process", tags=["pipeline"])
def cno_process(req: ProcessRequest):
    modality = None
    if req.modality_hint:
        try:
            modality = Modality(req.modality_hint)
        except ValueError:
            raise HTTPException(status_code=422, detail=f"unknown modality: {req.modality_hint}")
    result = PIPELINE.process(req.request, req.draft_response, modality)
    return result


@app.get("/cno/state", tags=["state"])
def get_state():
    """Inspect current memory anchors (live context stack)."""
    anchors = PIPELINE.memory.recent(20)
    return {
        "anchor_count": len(anchors),
        "recent": [{"timestamp": a.timestamp, "summary": a.summary, "type": a.request_type, "tone": a.tone} for a in anchors],
    }


@app.post("/cno/state/reset", tags=["state"])
def reset_state():
    PIPELINE.memory.reset()
    return {"status": "reset"}


@app.get("/", tags=["meta"])
def root():
    return {
        "service":     "Cognitive Neural Overlay (CNO)",
        "canon":       "#18",
        "parent_spec": "Sentient Quantum Architecture v8.0",
        "endpoints":   ["POST /cno/process", "GET /cno/state", "POST /cno/state/reset", "GET /healthz", "GET /docs"],
        "glyph_pipeline": "📥 → 🔄 → 🧊 → 🥥 → 📤",
    }
