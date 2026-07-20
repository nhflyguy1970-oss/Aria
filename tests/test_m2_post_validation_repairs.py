"""Post-validation repair tests — presentation, routing, recall context."""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.behaviors.memory.cognitive_presentation import (
    format_preference_recall_conversational,
    polish_cognitive_speech,
)
from jarvis.nlu.episodic_patterns import (
    is_live_hardware_question,
    is_past_event_memory_question,
    reformulate_for_acm_recall,
)
from jarvis.nlu.mapping import resolve_memory_route
from jarvis.runtime_routing import is_runtime_routing_question, route_runtime_priority


@pytest.fixture(autouse=True)
def _acm_primary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ARIA_ACM_SHADOW", "0")
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_LEGACY_READ_FALLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "repair.db"))
    monkeypatch.setenv("ARIA_ACM_AUTO_PERSIST", "1")
    from aria_core import acm_bridge, memory_manager

    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
    yield
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()


def test_live_hardware_not_memory_route() -> None:
    for msg in (
        "How much RAM is installed?",
        "What GPU do I have?",
        "What CPU do I have?",
        "How much VRAM is available?",
        "Show GPU status.",
    ):
        assert is_live_hardware_question(msg)
        assert resolve_memory_route(msg) is None
        assert is_runtime_routing_question(msg)
        assert route_runtime_priority(msg) is not None


def test_past_event_recall_not_mission_control() -> None:
    msg = "Did I tell you what GPU I installed yesterday?"
    assert is_past_event_memory_question(msg)
    assert not is_runtime_routing_question(msg)
    resolved = resolve_memory_route(msg)
    assert resolved and resolved["action"] == "memory_about_user"


def test_autobiographical_teaching_unchanged() -> None:
    msg = "This morning I installed a GPU."
    resolved = resolve_memory_route(msg)
    assert resolved and resolved["action"] == "memory_about_user"
    assert not is_runtime_routing_question(msg)


def test_preference_presentation() -> None:
    out = format_preference_recall_conversational("Your favorite color is blue.")
    assert out == "You told me your favorite color is blue."
    out2 = polish_cognitive_speech("Your favorite color is blue.")
    assert "You told me" in out2


def test_reformulate_did_i_tell() -> None:
    assert reformulate_for_acm_recall("Did I tell you what GPU I installed yesterday?") == (
        "What did I install yesterday?"
    )


def test_acm_recall_full_context_gpu_question() -> None:
    from aria_core import acm_bridge
    from jarvis.behaviors.memory.engine import MemoryEngine

    acm_bridge.primary_cognitive_speak("Yesterday I installed a GPU.")
    _result, speech = MemoryEngine._acm_authority_speak(
        "Did I tell you what GPU I installed yesterday?"
    )
    assert "GPU" in speech
    assert "yesterday" in speech.lower()
    assert "•" not in speech
    assert not speech.lower().startswith("memory")


def test_favorite_color_routes_to_memory_authority() -> None:
    resolved = resolve_memory_route("What is my favorite color?")
    assert resolved and resolved["action"] == "memory_about_user"


def test_duplicate_kayak_is_acm_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Repeated teachings create separate ACM experiences — document, do not dedupe in ACM."""
    from aria_core import acm_bridge

    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "dup.db"))
    acm_bridge.reset_for_tests()
    for _ in range(2):
        acm_bridge.primary_cognitive_speak("Yesterday I bought a kayak.")
    cog = acm_bridge.primary_cognitive_speak("What happened yesterday?")
    speech = cog.get("speech") or ""
    assert speech.count("kayak") >= 2
