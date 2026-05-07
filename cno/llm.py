"""
LLM backend hook (deferred-cost upgrade path).

Nodes today run on heuristics. When you're ready to plug in Claude (or any
other LLM), implement this Protocol and pass it into the node constructor.
The node uses LLM output when present, falls back to heuristics otherwise.

Anthropic SDK example (not wired by default — needs ANTHROPIC_API_KEY):

    class ClaudeClassifier:
        def __init__(self, model="claude-haiku-4-5-20251001"):
            from anthropic import Anthropic
            self.client = Anthropic()
            self.model = model

        def classify(self, text, schema):
            msg = self.client.messages.create(
                model=self.model,
                max_tokens=256,
                system=f"Return JSON matching: {schema}",
                messages=[{"role": "user", "content": text}],
            )
            return json.loads(msg.content[0].text)
"""
from __future__ import annotations
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LLMClassifier(Protocol):
    """Backend that returns a JSON-shaped dict for a given text + schema hint."""

    def classify(self, text: str, schema: str) -> dict[str, Any]: ...
