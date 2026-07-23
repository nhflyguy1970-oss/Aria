"""Autobiographical relational reasoning — Aria host promotion gates.

Vendored ACM cognition is unchanged; these tests verify Memory Authority
routing and end-to-end teach/recall for autobiographical relationships.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aria_core import acm_bridge, memory_manager
from jarvis.behaviors.memory.engine import MemoryEngine
from jarvis.capability_routing import capability_for_action_and_message
from jarvis.nlu.mapping import resolve_memory_route
from jarvis.nlu.semantic_autobio_patterns import (
    is_semantic_autobio_query,
    is_semantic_autobio_teaching,
)


TEACHINGS = (
    "I upgraded my desktop to train larger AI models.",
    "My goal is to build the best local AI assistant possible.",
    "I'm building Aria to achieve that goal.",
    "BlackFly is part of my AI ecosystem.",
    "Aria uses ACM.",
    "I prefer local AI because I value privacy.",
    "I prefer Python.",
    "For systems programming I prefer Rust.",
)

RELATIONAL_QUERIES = (
    "Why did I upgrade my desktop?",
    "Why am I building Aria?",
    "How does Aria relate to my goal?",
    "How are Aria and ACM related?",
    "How does BlackFly fit into my projects?",
    "Why do I prefer local AI?",
    "Would cloud AI usually fit my preferences?",
    "Would this fit my preferences?",
    "Which of my computers should I use for training AI?",
    "What programming language do I prefer?",
    "What language do I prefer for systems programming?",
    "What is my long-term goal?",
    "Why is my desktop better for AI than my laptop?",
    "Which should I use for software development?",
    "Why did I buy my phone?",
)


@pytest.fixture(autouse=True)
def _rel_isolation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ARIA_ACM_SHADOW", "0")
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_LEGACY_READ_FALLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "acm_rel.db"))
    monkeypatch.setenv("ARIA_ACM_AUTO_PERSIST", "1")
    monkeypatch.setenv("ARIA_TEACHING_DEBUG", "0")
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
    yield
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()


@pytest.mark.m3
def test_rel_01_version_pin() -> None:
    ver = Path(__file__).resolve().parents[1] / "aria_acm" / "VERSION.json"
    data = json.loads(ver.read_text())
    assert data["source_commit"] == "b720cbb32d36f61af5287adef1aac0a4d5d5b7f2"
    assert data["aria_acm_local_version"] == "aria-acm-v0.45.1-1"
    assert data["promotion"] == "PLATFORM-PRACTICAL-COMPLETE"
    assert Path("aria_acm/acm/remembering/relations.py").is_file()


@pytest.mark.m3
def test_rel_02_routing_to_memory_authority() -> None:
    for t in TEACHINGS:
        assert is_semantic_autobio_teaching(t), t
        resolved = resolve_memory_route(t)
        assert resolved is not None, t
        assert resolved["action"] == "memory_about_user", t
        assert (
            capability_for_action_and_message("memory_about_user", t)
            == "episodic_teaching"
        ), t

    for q in RELATIONAL_QUERIES:
        assert is_semantic_autobio_query(q), q
        resolved = resolve_memory_route(q)
        assert resolved is not None, q
        assert resolved["action"] == "memory_about_user", q
        assert (
            capability_for_action_and_message("memory_about_user", q)
            == "episodic_recall"
        ), q
        assert resolved["action"] not in (
            "web_search",
            "reference_search",
            "runtime_status",
            "chat",
        )


@pytest.mark.m3
def test_rel_03_teach_and_relational_recall() -> None:
    for t in TEACHINGS:
        result, speech = MemoryEngine._acm_authority_speak(t)
        assert "teaching_encoded" in (result.get("reasoning_path") or []), t
        assert speech.startswith("Okay, I'll remember"), speech

    cases = [
        ("Why did I upgrade my desktop?", ("train larger ai models",)),
        ("What is my long-term goal?", ("best local ai assistant",)),
        ("Why am I building Aria?", ("aria", "building the best local ai assistant")),
        ("How does Aria relate to my goal?", ("aria", "building the best local ai assistant")),
        ("How are Aria and ACM related?", ("aria uses acm",)),
        ("How does BlackFly fit into my projects?", ("blackfly", "ai ecosystem")),
        ("Why do I prefer local AI?", ("local ai", "privacy")),
        ("Would cloud AI usually fit my preferences?", ("would not", "local ai", "privacy")),
        ("What programming language do I prefer?", ("python",)),
        ("What language do I prefer for systems programming?", ("rust", "systems programming")),
        (
            "What programming language do I prefer for systems programming?",
            ("rust", "systems programming"),
        ),
        ("Why is my desktop better for AI than my laptop?", ("desktop", "train larger ai models")),
        (
            "Which of my computers should I use for training AI?",
            ("desktop", "train larger ai models"),
        ),
    ]
    for q, needles in cases:
        result, speech = MemoryEngine._acm_authority_speak(q)
        assert result.get("status") == "known", (q, speech)
        low = speech.lower()
        for n in needles:
            assert n in low, (q, speech, n)
        if q == "What programming language do I prefer?":
            assert "rust" not in low
        if "for systems programming" in q:
            assert "python" not in low


@pytest.mark.m3
def test_rel_04_unknown_without_autobiographical_evidence() -> None:
    for t in TEACHINGS:
        MemoryEngine._acm_authority_speak(t)

    for q in (
        "Why am I working on HouseFly?",
        "Which should I use for software development?",
        "Why did I buy my phone?",
    ):
        result, speech = MemoryEngine._acm_authority_speak(q)
        assert result.get("status") == "unknown", (q, speech)
        assert "don't currently know" in speech.lower(), (q, speech)
