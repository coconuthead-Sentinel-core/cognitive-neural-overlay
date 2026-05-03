"""
Input Node — detects modality, tone, and type of incoming request.

Per Sentinel Forge System Core Directive:
  [Input Node] Detects modality, tone, and type of request (question, command, abstract).

Glyph: 📥 (Input — intake)
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import re


class Modality(str, Enum):
    TEXT     = "text"
    VOICE    = "voice"      # voice-to-text — proprietor's primary input mode
    IMAGE    = "image"
    VIDEO    = "video"
    DOCUMENT = "document"
    CODE     = "code"
    MIXED    = "mixed"


class RequestType(str, Enum):
    QUESTION = "question"
    COMMAND  = "command"
    ABSTRACT = "abstract"
    DECLARATIVE = "declarative"


class Tone(str, Enum):
    NEUTRAL  = "neutral"
    URGENT   = "urgent"
    REFLECTIVE = "reflective"
    DIRECTIVE = "directive"
    PLAYFUL  = "playful"


@dataclass(frozen=True)
class InputClassification:
    modality:      Modality
    request_type:  RequestType
    tone:          Tone
    raw_length:    int
    glyph_tag:     str = "📥"


class InputNode:
    """Classifies an incoming payload into modality + type + tone."""

    _Q_MARKERS  = re.compile(r"\?|^(what|why|how|when|where|who|can|could|should|would|will|is|are|do|does)\b", re.IGNORECASE)
    _CMD_VERBS  = re.compile(r"^(do|build|create|make|run|start|stop|kill|fix|review|read|write|update|delete|sample|verify|check)\b", re.IGNORECASE)
    _URGENT     = re.compile(r"\b(urgent|now|immediately|asap|please do|start)\b", re.IGNORECASE)
    _REFLECTIVE = re.compile(r"\b(reflect|consider|think|ponder|wonder|feel)\b", re.IGNORECASE)
    _PLAYFUL    = re.compile(r"\b(coconut|fun|cool|awesome|haha)\b|🥥", re.IGNORECASE)

    def classify(self, raw: str, modality_hint: Modality | None = None) -> InputClassification:
        modality = modality_hint or self._guess_modality(raw)
        request_type = self._guess_request_type(raw)
        tone = self._guess_tone(raw)
        return InputClassification(
            modality=modality, request_type=request_type, tone=tone,
            raw_length=len(raw),
        )

    def _guess_modality(self, raw: str) -> Modality:
        if "://" in raw and any(ext in raw.lower() for ext in (".mp4", ".mov", ".webm")):
            return Modality.VIDEO
        if "://" in raw and any(ext in raw.lower() for ext in (".png", ".jpg", ".jpeg", ".webp", ".gif")):
            return Modality.IMAGE
        if "://" in raw and any(ext in raw.lower() for ext in (".docx", ".pdf", ".txt", ".md")):
            return Modality.DOCUMENT
        if raw.startswith(("```", "def ", "class ", "function ", "import ", "from ")):
            return Modality.CODE
        # Voice-to-text signature: trailing slash, "./" or "/." patterns, or many slashes
        if raw.rstrip().endswith("/") or "./" in raw or "/." in raw or raw.count("/") >= 2 or raw.count(".") > 5:
            return Modality.VOICE
        return Modality.TEXT

    def _guess_request_type(self, raw: str) -> RequestType:
        if self._CMD_VERBS.search(raw):
            return RequestType.COMMAND
        if self._Q_MARKERS.search(raw):
            return RequestType.QUESTION
        if any(w in raw.lower() for w in ("imagine", "consider the", "what if", "philosophical")):
            return RequestType.ABSTRACT
        return RequestType.DECLARATIVE

    def _guess_tone(self, raw: str) -> Tone:
        if self._URGENT.search(raw):
            return Tone.URGENT
        if self._PLAYFUL.search(raw):
            return Tone.PLAYFUL
        if self._REFLECTIVE.search(raw):
            return Tone.REFLECTIVE
        if any(w in raw.lower() for w in ("must", "do this", "now", "begin")):
            return Tone.DIRECTIVE
        return Tone.NEUTRAL
