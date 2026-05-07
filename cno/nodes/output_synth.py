"""
Output Synth Node — refines response clarity, tone, and structure.

Per Sentinel Forge System Core Directive:
  [Output Synth Node] Refines response clarity, tone, and structure.
  Clarity Score >= 95 mandatory.

Real (lightweight) text transformations per persona, plus a multi-signal
clarity score. Not LLM-grade rewriting — that lives in the optional LLM hook.

Glyph: 📤 (Output — emit)
"""

from __future__ import annotations
import re
from dataclasses import dataclass

from .persona_node import PersonaSelection


@dataclass(frozen=True)
class SynthesizedResponse:
    body:           str
    clarity_score:  int        # 1-100
    style_applied:  str
    transforms:     tuple[str, ...] = ()
    glyph_tag:      str = "📤"


_HEDGES = ("perhaps ", "maybe ", "i think ", "i believe ", "kind of ", "sort of ")
_FILLERS = ("very ", "really ", "actually ", "basically ", "literally ")
_REDUNDANT = (
    ("in order to", "to"),
    ("at this point in time", "now"),
    ("due to the fact that", "because"),
    ("a number of", "several"),
)


def _strip_hedges(text: str) -> str:
    out = text
    for h in _HEDGES:
        out = re.sub(re.escape(h), "", out, flags=re.IGNORECASE)
    return out


def _bulletize(text: str) -> str:
    """If draft has 3+ short-ish sentences and no list markers, convert to bullets."""
    if any(m in text for m in ("\n- ", "\n1.", "\n* ")):
        return text
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if len(sentences) < 3:
        return text
    return "\n".join(f"- {s.rstrip('.')}" for s in sentences)


def _tighten(text: str) -> str:
    """Replace common verbose phrases with shorter equivalents."""
    out = text
    for verbose, terse in _REDUNDANT:
        out = re.sub(verbose, terse, out, flags=re.IGNORECASE)
    return out


class OutputSynthNode:
    CLARITY_TARGET = 95

    def synthesize(self, draft: str, persona: PersonaSelection) -> SynthesizedResponse:
        body, applied = self._apply_style(draft, persona)
        clarity = self._score_clarity(body)
        return SynthesizedResponse(
            body=body, clarity_score=clarity, style_applied=persona.style.value,
            transforms=tuple(applied),
        )

    def _apply_style(self, draft: str, persona: PersonaSelection) -> tuple[str, list[str]]:
        style = persona.style.value
        applied: list[str] = []
        body = draft

        if style == "direct":
            new = _strip_hedges(body)
            if new != body:
                applied.append("hedges_stripped")
                body = new
            new = _tighten(body)
            if new != body:
                applied.append("verbose_tightened")
                body = new

        elif style == "technical":
            new = _tighten(body)
            if new != body:
                applied.append("verbose_tightened")
                body = new
            new = _bulletize(body)
            if new != body:
                applied.append("bulletized")
                body = new

        elif style == "academic":
            # Light: preserve, ensure trailing period.
            if body and not body.rstrip().endswith((".", "!", "?")):
                body = body.rstrip() + "."
                applied.append("period_appended")

        elif style == "visionary":
            applied.append("voice_preserved")

        elif style == "poetic":
            # Insert line breaks at semicolons / em-dashes for cadence.
            new = re.sub(r"\s*[;—]\s*", "\n", body)
            if new != body:
                applied.append("cadence_breaks")
                body = new

        else:  # mentor
            applied.append("mentor_default")

        return body, applied

    def _score_clarity(self, body: str) -> int:
        score = 100
        sentences = [s for s in re.split(r"[.!?]+\s+", body.strip()) if s]
        if not sentences:
            return 50
        avg_words = sum(len(s.split()) for s in sentences) / max(1, len(sentences))
        if avg_words > 30: score -= 10
        if avg_words > 45: score -= 10

        nested = body.count("(") + int(body.count("—") * 0.5)
        if nested > 10: score -= 5

        fillers = sum(body.lower().count(f) for f in _FILLERS)
        score -= min(10, fillers * 2)

        # Passive voice rough proxy: "was|were|been|being + past participle (-ed)"
        passive = len(re.findall(r"\b(was|were|been|being)\s+\w+ed\b", body, re.IGNORECASE))
        score -= min(8, passive * 2)

        # Bonus for structure markers
        if any(m in body for m in ("##", "**", "- ", "1.", "|")):
            score += 5

        return max(1, min(100, int(score)))
