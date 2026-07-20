"""M1 Aria integration polish — episodic routing, teaching ack, presentation."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jarvis.behaviors.memory.cognitive_presentation import (
    format_evidence_conversational,
    format_teaching_acknowledgement,
    polish_cognitive_speech,
)
from jarvis.behaviors.memory.engine import MemoryEngine
from jarvis.nlu.episodic_patterns import is_episodic_teaching
from jarvis.nlu.mapping import nlu_to_router_intent, resolve_memory_route
from jarvis.nlu.types import (
    GrammarAnalysis,
    MorphologyAnalysis,
    NLUResult,
    SemanticClassification,
    SyntaxAnalysis,
)
from jarvis.runtime_routing import is_runtime_routing_question, route_runtime_priority
from jarvis.session import SessionContext


TEACHINGS = (
    "Yesterday I bought a kayak.",
    "Yesterday I cleaned my garage.",
    "Last week I went fishing.",
    "This morning I installed a GPU.",
    "Last Tuesday I visited my brother.",
)


@pytest.fixture(autouse=True)
def _acm_primary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ARIA_ACM_SHADOW", "0")
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_LEGACY_READ_FALLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "m1_polish.db"))
    monkeypatch.setenv("ARIA_ACM_AUTO_PERSIST", "1")
    monkeypatch.setenv("ARIA_TEACHING_DEBUG", "0")
    from aria_core import acm_bridge, memory_manager

    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
    yield
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()


class _Ctx:
    session = SessionContext()
    memory = None

    def refresh_system_prompt(self) -> None:
        return None


def test_episodic_teaching_not_mission_control_gpu() -> None:
    prompt = "This morning I installed a GPU."
    assert is_episodic_teaching(prompt)
    resolved = resolve_memory_route(prompt)
    assert resolved is not None
    assert resolved["action"] == "memory_about_user"
    assert not is_runtime_routing_question(prompt)
    assert route_runtime_priority(prompt) is None

    nlu = NLUResult(
        prompt=prompt,
        grammar=GrammarAnalysis(sentence_type="declarative"),
        morphology=MorphologyAnalysis(),
        syntax=SyntaxAnalysis(),
        semantic=SemanticClassification(
            intent="runtime", action="install", subject="GPU", confidence=0.9, model="t"
        ),
    )
    intent = nlu_to_router_intent(nlu)
    assert intent is not None
    assert intent["action"] == "memory_about_user"


def test_gpu_operational_query_stays_runtime() -> None:
    prompt = "What is my GPU?"
    assert not is_episodic_teaching(prompt)
    assert resolve_memory_route(prompt) is None
    assert is_runtime_routing_question(prompt)


@pytest.mark.parametrize("prompt", TEACHINGS)
def test_episodic_teaching_acknowledgement(prompt: str) -> None:
    ack = format_teaching_acknowledgement(prompt)
    assert ack.startswith("Okay, I'll remember")
    assert "still learning" not in ack.lower()

    out = MemoryEngine.memory_about_user(_Ctx(), {"question": prompt}, prompt)
    body = (out.get("message") or "").lower()
    assert "still learning" not in body
    assert "okay, i'll remember" in body


def test_episodic_temporal_recall_routes_memory_authority() -> None:
    for q in (
        "What happened yesterday?",
        "What did I buy yesterday?",
        "What happened before buying the kayak?",
    ):
        resolved = resolve_memory_route(q)
        assert resolved is not None, q
        assert resolved["action"] == "memory_about_user", q


def test_conversational_presentation_polish() -> None:
    raw = "You bought a kayak (yesterday)."
    polished = polish_cognitive_speech(raw, {"status": "known"}, prompt="What did I buy yesterday?")
    assert "you bought a kayak" in polished.lower()
    assert "User " not in polished

    evidence = (
        "Evidence (preference lineage):\nfavorite color:\n"
        "  v1 blue (retired) — favorite color is blue\n"
        "  v2 green (active) — favorite color is green\n"
        "Episodic events:\n"
        "  - yesterday: Yesterday I bought a kayak.\n"
        "  - yesterday: Yesterday I cleaned my garage."
    )
    pretty = format_evidence_conversational(evidence)
    assert "Here's what I currently know" in pretty
    assert "Preferences" in pretty
    assert "Recent events" in pretty
    assert "kayak" in pretty.lower()
    assert "green" in pretty.lower()
    assert "Evidence (preference lineage)" not in pretty


def test_regression_preference_teaching_ack() -> None:
    out = MemoryEngine.memory_about_user(
        _Ctx(), {"question": "My favorite color is green."}, "My favorite color is green."
    )
    body = (out.get("message") or "").lower()
    assert "okay, i'll remember" in body
    assert "green" in body
    assert "still learning" not in body


def test_router_episodic_not_runtime() -> None:
    with patch("jarvis.runtime_introspection.get_runtime_client") as mock_client:
        mock_client.return_value = MagicMock()
        from jarvis.router import route

        intent = route("This morning I installed a GPU.", SessionContext(), None)
        assert intent.get("action") == "memory_about_user", intent
