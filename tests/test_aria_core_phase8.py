"""Phase 8 — Reflex Layer before cognition."""

from __future__ import annotations

import time
from pathlib import Path

from aria_core.event_bus import get_bus, recent_events
from aria_core.event_contracts import validate_contracts
from aria_core.ownership import OWNERSHIP
from aria_core.reflex import (
    evaluate,
    is_reflex,
    mission_control_panel,
    reflex_statistics,
    reset_for_tests,
    try_reflex,
)


def setup_function():
    reset_for_tests()
    get_bus().reset_for_tests()


def test_reflex_owned_by_core():
    assert OWNERSHIP["reflex"]["source_of_truth"] == "aria_core.reflex_engine"


def test_greetings_and_controls_match():
    cases = {
        "Hello Aria": ("social.greeting", "greeting"),
        "Hi": ("social.greeting", "greeting"),
        "Good morning": ("social.greeting", "greeting"),
        "How are you?": ("social.checkin", "greeting"),
        "What's up": ("social.checkin", "greeting"),
        "bye": ("social.farewell", "reflex_reply"),
        "thanks": ("social.ack", "reflex_reply"),
        "yes": ("social.confirm", "reflex_reply"),
        "no": ("social.negate", "reflex_reply"),
        "stop": ("session.interrupt", "session_interrupt"),
        "continue": ("session.continue", "session_continue"),
        "repeat": ("session.repeat", "session_repeat"),
        "help": ("meta.help", "capabilities"),
        "clear": ("session.clear", "clear"),
        "good morning briefing": ("briefing.morning", "morning_briefing"),
        "open mission control": ("ui.mission_control", "status_summary"),
    }
    for msg, (cat, action) in cases.items():
        hit = evaluate(msg)
        assert hit, msg
        assert hit["category"] == cat, msg
        assert hit["action"] == action, msg


def test_non_reflex_escalates():
    assert evaluate("What is quantum computing?") is None
    assert evaluate("remember that I like green tea") is None
    intent = try_reflex("Explain recursion with examples")
    assert intent is None
    stats = reflex_statistics()
    assert stats["escalated"] >= 1


def test_try_reflex_intent_and_events():
    intent = try_reflex("Hello Aria")
    assert intent["action"] == "greeting"
    assert intent["router"] == "reflex"
    assert intent["router_stage"] == "pre_nlu_reflex"
    assert intent["reflex_confidence"] >= 0.9
    names = {e["name"] for e in recent_events(limit=20)}
    assert "ReflexMatched" in names
    assert "ReflexLatency" in names


def test_latency_targets():
    for msg, budget in (
        ("Hello Aria", 10),
        ("yes", 10),
        ("stop", 20),
        ("open mission control", 50),
    ):
        t0 = time.perf_counter()
        hit = evaluate(msg)
        ms = (time.perf_counter() - t0) * 1000
        assert hit, msg
        assert ms < budget, f"{msg!r} took {ms:.1f}ms (budget {budget})"


def test_router_uses_reflex_before_nlu(monkeypatch):
    from jarvis.router import route
    from jarvis.session import SessionContext

    calls = {"nlu": 0}

    def _boom(*_a, **_k):
        calls["nlu"] += 1
        raise AssertionError("NLU must not run for reflexes")

    monkeypatch.setattr("jarvis.nlu.pipeline.route_via_nlu", _boom)
    monkeypatch.setattr("jarvis.nlu.pipeline.nlu_enabled", lambda: True)
    intent = route("Hello Aria", SessionContext())
    assert intent["action"] == "greeting"
    assert intent.get("router_stage") == "pre_nlu_reflex"
    assert calls["nlu"] == 0


def test_mission_control_panel():
    try_reflex("Hi")
    try_reflex("Explain gravity")
    panel = mission_control_panel(limit=20)
    assert panel["owner"] == "aria_core.reflex"
    assert "hit_rate" in panel
    assert "top_categories" in panel
    assert "history" in panel


def test_event_contracts_include_reflex():
    assert validate_contracts() == []


def test_is_reflex_compat():
    assert is_reflex("Hello")
    assert not is_reflex("Write a sorting algorithm")


def test_phase8_docs_exist():
    root = Path(__file__).resolve().parents[1] / "docs" / "aria_core"
    for name in ("PHASE8.md", "REFLEX.md"):
        assert (root / name).is_file(), name
