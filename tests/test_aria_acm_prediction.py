"""Prediction manual-acceptance gates through Aria Memory Authority."""

from __future__ import annotations

from jarvis.behaviors.memory.engine import MemoryEngine
from jarvis.nlu.mapping import resolve_memory_route
from jarvis.nlu.semantic_autobio_patterns import (
    is_semantic_autobio_query,
    is_semantic_autobio_teaching,
)

TEACHINGS = (
    "It has rained every day this week.",
    "Every time I drink coffee after 8 PM, I have trouble sleeping.",
    "Whenever I skip breakfast, I get hungry before lunch.",
    "Every Saturday I usually go fishing.",
    "I usually get more work done in the morning.",
    "Every weekend for the last year I have gone hiking.",
)

PREDICTION_QUERIES = (
    "What am I likely to do next Saturday?",
    "When am I likely to be most productive?",
    "If I drink coffee after 8 PM, what is likely to happen?",
    "Why do you think that is likely?",
    "What will happen in the stock market tomorrow?",
    "Will it rain tomorrow?",
)


def test_habit_teachings_route_to_memory_authority() -> None:
    for text in TEACHINGS:
        assert is_semantic_autobio_teaching(text), text
        route = resolve_memory_route(text)
        assert route is not None, text
        assert route["action"] == "memory_about_user", text


def test_prediction_queries_route_to_memory_authority() -> None:
    for q in PREDICTION_QUERIES:
        assert is_semantic_autobio_query(q), q
        route = resolve_memory_route(q)
        assert route is not None, q
        assert route["action"] == "memory_about_user", q


def test_prediction_manual_acceptance_via_acm_authority() -> None:
    for text in TEACHINGS:
        result, speech = MemoryEngine._acm_authority_speak(text)
        assert "teaching_encoded" in (result.get("reasoning_path") or []), text
        assert speech.startswith("Okay, I'll remember"), speech

    saturday = MemoryEngine._acm_authority_speak("What am I likely to do next Saturday?")
    assert saturday[0].get("status") == "known"
    assert "fishing" in saturday[1].lower()

    productive = MemoryEngine._acm_authority_speak(
        "When am I likely to be most productive?"
    )
    assert productive[0].get("status") == "known"
    assert "work" in productive[1].lower()

    rain = MemoryEngine._acm_authority_speak("Will it rain tomorrow?")
    assert rain[0].get("status") == "known"
    assert "rain" in rain[1].lower()

    market = MemoryEngine._acm_authority_speak(
        "What will happen in the stock market tomorrow?"
    )
    assert market[0].get("status") == "unknown"
    assert "don't currently know" in market[1].lower()


def test_prediction_conflict_and_explainability() -> None:
    MemoryEngine._acm_authority_speak(
        "Every time I drink coffee after 8 PM, I have trouble sleeping."
    )
    MemoryEngine._acm_authority_speak("Coffee causes insomnia.")
    MemoryEngine._acm_authority_speak("Coffee sometimes helps me sleep.")
    conflict = MemoryEngine._acm_authority_speak(
        "If I drink coffee after 8 PM, what is likely to happen?"
    )
    assert conflict[0].get("status") == "conflicting"
    assert "conflict" in conflict[1].lower()
    assert conflict[0].get("confidence", 1.0) <= 0.45

    why = MemoryEngine._acm_authority_speak("Why do you think that is likely?")
    assert why[0].get("intent") == "prediction"
    assert "coffee" in why[1].lower()
    assert "taught" in why[1].lower() or "previously" in why[1].lower()
