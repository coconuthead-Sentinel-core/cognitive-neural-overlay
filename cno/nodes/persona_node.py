"""
Persona Node — adjusts response style based on intent.

Per Sentinel Forge System Core Directive:
  [Persona Node] Adjusts style (technical, visionary, poetic, academic) based on intent.

Multi-factor scoring matrix: each candidate persona earns points from
(sublayer, request_type, tone, raw_length). Highest total wins; ties break in
the doctrine-defined order (mentor / Archivist of Wisdom default).

Glyph: 🥥 (Coconut — Coconut Head persona / activate creative mode)
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

from .input_node import InputClassification, RequestType, Tone
from .router_node import RoutingDecision, Sublayer


class PersonaStyle(str, Enum):
    TECHNICAL = "technical"
    VISIONARY = "visionary"
    POETIC    = "poetic"
    ACADEMIC  = "academic"
    MENTOR    = "mentor"      # Archivist of Wisdom default
    DIRECT    = "direct"


@dataclass(frozen=True)
class PersonaSelection:
    style:      PersonaStyle
    rationale:  str
    confidence: float = 0.0
    glyph_tag:  str = "🥥"


# Scoring matrix:
#  +N points to a persona for a given (signal -> persona) match.
#  Tunable; the README's stated CSTM_Lattice §7 quick-reference behaviors
#  inform default weights.
_SUBLAYER_BIAS: dict[Sublayer, dict[PersonaStyle, int]] = {
    Sublayer.ANALYSIS:    {PersonaStyle.TECHNICAL: 3, PersonaStyle.ACADEMIC: 2, PersonaStyle.MENTOR: 1},
    Sublayer.REFLECTION:  {PersonaStyle.VISIONARY: 3, PersonaStyle.POETIC: 2, PersonaStyle.MENTOR: 2},
    Sublayer.OUTPUT:      {PersonaStyle.DIRECT: 3, PersonaStyle.TECHNICAL: 1},
}

_TONE_BIAS: dict[Tone, dict[PersonaStyle, int]] = {
    Tone.URGENT:     {PersonaStyle.DIRECT: 2, PersonaStyle.TECHNICAL: 1},
    Tone.REFLECTIVE: {PersonaStyle.VISIONARY: 2, PersonaStyle.POETIC: 1, PersonaStyle.ACADEMIC: 1},
    Tone.PLAYFUL:    {PersonaStyle.POETIC: 2, PersonaStyle.MENTOR: 1},
    Tone.DIRECTIVE:  {PersonaStyle.DIRECT: 2},
    Tone.NEUTRAL:    {PersonaStyle.TECHNICAL: 1, PersonaStyle.MENTOR: 1},
}

_REQUEST_BIAS: dict[RequestType, dict[PersonaStyle, int]] = {
    RequestType.QUESTION:    {PersonaStyle.TECHNICAL: 1, PersonaStyle.MENTOR: 1},
    RequestType.COMMAND:     {PersonaStyle.DIRECT: 2},
    RequestType.ABSTRACT:    {PersonaStyle.VISIONARY: 2, PersonaStyle.POETIC: 1, PersonaStyle.ACADEMIC: 1},
    RequestType.DECLARATIVE: {PersonaStyle.MENTOR: 1, PersonaStyle.TECHNICAL: 1},
}


def _length_bias(raw_length: int) -> dict[PersonaStyle, int]:
    if raw_length > 800:
        return {PersonaStyle.ACADEMIC: 2, PersonaStyle.VISIONARY: 1}
    if raw_length < 80:
        return {PersonaStyle.DIRECT: 1, PersonaStyle.TECHNICAL: 1}
    return {}


def _add(target: dict[PersonaStyle, int], src: dict[PersonaStyle, int]) -> None:
    for k, v in src.items():
        target[k] = target.get(k, 0) + v


class PersonaNode:
    """Selects the response persona style via multi-factor scoring."""

    def select(self, classification: InputClassification, routing: RoutingDecision) -> PersonaSelection:
        scores: dict[PersonaStyle, int] = {}
        _add(scores, _SUBLAYER_BIAS.get(routing.sublayer, {}))
        _add(scores, _TONE_BIAS.get(classification.tone, {}))
        _add(scores, _REQUEST_BIAS.get(classification.request_type, {}))
        _add(scores, _length_bias(classification.raw_length))

        if not scores:
            return PersonaSelection(PersonaStyle.MENTOR, "no signals -> mentor (Archivist of Wisdom)", 0.5)

        # Tie-break order favors mentor (the doctrine default).
        order = (PersonaStyle.MENTOR, PersonaStyle.TECHNICAL, PersonaStyle.DIRECT,
                 PersonaStyle.VISIONARY, PersonaStyle.ACADEMIC, PersonaStyle.POETIC)
        ranked = sorted(scores.items(), key=lambda kv: (-kv[1], order.index(kv[0])))
        best, best_score = ranked[0]
        runner_up_score = ranked[1][1] if len(ranked) > 1 else 0
        gap = best_score - runner_up_score
        confidence = min(0.95, 0.5 + 0.08 * best_score + 0.05 * gap)

        rationale = (
            f"score={best_score} (gap+{gap}) "
            f"from sublayer={routing.sublayer.value}, "
            f"tone={classification.tone.value}, "
            f"type={classification.request_type.value}, "
            f"len={classification.raw_length}"
        )
        return PersonaSelection(best, rationale, confidence)
