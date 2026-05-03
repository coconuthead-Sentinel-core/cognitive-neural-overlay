"""
CNO Pipeline — drives a request through all 5 nodes sequentially.

Per Sentinel Forge System Core Directive: linear flow
    Input -> Router -> Memory -> Persona -> OutputSynth

Each crossing is logged with module tags for symbolic traceability.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .nodes import (
    InputNode, RouterNode, MemoryNode, PersonaNode, OutputSynthNode,
    Modality,
)


@dataclass
class CNOPipelineResult:
    request:           str
    classification:    dict
    routing:           dict
    memory_anchor:     dict
    persona_selection: dict
    synthesis:         dict
    module_tags:       list[str] = field(default_factory=list)
    timestamp:         str = ""
    glyph_pipeline:    str = "📥 → 🔄 → 🧊 → 🥥 → 📤"


class CNOPipeline:
    """Linear 5-node CNO pipeline. Singleton-friendly."""

    def __init__(self):
        self.input    = InputNode()
        self.router   = RouterNode()
        self.memory   = MemoryNode()
        self.persona  = PersonaNode()
        self.synth    = OutputSynthNode()

    def process(self, request: str, draft_response: str = "", modality_hint: Modality | None = None) -> CNOPipelineResult:
        tags: list[str] = []

        # 1. INPUT
        cls = self.input.classify(request, modality_hint=modality_hint)
        tags.append(f"[Input Node: modality={cls.modality.value}, type={cls.request_type.value}, tone={cls.tone.value}]")

        # 2. ROUTER
        route = self.router.route(cls)
        tags.append(f"[Router Node: Activated → {route.sublayer.value}]")

        # 3. MEMORY
        anchor = self.memory.anchor(
            summary=request[:200],
            request_type=cls.request_type.value,
            tone=cls.tone.value,
        )
        tags.append(f'[Memory Node: Context Anchor = "{anchor.summary[:60]}..."]')

        # 4. PERSONA
        persona = self.persona.select(cls, route)
        tags.append(f"[Persona Node: style={persona.style.value} ({persona.rationale})]")

        # 5. OUTPUT SYNTH
        if not draft_response:
            draft_response = f"[draft based on {route.sublayer.value} routing of: {request[:100]}]"
        synth = self.synth.synthesize(draft_response, persona)
        tags.append(f"[Output Synth Node: clarity={synth.clarity_score}, style={synth.style_applied}]")

        return CNOPipelineResult(
            request=request[:500],
            classification={"modality": cls.modality.value, "request_type": cls.request_type.value, "tone": cls.tone.value, "raw_length": cls.raw_length},
            routing={"sublayer": route.sublayer.value, "rationale": route.rationale},
            memory_anchor={"timestamp": anchor.timestamp, "summary": anchor.summary},
            persona_selection={"style": persona.style.value, "rationale": persona.rationale},
            synthesis={"body": synth.body[:500], "clarity_score": synth.clarity_score, "style_applied": synth.style_applied},
            module_tags=tags,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


PIPELINE = CNOPipeline()
