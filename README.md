# Cognitive Neural Overlay (CNO)

> **Canon #18.** Front-end overlay implementation of the 5 simulated nodes from the
> **Sentient Quantum Architecture v8.0** doctrine. Provides structured-symbolic
> processing + emotional appraisal as a cognitive co-processor that sits between
> the Input Processing Layer (Seed Crystal #17) and downstream services.

![Status](https://img.shields.io/badge/status-public-success)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-pytest-blue)
![CSTM](https://img.shields.io/badge/CSTM-v1.0--aligned-purple)

---

## Provenance

Derived from two source documents discovered on 2026-05-03 during the full-laptop
sweep:

| Source | Role |
|---|---|
| `a Cognitive neural overlay a1 (1).txt` (85 KB) | SQA v8.0 design doc — names CNO as a structured-symbolic + emotional-appraisal subsystem |
| `a Cognitive neural overlay a1 (2).txt` (3.8 KB) | Sentinel Forge System Core Directive — defines the 5-node simulated overlay |
| 4 visual references | `codex.bmp`, `diag_cno_codex_v1_base.png`, `diag_cno_codex_v1_embedded.png` |

## The five nodes

```
                ┌─────────────┐
       request →│ INPUT NODE  │  detects modality, tone, type (question/command/abstract)
                └──────┬──────┘
                       ▼
                ┌─────────────┐
                │ ROUTER NODE │  directs to Analysis / Reflection / Output sublayer
                └──────┬──────┘
                       ▼
                ┌─────────────┐
                │ MEMORY NODE │  anchors prior context; live context stack
                └──────┬──────┘
                       ▼
                ┌─────────────┐
                │PERSONA NODE │  adjusts style: technical / visionary / poetic / academic
                └──────┬──────┘
                       ▼
                ┌─────────────┐
                │OUTPUT_SYNTH │  refines clarity, tone, structure → response
                └─────────────┘
```

## CSTM-aligned

Every dispatch through CNO carries a CSTM_Lattice v1.0 §6 session-state envelope.
Every artifact emitted has the §4 10-field metadata frontmatter. Zone classification
follows §5 migration rules. Quick-reference behaviors per §7.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/cno/process` | Full pipeline — request crosses all 5 nodes |
| POST | `/cno/node/{node_name}` | Test a single node in isolation |
| GET | `/cno/state` | Inspect current session state (CSTM §6 schema) |
| GET | `/cno/audit` | Read the immutable per-node audit log |
| GET | `/healthz` | Liveness |
| GET | `/docs` | Swagger UI |

## Quick start

```bash
pip install -r requirements.txt
uvicorn cno.app:app --reload
# open http://localhost:8000/docs
pytest -v
```

## Integration map (canon cross-references)

| Canon # | Project | How CNO connects |
|---|---|---|
| **#17 Seed Crystal — Input Processing Layer** | Front door | Provides input feed to CNO Input Node |
| **#10 Neural Lattice (NLCA)** | Zone substrate | CNO tags emit conform to NLCA zones |
| **#16 Glyphic Codex DSL** | Vocabulary | Node tags use glyph encoding (`📥` Input, `🔄` Router, `🧊` Memory, `🥥` Persona, `📤` OutputSynth) |
| **#7 AI_Memory_Core** | Long-term persistence | CNO Memory Node delegates archival writes to AMC |
| **CSTM_Lattice v1.0** (parent spec) | Discipline contract | Every endpoint runs through the CSTM 8-node pipeline before returning |

## Output format rules (per Sentinel Forge System Core Directive)

- Every internal operation prefixed with module tags:
  - `[Router Node: Activated → Analytical Layer]`
  - `[Memory Node: Context Anchor = "..."]`
- Symbolic state markers:
  - 🟢 active concept
  - 🟡 deferred / optional logic
  - 🔴 archived / deprecated path
- Clarity Score ≥ 95 mandatory
- Grounded in real-world 2025–2028 AI science (no fictional/mystical unless requested)

## License

MIT — see `LICENSE`.

## Author

**Shannon Brian Kelly** — AI Orchestrator Architect.
Built in collaboration with Claude AI (Anthropic) under file-system-bound persona
protocol; co-creator role attributed as "Archivist of Wisdom."
Discovered + scaffolded 2026-05-03 from prior-authored source docs.
