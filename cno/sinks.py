"""
ArchivalSink protocol + concrete sinks for the AMC (Canon #7) bridge.

The MemoryNode keeps an in-process FIFO. When a sink is attached, every anchor
is *also* shipped to long-term storage. Three implementations:

- NullSink:    drop everything (default; no archival)
- JsonlSink:   append JSON-per-line to a file (offline durable copy)
- HttpAMCSink: POST to an AMC HTTP endpoint (real AMC bridge — TODO: confirm
               contract once Canon #7 service URL + schema are known)

Failures never break the pipeline — sinks log and swallow.
"""
from __future__ import annotations
import json
import logging
import os
import threading
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


log = logging.getLogger("cno.sinks")


@runtime_checkable
class ArchivalSink(Protocol):
    name: str

    def persist(self, anchor: Any) -> None: ...


def _to_dict(obj: Any) -> dict:
    if isinstance(obj, dict):
        return obj
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    if hasattr(obj, "__dict__"):
        return dict(obj.__dict__)
    return {"value": str(obj)}


class NullSink:
    name = "null"

    def persist(self, anchor: Any) -> None:
        return


class JsonlSink:
    """Appends JSON lines to a file. Threadsafe."""
    name = "jsonl"

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def persist(self, anchor: Any) -> None:
        try:
            with self._lock:
                with self.path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(_to_dict(anchor), default=str) + "\n")
        except OSError as e:
            log.warning("jsonl_sink_write_failed", extra={"err": str(e)})


class HttpAMCSink:
    """
    Stub HTTP sink. POSTs anchors to {url}/anchors as JSON.

    TODO: real AMC contract. Confirm when Canon #7 publishes its API:
      - exact path
      - auth header style (bearer? signed?)
      - response schema
      - retry/backoff requirements
    """
    name = "http"

    def __init__(self, url: str, *, api_key: str | None = None, timeout: float = 2.0):
        # Lazy import — httpx is already in requirements.txt but only loaded if used.
        import httpx
        self._url = url.rstrip("/") + "/anchors"
        self._api_key = api_key
        self._client = httpx.Client(timeout=timeout)

    def persist(self, anchor: Any) -> None:
        headers = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        try:
            resp = self._client.post(self._url, json=_to_dict(anchor), headers=headers)
            if resp.status_code >= 400:
                log.warning("amc_sink_non_2xx", extra={"status": resp.status_code, "url": self._url})
        except Exception as e:  # network errors, malformed url, etc.
            log.warning("amc_sink_post_failed", extra={"err": str(e), "url": self._url})


# ---- factory ----

def load_sink_from_env() -> ArchivalSink:
    """
    Pick a sink based on env:
      CNO_AMC_SINK=null|jsonl|http   (default: null)
      CNO_AMC_JSONL_PATH=...         (when sink=jsonl; default: cno_anchors.jsonl)
      CNO_AMC_URL=http://...         (when sink=http; required)
      CNO_AMC_API_KEY=...            (when sink=http; optional)
    """
    kind = (os.environ.get("CNO_AMC_SINK") or "null").lower()
    if kind == "null":
        return NullSink()
    if kind == "jsonl":
        path = os.environ.get("CNO_AMC_JSONL_PATH") or "cno_anchors.jsonl"
        return JsonlSink(Path(path))
    if kind == "http":
        url = os.environ.get("CNO_AMC_URL")
        if not url:
            log.warning("amc_sink_http_missing_url; falling back to null")
            return NullSink()
        return HttpAMCSink(url, api_key=os.environ.get("CNO_AMC_API_KEY"))
    log.warning("amc_sink_unknown_kind; falling back to null", extra={"kind": kind})
    return NullSink()
