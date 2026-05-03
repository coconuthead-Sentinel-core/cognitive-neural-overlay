"""
Persona Node — adjusts response style based on intent.

Per Sentinel Forge System Core Directive:
  [Persona Node] Adjusts style (technical, visionary, poetic, academic) based on intent.

Glyph: 🥥 (Coconut — Coconut Head persona / activate creative mode)
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .input_node import InputClassification, RequestType, Tone
from .router_node import RoutingDecision, Sublayer


class PersonaStyle(str, Enum):
    TECHNICAL  = "technical"
    VISIONARY  = "visionary"
    POETIC     = "poetic"
    ACADEMIC   = "academic"
    MENTOR     = "mentor"      # Archivist of Wisdom default
    DIRECT     = "direct"


@dataclass(frozen=True)
class PersonaSelection:
    style:       PersonaStyle
    rationale:   str
    glyph_tag:   str = "🥥"


class PersonaNode:
    """Selects the response persona style."""

    def select(self, classification: InputClassification, routing: RoutingDecision) -> PersonaSelection:
        # Reflective + abstract -> visionary or poetic
        if routing.sublayer == Sublayer.REFLECTION:
            if classification.tone == Tone.PLAYFUL:
                return PersonaSelection(PersonaStyle.POETIC, "reflective+playful -> poetic voice")
            return PersonaSelection(PersonaStyle.VISIONARY, "reflective+formal -> visionary")
        # Analysis layer -> technical or academic depending on length
        if routing.sublayer == Sublayer.ANALYSIS:
            if classification.raw_length > 800:
                return PersonaSelection(PersonaStyle.ACADEMIC, "long analysis -> academic depth")
            return PersonaSelection(PersonaStyle.TECHNICAL, "short analysis -> technical brevity")
        # Output layer -> direct (commands)
        if routing.sublayer == Sublayer.OUTPUT and classification.request_type == RequestType.COMMAND:
            return PersonaSelection(PersonaStyle.DIRECT, "command -> direct execution voice")
        # Default: mentor (Archivist of Wisdom)
        return PersonaSelection(PersonaStyle.MENTOR, "default -> mentor / Archivist of Wisdom")
