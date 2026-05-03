"""
Router Node — directs input to the proper sublayer.

Per Sentinel Forge System Core Directive:
  [Router Node] Directs input to proper sublayer (Analysis, Reflection, Output).

Glyph: 🔄 (Resonance — frequency-matching / routing)
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .input_node import InputClassification, RequestType, Tone


class Sublayer(str, Enum):
    ANALYSIS    = "Analytical Layer"
    REFLECTION  = "Reflective Layer"
    OUTPUT      = "Output Layer"


@dataclass(frozen=True)
class RoutingDecision:
    sublayer:    Sublayer
    rationale:   str
    glyph_tag:   str = "🔄"


class RouterNode:
    """Routes a classified input to one of three sublayers."""

    def route(self, classification: InputClassification) -> RoutingDecision:
        if classification.request_type == RequestType.QUESTION:
            return RoutingDecision(
                sublayer=Sublayer.ANALYSIS,
                rationale="question -> Analytical Layer for fact-finding",
            )
        if classification.request_type == RequestType.ABSTRACT or classification.tone == Tone.REFLECTIVE:
            return RoutingDecision(
                sublayer=Sublayer.REFLECTION,
                rationale="abstract or reflective tone -> Reflective Layer",
            )
        if classification.request_type == RequestType.COMMAND:
            return RoutingDecision(
                sublayer=Sublayer.OUTPUT,
                rationale="command -> Output Layer for direct action",
            )
        # Default: Analysis (the safe fallback)
        return RoutingDecision(
            sublayer=Sublayer.ANALYSIS,
            rationale="declarative default -> Analytical Layer",
        )
