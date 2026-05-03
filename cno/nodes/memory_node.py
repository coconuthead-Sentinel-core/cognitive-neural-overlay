"""
Memory Node — anchors prior input summaries via a live context stack.

Per Sentinel Forge System Core Directive:
  [Memory Node] Anchors previous input summaries using a live context stack.

Glyph: 🧊 (Platonic Cube — Stable Memory Structure)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock


@dataclass(frozen=True)
class ContextAnchor:
    timestamp:    str
    summary:      str
    request_type: str
    tone:         str


class MemoryNode:
    """Live context stack — append-only, FIFO eviction past max_depth."""

    def __init__(self, max_depth: int = 50):
        self.max_depth = max_depth
        self._stack: list[ContextAnchor] = []
        self._lock = Lock()

    def anchor(self, summary: str, request_type: str = "unknown", tone: str = "neutral") -> ContextAnchor:
        anchor = ContextAnchor(
            timestamp    = datetime.now(timezone.utc).isoformat(),
            summary      = summary[:200],
            request_type = request_type,
            tone         = tone,
        )
        with self._lock:
            self._stack.append(anchor)
            if len(self._stack) > self.max_depth:
                self._stack = self._stack[-self.max_depth:]
        return anchor

    def recent(self, n: int = 5) -> list[ContextAnchor]:
        with self._lock:
            return list(self._stack[-n:])

    def all_anchors(self) -> list[ContextAnchor]:
        with self._lock:
            return list(self._stack)

    def reset(self) -> None:
        with self._lock:
            self._stack.clear()

    @property
    def glyph_tag(self) -> str:
        return "🧊"
