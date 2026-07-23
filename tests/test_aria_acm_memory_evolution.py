"""Memory evolution — Aria host promotion gates (vendored ACM + routing)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aria_core import acm_bridge, memory_manager
from jarvis.behaviors.memory.engine import MemoryEngine
from jarvis.nlu.mapping import resolve_memory_route
from jarvis.nlu.semantic_autobio_patterns import (
    is_semantic_autobio_query,
    is_semantic_autobio_teaching,
)


TEACHINGS = (
    "My laptop runs Zorin.",
    "My laptop runs Fedora.",
    "I prefer local AI models.",
    "I now prefer cloud AI models.",
    "I'm working on Aria.",
    "I'm building BlackFly.",
    "BlackFly is finished.",
    "I'm now working on HouseFly.",
    "My desktop has an RTX 3060.",
    "My desktop has an RTX 4070.",
    "I no longer use my laptop.",
    "My phone is a Pixel 10.",
)


@pytest.fixture(autouse=True)
def _evo_isolation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ARIA_ACM_SHADOW", "0")
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_LEGACY_READ_FALLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "acm_evo.db"))
    monkeypatch.setenv("ARIA_ACM_AUTO_PERSIST", "1")
    monkeypatch.setenv("ARIA_TEACHING_DEBUG", "0")
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
    yield
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()


@pytest.mark.m3
def test_evo_01_version_pin() -> None:
    ver = Path(__file__).resolve().parents[1] / "aria_acm" / "VERSION.json"
    data = json.loads(ver.read_text())
    assert data["source_commit"] == "e6a71fb9d947a0b34402ec835e6a1e0665c8f9f8"
    assert data["aria_acm_local_version"] == "aria-acm-v0.45.0-1"
    assert data["promotion"] == "PLATFORM-PRACTICAL-COMPLETE"
    assert Path("aria_acm/acm/remembering/evolution.py").is_file()
    assert Path("aria_acm/acm/remembering/relations.py").is_file()


@pytest.mark.m3
def test_evo_02_lifecycle_routing() -> None:
    for t in TEACHINGS:
        assert is_semantic_autobio_teaching(t), t
        resolved = resolve_memory_route(t)
        assert resolved is not None, t
        assert resolved["action"] == "memory_about_user", t

    for q in (
        "What operating systems has my laptop used?",
        "Have my AI preferences changed?",
        "What projects have I worked on?",
        "Has my desktop hardware changed?",
        "Tell me about my computers.",
        "How has my AI setup changed over time?",
        "What phone do I own?",
    ):
        assert is_semantic_autobio_query(q), q
        resolved = resolve_memory_route(q)
        assert resolved is not None, q
        assert resolved["action"] == "memory_about_user", q


@pytest.mark.m3
def test_evo_03_teach_and_historical_recall() -> None:
    for t in TEACHINGS:
        result, speech = MemoryEngine._acm_authority_speak(t)
        assert "teaching_encoded" in (result.get("reasoning_path") or []), t
        assert speech.startswith("Okay, I'll remember"), speech

    cases = [
        ("What operating systems has my laptop used?", ("zorin", "fedora")),
        ("Do I prefer local AI or cloud AI?", ("cloud",)),
        ("Have my AI preferences changed?", ("yes", "local", "cloud")),
        ("What projects am I working on?", ("aria", "housefly")),
        ("What projects have I worked on?", ("blackfly", "aria", "housefly")),
        ("Has my desktop hardware changed?", ("3060", "4070")),
        ("Tell me about my computers.", ("current", "historical", "desktop")),
        ("How has my AI setup changed over time?", ("finished", "housefly")),
        ("What phone do I own?", ("pixel",)),
    ]
    for q, needles in cases:
        result, speech = MemoryEngine._acm_authority_speak(q)
        assert result.get("status") == "known", (q, speech)
        low = speech.lower()
        for n in needles:
            assert n in low, (q, speech, n)
        if q.startswith("What projects am I"):
            assert "blackfly" not in low
