"""
Output Synth Node — refines response clarity, tone, and structure.

Per Sentinel Forge System Core Directive:
  [Output Synth Node] Refines response clarity, tone, and structure.
  Clarity Score >= 95 mandatory.

Glyph: 📤 (Output — emit)
"""

from __future__ import annotations
from dataclasses import dataclass
import re
from .persona_node import PersonaSelection


@dataclass(frozen=True)
class SynthesizedResponse:
    body:           str
    clarity_score:  int        # 1-100
    style_applied:  str
    glyph_tag:      str = "📤"


class OutputSynthNode:
    """Synthesizes the final response per persona + clarity targets."""

    CLARITY_TARGET = 95

    def synthesize(self, draft: str, persona: PersonaSelection) -> SynthesizedResponse:
        body = self._apply_style(draft, persona)
        clarity = self._score_clarity(body)
        return SynthesizedResponse(
            body=body, clarity_score=clarity, style_applied=persona.style.value,
        )

    def _apply_style(self, draft: str, persona: PersonaSelection) -> str:
        style = persona.style.value
        # Style-specific transformations (lightweight; full LLM would do more)
        if style == "technical":
            # ensure brevity + bullet form for long drafts
            if len(draft) > 500 and "\n- " not in draft:
                return draft  # leave as-is; caller may format
        if style == "academic":
            return draft  # academic prose preserved
        if style == "poetic" or style == "visionary":
            return draft  # imaginative voice preserved
        if style == "direct":
            # strip hedges
            for hedge in ("perhaps ", "maybe ", "I think ", "I believe "):
                draft = draft.replace(hedge, "")
            return draft
        return draft  # mentor default

    def _score_clarity(self, body: str) -> int:
        """Heuristic clarity score (1-100). Higher = clearer."""
        score = 100
        sentences = re.split(r"[.!?]+\s+", body.strip())
        if not sentences:
            return 50
        # Penalty for very long sentences
        avg_words = sum(len(s.split()) for s in sentences) / max(1, len(sentences))
        if avg_words > 30:
            score -= 10
        if avg_words > 45:
            score -= 10
        # Penalty for nested clauses (rough)
        nested = body.count("(") + body.count("—") * 0.5
        if nested > 10:
            score -= 5
        # Penalty for filler
        fillers = sum(body.lower().count(f) for f in ("very ", "really ", "actually ", "basically "))
        score -= min(10, fillers)
        # Bonus for structure markers
        if any(m in body for m in ("##", "**", "- ", "1.", "|")):
            score += 5
        return max(1, min(100, int(score)))
