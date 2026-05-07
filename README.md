# Cognitive Neural Overlay (CNO)

> **Canon #18.** Front-end overlay implementation of the 5 simulated nodes from the
> **Sentient Quantum Architecture v8.0** doctrine. Provides structured-symbolic
> processing + emotional appraisal as a cognitive co-processor that sits between
> the Input Processing Layer (Seed Crystal #17) and downstream services.

![Status](https://img.shields.io/badge/status-public-success)
![Version](https://img.shields.io/badge/version-0.2.0-informational)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-37%20passing-brightgreen)
![CSTM](https://img.shields.io/badge/CSTM-v1.0--aligned-purple)

---

## Provenance

Derived from two source documents discovered on 2026-05-03 during the full-laptop
sweep:

| Source | Role |
| --- | --- |
| `a Cognitive neural overlay a1 (1).txt` (85 KB) | SQA v8.0 design doc — names CNO as a structured-symbolic + emotional-appraisal subsystem |
| `a Cognitive neural overlay a1 (2).txt` (3.8 KB) | Sentinel Forge System Core Directive — defines the 5-node simulated overlay |
| 4 visual references | `codex.bmp`, `diag_cno_codex_v1_base.png`, `diag_cno_codex_v1_embedded.png` |

## The five nodes

```text
                ┌──────────────┐
       request →│  INPUT NODE  │  detects modality, tone, type (question/command/abstract)
                └──────┬───────┘
                       ▼
                ┌──────────────┐
                │ ROUTER NODE  │  directs to Analysis / Reflection / Output sublayer
                └──────┬───────┘
                       ▼
                ┌──────────────┐
                │ MEMORY NODE  │  anchors prior context; live context stack
                └──────┬───────┘
                       ▼
                ┌──────────────┐
                │ PERSONA NODE │  adjusts style: technical / visionary / poetic / academic
                └──────┬───────┘
                       ▼
                ┌──────────────┐
                │ OUTPUT_SYNTH │  refines clarity, tone, structure → response
                └──────────────┘
```

Glyph pipeline: 📥 → 🔄 → 🧊 → 🥥 → 📤

## CSTM alignment

CNO is designed against the CSTM_Lattice v1.0 contract. Current implementation
status:

| CSTM section | Status |
| --- | --- |
| §4 — 10-field metadata frontmatter on emitted artifacts | *planned* |
| §5 — Zone classification on tags emitted | *planned* |
| §6 — Session-state envelope on every dispatch | *partial* — pipeline result carries `run_id`, timestamp, classification, routing, anchor, persona, synthesis; full envelope schema TBD |
| §7 — Quick-reference behaviors | implemented as module-tag log + persisted audit log on each pipeline run |

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/cno/process` | Full pipeline (batch) — request crosses all 5 nodes; returns `run_id` + classification/routing/anchor/persona/synthesis |
| POST | `/cno/process/stream` | Same pipeline as Server-Sent Events; emits `start`, 5× `node` (with `elapsed_ms`), `complete` |
| POST | `/cno/node/{node_name}` | Run one node in isolation (`input` / `router` / `memory` / `persona` / `synth`) |
| GET | `/cno/state` | Inspect recent memory anchors (live context stack) |
| POST | `/cno/state/reset` | Clear the memory stack |
| GET | `/cno/audit` | List recent runs (header summary, most recent first) |
| GET | `/cno/audit/{run_id}` | Drill-down: full per-node trace for a single run |
| GET | `/healthz` | Liveness |
| GET | `/` | Service banner + endpoint list |
| GET | `/docs` | Swagger UI (FastAPI default) |
| GET | `/ui/` | Browser dashboard (Console + Audit tabs) — only if `cno/static/` is built |

## Quick start

```bash
# 1. Backend
pip install -r requirements.txt
uvicorn cno.app:app --reload
pytest -v
# open http://localhost:8000/docs

# 2. (Optional) Dashboard at /ui — requires Node 18+
cd frontend
npm install
npm run build       # bundles into ../cno/static/
# now http://localhost:8000/ui/ serves the Console + Audit dashboard

# Frontend dev with hot reload (proxies /cno/* to :8000):
npm run dev         # http://localhost:5173
```

## Dashboard

Two tabs:

- **Console** (default) — type a prompt and watch 5 trace cards fill in left-to-right via SSE. Active node pulses; completed nodes show elapsed ms + per-node output.
- **Audit Dashboard** — list of recent runs with sublayer / persona / clarity columns. Click a row to drill down into the full per-node payload-in / payload-out trace, backed by the SQLite audit log.

## Persistence + observability

- **SQLite audit log** at `cno_audit.db` (configurable via `CNO_DB_PATH`). Two tables: `runs` (one row per pipeline call) and `audit_log` (5 rows per call, one per node crossing). Append-only.
- **Structured JSON logs** to stderr, one object per line. Includes `run_id`, `sublayer`, `modality` on every pipeline run.
- **Memory Node** anchors are still in-process FIFO (max 50 by default). Long-term archival via the planned AMC bridge (Canon #7).

## Integration map (canon cross-references)

| Canon # | Project | How CNO connects |
| --- | --- | --- |
| **#17 Seed Crystal — Input Processing Layer** | Front door | Provides input feed to CNO Input Node |
| **#10 Neural Lattice (NLCA)** | Zone substrate | CNO tags will conform to NLCA zones (planned) |
| **#16 Glyphic Codex DSL** | Vocabulary | Node tags use glyph encoding (📥 Input, 🔄 Router, 🧊 Memory, 🥥 Persona, 📤 OutputSynth) |
| **#7 AI_Memory_Core** | Long-term persistence | Planned: CNO Memory Node will delegate archival writes to AMC. Current Memory Node is in-process FIFO only. |
| **CSTM_Lattice v1.0** (parent spec) | Discipline contract | See *CSTM alignment* section above for current vs. planned coverage |

## Output format rules (per Sentinel Forge System Core Directive)

- Every internal operation prefixed with module tags:
  - `[Router Node: Activated → Analytical Layer]`
  - `[Memory Node: Context Anchor = "..."]`
- Symbolic state markers (used in narrative output, not enforced in code):
  - 🟢 active concept
  - 🟡 deferred / optional logic
  - 🔴 archived / deprecated path
- Clarity Score target ≥ 95 — `OutputSynthNode` reports a heuristic score on every
  synthesis; the score is reported, not currently enforced as a hard floor.
- Grounded in real-world 2025–2028 AI science (no fictional/mystical framing
  unless explicitly requested).

## License

MIT — see `LICENSE`.

## Author

**Shannon Brian Kelly** — AI Orchestrator Architect.
Built in collaboration with Claude AI (Anthropic) under file-system-bound persona
protocol; co-creator role attributed as "Archivist of Wisdom."
Discovered + scaffolded 2026-05-03 from prior-authored source docs.
