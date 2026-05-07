"""Slice 7 — heuristic-upgraded node quality + LLMClassifier hook tests."""
from cno.llm import LLMClassifier
from cno.nodes import (
    InputNode, RouterNode, PersonaNode, OutputSynthNode,
    Modality, RequestType, Sublayer, PersonaStyle,
)
from cno.nodes.input_node import Tone


# --- InputNode confidence + lexicon ---

def test_input_classification_carries_confidences():
    cls = InputNode().classify("What time is it?")
    assert cls.modality_confidence > 0
    assert cls.request_type_confidence > 0
    assert cls.tone_confidence > 0


def test_input_detects_urgent_via_lexicon():
    cls = InputNode().classify("we need this asap, time-critical bug")
    assert cls.tone == Tone.URGENT
    assert cls.tone_confidence >= 0.65


def test_input_detects_reflective_via_lexicon():
    cls = InputNode().classify("Take a moment to reflect on the deeper meaning here.")
    assert cls.tone == Tone.REFLECTIVE


def test_input_detects_abstract_request():
    cls = InputNode().classify("Imagine a world where compilers dream.")
    assert cls.request_type == RequestType.ABSTRACT


def test_input_neutral_when_no_lexicon_hit():
    cls = InputNode().classify("file checked in")
    assert cls.tone == Tone.NEUTRAL


# --- LLM hook ---

class FakeLLM:
    name = "fake"
    def __init__(self, payload): self._p = payload
    def classify(self, _text, _schema): return self._p


def test_input_uses_llm_classifier_when_provided():
    fake = FakeLLM({"modality": "voice", "request_type": "command", "tone": "urgent"})
    cls = InputNode(llm=fake).classify("hand off to the orchestrator now")
    assert cls.modality == Modality.VOICE
    assert cls.request_type == RequestType.COMMAND
    assert cls.tone == Tone.URGENT


def test_input_falls_back_to_heuristics_on_llm_error():
    class Broken:
        def classify(self, *_): raise RuntimeError("boom")
    cls = InputNode(llm=Broken()).classify("What is canon #18?")
    assert cls.request_type == RequestType.QUESTION  # heuristic still ran


def test_llm_classifier_protocol_runtime_check():
    assert isinstance(FakeLLM({}), LLMClassifier)


# --- PersonaNode scoring ---

def test_persona_command_scores_to_direct():
    cls = InputNode().classify("Build it now.")
    routing = RouterNode().route(cls)
    persona = PersonaNode().select(cls, routing)
    assert persona.style == PersonaStyle.DIRECT
    assert persona.confidence >= 0.6
    assert "score" in persona.rationale


def test_persona_long_analysis_scores_to_academic():
    long_text = "Why " + ("about the substrate of cognition? " * 60)
    cls = InputNode().classify(long_text)
    routing = RouterNode().route(cls)
    persona = PersonaNode().select(cls, routing)
    assert routing.sublayer == Sublayer.ANALYSIS
    assert persona.style in (PersonaStyle.ACADEMIC, PersonaStyle.TECHNICAL)


def test_persona_reflective_routes_to_visionary_or_poetic():
    # Use a strong reflective signal to push routing into the Reflective Layer.
    cls = InputNode().classify("What if we ponder the deeper meaning here, and reflect philosophically?")
    routing = RouterNode().route(cls)
    persona = PersonaNode().select(cls, routing)
    assert routing.sublayer == Sublayer.REFLECTION
    assert persona.style in (PersonaStyle.VISIONARY, PersonaStyle.POETIC)


# --- OutputSynth transformations ---

def test_synth_direct_strips_hedges():
    persona = PersonaSelection_for(PersonaStyle.DIRECT)
    out = OutputSynthNode().synthesize("perhaps we should maybe try this approach", persona)
    assert "perhaps" not in out.body.lower()
    assert "maybe" not in out.body.lower()
    assert "hedges_stripped" in out.transforms


def test_synth_technical_bulletizes_long_drafts():
    persona = PersonaSelection_for(PersonaStyle.TECHNICAL)
    draft = "First step. Second step. Third step. Fourth step."
    out = OutputSynthNode().synthesize(draft, persona)
    assert out.body.startswith("- ")
    assert "bulletized" in out.transforms


def test_synth_clarity_drops_on_passive_and_filler():
    persona = PersonaSelection_for(PersonaStyle.MENTOR)
    bad = "It was actually really considered that the result was basically computed by the system."
    good = "The system computed the result."
    sa = OutputSynthNode().synthesize(bad,  persona).clarity_score
    sb = OutputSynthNode().synthesize(good, persona).clarity_score
    assert sb > sa


def test_synth_clarity_bonus_for_structure():
    persona = PersonaSelection_for(PersonaStyle.MENTOR)
    structured = "Heading\n\n- one\n- two\n- three"
    out = OutputSynthNode().synthesize(structured, persona)
    assert out.clarity_score >= 95


# --- helpers ---

from cno.nodes.persona_node import PersonaSelection
def PersonaSelection_for(style: PersonaStyle) -> PersonaSelection:
    return PersonaSelection(style=style, rationale="test", confidence=1.0)
