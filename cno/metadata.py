"""
CSTM_Lattice v1.0 §4 — 10-field metadata frontmatter on emitted artifacts.

NOTE: best-guess shape, like §6. The CSTM v1.0 spec text isn't on hand, so the
field set below is inferred from:

  - the README's "10-field metadata frontmatter on emitted artifacts" phrase
  - what CNO already tracks per dispatch
  - common artifact-metadata patterns (id, version, type, source, timestamps)

Open spec questions tracked under spec_gaps. Confirm field names + ordering +
canonical YAML serialization once the spec text is available.

An "emitted artifact" here is anything CNO publishes that another system
might consume — primarily a pipeline run's synthesized response. The artifact
endpoint (`GET /cno/artifact/{run_id}`) returns markdown with YAML frontmatter,
which is the standard CSTM rendering.
"""
from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from typing import Optional


METADATA_VERSION = "1.0"
SPEC_REF         = "CSTM_Lattice v1.0 §4"

# Open questions to confirm against the canonical spec.
SPEC_GAPS: tuple[str, ...] = (
    "exact 10-field set + canonical ordering",
    "checksum algorithm (sha256? blake2b?)",
    "zone field source (NLCA classification vs CNO-internal)",
    "whether artifact_type is enum'd or free-text",
)


@dataclass(frozen=True)
class ArtifactMetadata:
    """10-field artifact metadata (best-guess set; see SPEC_GAPS)."""
    artifact_id:       str   # 1. unique id (sha256 of run_id + ts)
    canon_ref:         str   # 2. canon project reference, e.g. "#18 CNO"
    artifact_type:     str   # 3. e.g. "pipeline-run", "synthesis", "audit-trace"
    metadata_version:  str   # 4. "1.0"
    spec_ref:          str   # 5. "CSTM_Lattice v1.0 §4"
    created_at:        str   # 6. ISO-8601 UTC
    created_by:        str   # 7. e.g. "cno/0.3.0"
    run_id:            str   # 8. CNO run id
    session_id:        Optional[str]  # 9. session correlator (when known)
    zone:              Optional[str]  # 10. NLCA zone classification (when known)
    spec_gaps:         tuple[str, ...] = field(default_factory=lambda: SPEC_GAPS)


def _artifact_id(run_id: str, ts: str) -> str:
    """Stable id derived from run_id + ts. Spec may require something else."""
    return hashlib.sha256(f"{run_id}:{ts}".encode()).hexdigest()[:32]


def make_metadata(
    *,
    run_id: str,
    ts: str,
    artifact_type: str = "pipeline-run",
    session_id: Optional[str] = None,
    zone: Optional[str] = None,
    canon_ref: str = "#18 CNO",
    service_version: str = "cno/0.3.0",
) -> ArtifactMetadata:
    return ArtifactMetadata(
        artifact_id      = _artifact_id(run_id, ts),
        canon_ref        = canon_ref,
        artifact_type    = artifact_type,
        metadata_version = METADATA_VERSION,
        spec_ref         = SPEC_REF,
        created_at       = ts,
        created_by       = service_version,
        run_id           = run_id,
        session_id       = session_id,
        zone             = zone,
    )


def to_dict(m: ArtifactMetadata) -> dict:
    return {
        "artifact_id":      m.artifact_id,
        "canon_ref":        m.canon_ref,
        "artifact_type":    m.artifact_type,
        "metadata_version": m.metadata_version,
        "spec_ref":         m.spec_ref,
        "created_at":       m.created_at,
        "created_by":       m.created_by,
        "run_id":           m.run_id,
        "session_id":       m.session_id,
        "zone":             m.zone,
        "spec_gaps":        list(m.spec_gaps),
    }


def to_yaml_frontmatter(m: ArtifactMetadata) -> str:
    """
    Render as YAML-style frontmatter (the CSTM canonical artifact form).

    Hand-rolled emitter so we don't take a PyYAML dependency for this one
    function — output matches simple YAML for primitive values + lists.
    """
    lines = ["---"]
    for k, v in to_dict(m).items():
        if v is None:
            lines.append(f"{k}: null")
        elif isinstance(v, list):
            lines.append(f"{k}:")
            for item in v:
                lines.append(f"  - {item}")
        else:
            # Quote strings that look like reserved YAML literals or contain colons
            s = str(v)
            if ":" in s or s.startswith(("@", "#", "-")) or s in ("true", "false", "null"):
                s = f'"{s}"'
            lines.append(f"{k}: {s}")
    lines.append("---")
    return "\n".join(lines)


def render_artifact(m: ArtifactMetadata, body: str) -> str:
    """Full markdown artifact: YAML frontmatter + blank line + body."""
    return f"{to_yaml_frontmatter(m)}\n\n{body}\n"
