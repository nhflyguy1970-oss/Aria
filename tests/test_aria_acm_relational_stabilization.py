"""Stabilization repairs for autobiographical relational reasoning defects."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aria_core import acm_bridge, memory_manager
from jarvis.behaviors.memory.engine import MemoryEngine
from jarvis.nlu.mapping import resolve_memory_route


@pytest.fixture(autouse=True)
def _stab_isolation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ARIA_ACM_SHADOW", "0")
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_LEGACY_READ_FALLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "acm_stab.db"))
    monkeypatch.setenv("ARIA_ACM_AUTO_PERSIST", "1")
    monkeypatch.setenv("ARIA_TEACHING_DEBUG", "0")
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
    yield
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()


@pytest.mark.m3
def test_stab_00_version_pin() -> None:
    ver = Path(__file__).resolve().parents[1] / "aria_acm" / "VERSION.json"
    data = json.loads(ver.read_text())
    assert data["source_commit"] == "e6a71fb9d947a0b34402ec835e6a1e0665c8f9f8"
    assert data["aria_acm_local_version"] == "aria-acm-v0.45.0-1"
    assert data["promotion"] == "PLATFORM-PRACTICAL-COMPLETE"


@pytest.mark.m3
def test_stab_01_contextual_preference_overrides_only_in_context() -> None:
    for t in ("I prefer Python.", "For systems programming I prefer Rust."):
        result, speech = MemoryEngine._acm_authority_speak(t)
        assert "teaching_encoded" in (result.get("reasoning_path") or []), t
        assert speech.startswith("Okay, I'll remember"), speech

    result, speech = MemoryEngine._acm_authority_speak(
        "What programming language do I prefer?"
    )
    assert result.get("status") == "known"
    assert "python" in speech.lower()
    assert "rust" not in speech.lower()

    result, speech = MemoryEngine._acm_authority_speak(
        "What programming language do I prefer for systems programming?"
    )
    assert result.get("status") == "known"
    assert "rust" in speech.lower()
    assert "systems programming" in speech.lower()
    assert "python" not in speech.lower()


@pytest.mark.m3
def test_stab_02_repeated_goal_teaching_does_not_duplicate_active_goal() -> None:
    teaching = "My goal is to build the best local AI assistant possible."
    for _ in range(2):
        result, speech = MemoryEngine._acm_authority_speak(teaching)
        assert "teaching_encoded" in (result.get("reasoning_path") or [])
        assert speech.startswith("Okay, I'll remember")

    engine = acm_bridge.get_engine()
    titles = [g.title for g in engine.store.active_goals()]
    assert len(titles) == 1
    assert "best local ai assistant" in titles[0].lower()

    result, speech = MemoryEngine._acm_authority_speak("What is my long-term goal?")
    assert result.get("status") == "known"
    low = speech.lower()
    assert "best local ai assistant" in low
    assert low.count("best local ai assistant") == 1


@pytest.mark.m3
def test_stab_03_explainability_cites_supporting_upgrade_memory_not_ram() -> None:
    MemoryEngine._acm_authority_speak("Yesterday I upgraded my RAM.")
    MemoryEngine._acm_authority_speak(
        "I upgraded my desktop to train larger AI models."
    )

    result, speech = MemoryEngine._acm_authority_speak("Why did I upgrade my desktop?")
    assert result.get("status") == "known"
    assert "train larger ai models" in speech.lower()

    q = "How did you know why I upgraded my desktop?"
    routed = resolve_memory_route(q)
    assert routed is not None
    assert routed["action"] == "memory_about_user"

    result, speech = MemoryEngine._acm_authority_speak(q)
    assert result.get("status") == "known"
    low = speech.lower()
    assert "upgraded your desktop" in low or "upgraded my desktop" in low
    assert "train larger ai models" in low
    assert "ram" not in low
    assert "previously taught" in low or "remembered autobiographical" in low


@pytest.mark.m3
def test_stab_04_blackfly_after_building_project_label() -> None:
    """Prior 'I'm building BlackFly' must not hide part_of entity label."""
    MemoryEngine._acm_authority_speak("I'm building BlackFly.")
    MemoryEngine._acm_authority_speak("BlackFly is part of my AI ecosystem.")
    result, speech = MemoryEngine._acm_authority_speak(
        "How does BlackFly fit into my projects?"
    )
    assert result.get("status") == "known", speech
    low = speech.lower()
    assert "blackfly" in low
    assert "ecosystem" in low


@pytest.mark.m3
def test_stab_05_what_have_i_caught_routes_to_memory_authority() -> None:
    q = "What have I caught?"
    route = resolve_memory_route(q)
    assert route is not None
    assert route["action"] == "memory_about_user"
