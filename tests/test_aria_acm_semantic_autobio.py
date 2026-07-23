"""Semantic autobiographical memory — Aria host promotion gates.

Vendored ACM cognition is unchanged; these tests verify Memory Authority routing,
teaching recognition on the normal conversation path, and immediate recall.
"""

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
    "I'm working on Aria.",
    "I'm building BlackFly.",
    "My desktop has an RTX 3060.",
    "I prefer local AI models.",
    "I like step-by-step debugging.",
)


@pytest.fixture(autouse=True)
def _sem_isolation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ARIA_ACM_SHADOW", "0")
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_LEGACY_READ_FALLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "acm_sem.db"))
    monkeypatch.setenv("ARIA_ACM_AUTO_PERSIST", "1")
    monkeypatch.setenv("ARIA_TEACHING_DEBUG", "0")
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
    yield
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()


@pytest.mark.m3
def test_sem_01_version_pin() -> None:
    ver = Path(__file__).resolve().parents[1] / "aria_acm" / "VERSION.json"
    data = json.loads(ver.read_text())
    assert data["source_commit"] == "6185854e2adf56aabc13d26f6a51d9fce660a01a"
    assert data["aria_acm_local_version"] == "aria-acm-v0.33.0-1"
    assert data["promotion"] == "M5-ACM-CAP6-EXPLAIN"
    assert (Path("aria_acm/acm/remembering/semantic.py")).is_file()
    assert (Path("aria_acm/acm/remembering/evolution.py")).is_file()
    assert (Path("aria_acm/acm/remembering/relations.py")).is_file()


@pytest.mark.m3
def test_sem_02_routing_to_memory_authority() -> None:
    for t in TEACHINGS:
        assert is_semantic_autobio_teaching(t), t
        resolved = resolve_memory_route(t)
        assert resolved is not None, t
        assert resolved["action"] == "memory_about_user", t

    for q in (
        "What operating system does my laptop use?",
        "What projects am I working on?",
        "What AI projects have I been building?",
        "Tell me what you know about my computer.",
        "Tell me what you know about my AI setup.",
        "Do I prefer local AI models or cloud models?",
        "What kind of responses do I like when debugging?",
        "Summarize what you know about me.",
        "Which computer would probably be better for training larger AI models?",
    ):
        assert is_semantic_autobio_query(q) or resolve_memory_route(q), q
        resolved = resolve_memory_route(q)
        assert resolved is not None, q
        assert resolved["action"] == "memory_about_user", q


@pytest.mark.m3
def test_sem_03_teach_and_recall_via_memory_engine() -> None:
    """Normal Memory Authority path — no programmatic seeding fixtures."""
    for t in TEACHINGS:
        result, speech = MemoryEngine._acm_authority_speak(t)
        assert "teaching_encoded" in (result.get("reasoning_path") or []), t
        assert speech.startswith("Okay, I'll remember"), speech

    cases = [
        ("What operating system does my laptop use?", ("zorin", "laptop")),
        ("What projects am I working on?", ("aria", "blackfly")),
        ("What AI projects have I been building?", ("aria", "blackfly")),
        ("Tell me what you know about my computer.", ("laptop", "zorin")),
        ("Tell me what you know about my AI setup.", ("local",)),
        ("Do I prefer local AI models or cloud models?", ("local",)),
        ("What kind of responses do I like when debugging?", ("step-by-step",)),
        ("Summarize what you know about me.", ("zorin", "aria", "local")),
        (
            "Which computer would probably be better for training larger AI models?",
            ("desktop", "3060"),
        ),
    ]
    for q, needles in cases:
        result, speech = MemoryEngine._acm_authority_speak(q)
        assert result.get("status") == "known", q
        low = speech.lower()
        for n in needles:
            assert n in low, (q, speech, n)


@pytest.mark.m3
def test_sem_04_unknown_boundary() -> None:
    for t in TEACHINGS:
        MemoryEngine._acm_authority_speak(t)
    result, speech = MemoryEngine._acm_authority_speak(
        "What operating system does my phone use?"
    )
    assert result.get("status") == "unknown"
    assert "don't currently know" in speech.lower()
    assert "ubuntu" not in speech.lower()
    assert "zorin" not in speech.lower()
