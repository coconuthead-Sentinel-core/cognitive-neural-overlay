"""ArchivalSink + MemoryNode integration tests."""
import json
import shutil
import tempfile
from pathlib import Path

import pytest

from cno.nodes import MemoryNode
from cno.sinks import (
    ArchivalSink, NullSink, JsonlSink, HttpAMCSink,
    load_sink_from_env,
)


@pytest.fixture
def tmp_dir():
    """Manual temp dir — pytest's tmp_path runs into Windows permission issues here."""
    d = Path(tempfile.mkdtemp(prefix="cno_sink_test_"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


# --- protocol ---

def test_all_concrete_sinks_satisfy_protocol(tmp_dir):
    assert isinstance(NullSink(), ArchivalSink)
    assert isinstance(JsonlSink(tmp_dir / "x.jsonl"), ArchivalSink)


# --- NullSink ---

def test_null_sink_is_silent():
    NullSink().persist({"summary": "anything"})  # must not raise


# --- JsonlSink ---

def test_jsonl_sink_appends_one_line_per_anchor(tmp_dir):
    p = tmp_dir / "anchors.jsonl"
    sink = JsonlSink(p)
    sink.persist({"summary": "first",  "tone": "neutral"})
    sink.persist({"summary": "second", "tone": "urgent"})
    lines = p.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["summary"] == "first"
    assert json.loads(lines[1])["tone"]    == "urgent"


def test_jsonl_sink_creates_parent_dir(tmp_dir):
    p = tmp_dir / "nested" / "dir" / "anchors.jsonl"
    sink = JsonlSink(p)
    sink.persist({"summary": "ok"})
    assert p.exists()


# --- factory ---

def test_load_sink_from_env_default_is_null(monkeypatch):
    monkeypatch.delenv("CNO_AMC_SINK", raising=False)
    assert isinstance(load_sink_from_env(), NullSink)


def test_load_sink_from_env_jsonl(monkeypatch, tmp_dir):
    monkeypatch.setenv("CNO_AMC_SINK", "jsonl")
    monkeypatch.setenv("CNO_AMC_JSONL_PATH", str(tmp_dir / "anchors.jsonl"))
    sink = load_sink_from_env()
    assert isinstance(sink, JsonlSink)


def test_load_sink_from_env_http_falls_back_when_no_url(monkeypatch):
    monkeypatch.setenv("CNO_AMC_SINK", "http")
    monkeypatch.delenv("CNO_AMC_URL", raising=False)
    assert isinstance(load_sink_from_env(), NullSink)


def test_load_sink_from_env_unknown_falls_back(monkeypatch):
    monkeypatch.setenv("CNO_AMC_SINK", "telepathy")
    assert isinstance(load_sink_from_env(), NullSink)


# --- MemoryNode integration ---

def test_memory_node_calls_sink_on_each_anchor(tmp_dir):
    p = tmp_dir / "anchors.jsonl"
    m = MemoryNode(sink=JsonlSink(p))
    m.anchor("first")
    m.anchor("second")
    lines = p.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2


def test_memory_node_sink_failure_does_not_break_anchor():
    class Boom:
        name = "boom"
        def persist(self, _): raise RuntimeError("boom")
    m = MemoryNode(sink=Boom())
    a = m.anchor("survives")  # must not raise
    assert a.summary == "survives"
    assert m.recent(1)[0].summary == "survives"


def test_memory_node_without_sink_still_works():
    m = MemoryNode(sink=None)
    a = m.anchor("plain")
    assert a.summary == "plain"


# --- HTTP sink (defensive smoke) ---

def test_http_sink_post_failure_swallowed():
    """No real network; assert that connect-refused-style errors don't propagate."""
    sink = HttpAMCSink("http://127.0.0.1:1/")  # port 1 = nothing listening
    sink.persist({"summary": "no-route"})  # must not raise
