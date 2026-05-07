"""
Memory Node — anchors prior input summaries via a live context stack.

Per Sentinel Forge System Core Directive:
  [Memory Node] Anchors previous input summaries using a live context stack.

Live context: in-process FIFO, max_depth entries. Long-term archival: optional
ArchivalSink (Canon #7 / AMC bridge) — every anchor is shipped to the sink in
addition to the local stack.

Glyph: 🧊 (Platonic Cube — Stable Memory Structure)
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..sinks import ArchivalSink


@dataclass(frozen=True)
class ContextAnchor:
    timestamp:    str
    summary:      str
    request_type: str
    tone:         str


class MemoryNode:
    """Live context stack — append-only, FIFO eviction past max_depth."""

    def __init__(self, max_depth: int = 50, sink: Optional["ArchivalSink"] = None):
        self.max_depth = max_depth
        self._stack: list[ContextAnchor] = []
        self._lock = Lock()
        self.sink = sink

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
        if self.sink is not None:
            # Sink errors must never break the pipeline.
            try:
                self.sink.persist(anchor)
            except Exception:
                pass
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
