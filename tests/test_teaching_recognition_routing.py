"""Live Teaching Recognition routing — declarative memory must not strip to search."""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.nlu.mapping import nlu_to_router_intent
from jarvis.nlu.types import (
    GrammarAnalysis,
    MorphologyAnalysis,
    NLUResult,
    SemanticClassification,
    SyntaxAnalysis,
)
from jarvis.routing_inspector import build_execution_flow, classify_route


def _memory_declarative(prompt: str, *, subject: str = "favorite color") -> NLUResult:
    """Reproduce the live NLU shape that caused the blue→green regression."""
    return NLUResult(
        prompt=prompt,
        grammar=GrammarAnalysis(sentence_type="declarative", mood="neutral"),
        morphology=MorphologyAnalysis(stems=prompt.lower().split()),
        syntax=SyntaxAnalysis(),
        semantic=SemanticClassification(
            intent="memory",
            action="remember facts",
            subject=subject,
            confidence=1.0,
            model="test",
            device="cpu",
        ),
    )


def test_declarative_teaching_routes_to_memory_authority_full_prompt() -> None:
    """NLU memory + declarative must not collapse to memory_search(subject)."""
    prompt = "My favorite color is green."
    intent = nlu_to_router_intent(_memory_declarative(prompt))
    assert intent is not None
    assert intent["action"] == "memory_about_user"
    assert intent["params"]["question"] == prompt
    assert intent["params"].get("query") != "favorite color"
    assert classify_route(intent["action"]) == "Memory"
    flow = build_execution_flow(
        prompt=prompt,
        intent=intent["action"],
        route="Memory",
        handler="MemoryStore",
        backend="Memory",
        stage="finalize",
    )
    assert "Teaching Recognition" in flow
    assert "Encode Authority" in flow


def test_interrogative_memory_routes_to_acm_recall() -> None:
    result = NLUResult(
        prompt="What is my favorite color?",
        grammar=GrammarAnalysis(sentence_type="interrogative", question_type="what"),
        morphology=MorphologyAnalysis(),
        syntax=SyntaxAnalysis(),
        semantic=SemanticClassification(
            intent="memory",
            action="recall",
            subject="favorite color",
            confidence=1.0,
            model="test",
        ),
    )
    # resolve_memory_route sends fact recall through ACM presentation (memory_about_user).
    intent = nlu_to_router_intent(result)
    assert intent is not None
    assert intent["action"] == "memory_about_user"
    assert intent["params"]["question"] == "What is my favorite color?"


def test_live_nlu_teaching_path_updates_preference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End-to-end: NLU-shaped declarative → memory_about_user → green supersedes blue."""
    monkeypatch.setenv("ARIA_ACM_SHADOW", "0")
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_LEGACY_READ_FALLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "teach_live.db"))
    monkeypatch.setenv("ARIA_ACM_AUTO_PERSIST", "1")
    monkeypatch.setenv("ARIA_TEACHING_DEBUG", "1")

    from aria_core import acm_bridge, memory_manager
    from jarvis.behaviors.memory.engine import MemoryEngine
    from jarvis.session import SessionContext

    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()

    # Prior state: blue (as in live certification)
    acm_bridge.primary_remember("My favorite color is blue.", entry_type="preference")
    before = acm_bridge.primary_cognitive_speak("What is my favorite color?")
    assert "blue" in (before.get("speech") or "").lower()

    # Exact live failure route shape → corrected action
    routed = nlu_to_router_intent(_memory_declarative("My favorite color is green."))
    assert routed is not None and routed["action"] == "memory_about_user"

    class _Ctx:
        session = SessionContext()
        memory = None

        def refresh_system_prompt(self) -> None:
            return None

    out = MemoryEngine.memory_about_user(
        _Ctx(), routed["params"], "My favorite color is green."
    )
    assert out.get("ok") is not False
    last = acm_bridge.last_primary_op()
    assert (last.get("teaching_recognition") or {}).get("teaching") is True
    assert "teaching_encoded" in (last.get("teaching_pipeline") or [])

    after = acm_bridge.primary_cognitive_speak("What is my favorite color?")
    assert "green" in (after.get("speech") or "").lower()
    assert "blue" not in (after.get("speech") or "").lower()

    engine = acm_bridge.get_engine()
    values = {
        (a.value, a.active)
        for c in engine.store.concepts.values()
        for a in c.attributes
        if a.key == "favorite_color"
    }
    assert values == {("blue", False), ("green", True)}

    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
