"""End-to-end + per-node tests for CNO."""
import pytest
from cno.pipeline import CNOPipeline
from cno.nodes import (
    InputNode, RouterNode, MemoryNode, PersonaNode, OutputSynthNode,
    Modality, RequestType, Sublayer, PersonaStyle,
)


@pytest.fixture
def pipeline():
    p = CNOPipeline()
    p.memory.reset()
    return p


def test_input_node_classifies_question():
    node = InputNode()
    cls = node.classify("What is the meaning of canon entry 18?")
    assert cls.request_type == RequestType.QUESTION


def test_input_node_classifies_command():
    node = InputNode()
    cls = node.classify("Build the CNO codebase now.")
    assert cls.request_type == RequestType.COMMAND


def test_input_node_detects_voice_modality_from_slashes():
    node = InputNode()
    cls = node.classify("Do this. Then that. Then the other thing/")
    assert cls.modality == Modality.VOICE


def test_router_routes_question_to_analysis():
    cls = InputNode().classify("What time is it?")
    decision = RouterNode().route(cls)
    assert decision.sublayer == Sublayer.ANALYSIS


def test_router_routes_command_to_output():
    cls = InputNode().classify("Build it.")
    decision = RouterNode().route(cls)
    assert decision.sublayer == Sublayer.OUTPUT


def test_memory_node_anchors_in_order():
    m = MemoryNode()
    m.anchor("first")
    m.anchor("second")
    m.anchor("third")
    recent = m.recent(2)
    assert len(recent) == 2
    assert recent[-1].summary == "third"


def test_memory_node_max_depth_eviction():
    m = MemoryNode(max_depth=3)
    for i in range(5):
        m.anchor(f"item-{i}")
    assert len(m.all_anchors()) == 3
    assert m.all_anchors()[0].summary == "item-2"  # oldest two evicted


def test_persona_selection_for_command_is_direct():
    cls = InputNode().classify("Build it.")
    routing = RouterNode().route(cls)
    persona = PersonaNode().select(cls, routing)
    assert persona.style == PersonaStyle.DIRECT


def test_output_synth_clarity_score_in_range():
    persona_sel = PersonaNode().select(
        InputNode().classify("technical question?"),
        RouterNode().route(InputNode().classify("technical question?")),
    )
    synth = OutputSynthNode().synthesize("This is a clean short response.", persona_sel)
    assert 1 <= synth.clarity_score <= 100


def test_full_pipeline_runs_all_5_nodes(pipeline):
    result = pipeline.process("What is canon #18?")
    assert len(result.module_tags) == 5
    assert all(t.startswith("[") for t in result.module_tags)
    assert result.classification["request_type"] == "question"
    assert result.routing["sublayer"] == "Analytical Layer"


def test_pipeline_glyph_sequence(pipeline):
    result = pipeline.process("Do something now.")
    # Verify the 5 glyphs in order: input, router, memory, persona, output
    assert result.glyph_pipeline == "📥 → 🔄 → 🧊 → 🥥 → 📤"


def test_pipeline_anchors_request_in_memory(pipeline):
    pipeline.process("anchor me first")
    pipeline.process("anchor me second")
    anchors = pipeline.memory.recent(2)
    assert anchors[-1].summary.startswith("anchor me second")


def test_pipeline_with_voice_modality(pipeline):
    result = pipeline.process("Speak this. Then this. Then that/")
    assert result.classification["modality"] == "voice"
