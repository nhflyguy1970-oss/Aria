"""Prediction stabilization — post-promotion acceptance regressions."""

from __future__ import annotations

import re

from jarvis.behaviors.memory.engine import MemoryEngine
from jarvis.lang_util import (
    conversation_language,
    enforce_reply_language,
    is_language_mismatch,
)
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
    "Coffee causes insomnia.",
    "Sometimes coffee helps me sleep.",
)

PREDICTION_QUERIES = (
    "What is likely to happen tomorrow?",
    "What am I likely to do next Saturday?",
    "When am I likely to be most productive?",
    "If I drink coffee after 8 PM, what is likely to happen?",
    "Why do you think that is likely?",
    "How did you make that prediction?",
    "Will I definitely go fishing next Saturday?",
    "When SHOULD I work?",
    "What am I likely to do on my birthday next year?",
    "How confident are you that I'll go hiking this weekend?",
    "What will happen in the stock market tomorrow?",
    "Will it rain tomorrow?",
)

_SCORE_LEAK = re.compile(
    r"(~\d+%\)|goal\s*\(~|pattern\s*\(~|user\s*\(~|when\s*\(~)",
    re.I,
)
_CJK = re.compile(r"[\u4e00-\u9fff]")


def test_recurring_teachings_route_to_memory_authority() -> None:
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


def test_prediction_stabilization_acceptance() -> None:
    for text in TEACHINGS:
        result, speech = MemoryEngine._acm_authority_speak(text)
        assert "teaching_encoded" in (result.get("reasoning_path") or []), text
        assert speech.startswith("Okay, I'll remember"), speech
        assert not _CJK.search(speech), speech

    rain = MemoryEngine._acm_authority_speak("What is likely to happen tomorrow?")
    assert rain[0].get("status") == "known"
    assert "rain" in rain[1].lower()
    assert not _SCORE_LEAK.search(rain[1]), rain[1]

    saturday = MemoryEngine._acm_authority_speak(
        "Will I definitely go fishing next Saturday?"
    )
    assert saturday[0].get("intent") == "prediction"
    assert "fishing" in saturday[1].lower()
    assert "certain" in saturday[1].lower() or "definite" in saturday[1].lower()

    MemoryEngine._acm_authority_speak("What am I likely to do next Saturday?")
    why = MemoryEngine._acm_authority_speak("How did you make that prediction?")
    assert why[0].get("intent") == "prediction"
    assert "fishing" in why[1].lower() or "taught" in why[1].lower()
    assert "aria to achieve" not in why[1].lower()

    work = MemoryEngine._acm_authority_speak("When SHOULD I work?")
    assert work[0].get("intent") == "prediction"
    assert "work" in work[1].lower()

    bday = MemoryEngine._acm_authority_speak(
        "What am I likely to do on my birthday next year?"
    )
    assert bday[0].get("status") == "unknown"
    assert "don't currently know" in bday[1].lower()
    assert not _SCORE_LEAK.search(bday[1]), bday[1]

    conf = MemoryEngine._acm_authority_speak(
        "How confident are you that I'll go hiking this weekend?"
    )
    assert conf[0].get("intent") == "prediction"
    assert "confidence" in conf[1].lower()
    assert "hiking" in conf[1].lower()

    conflict = MemoryEngine._acm_authority_speak(
        "If I drink coffee after 8 PM, what is likely to happen?"
    )
    assert conflict[0].get("status") == "conflicting"
    assert "conflict" in conflict[1].lower()


def test_language_stability_english_conversation() -> None:
    assert conversation_language("What is likely to happen tomorrow?") == "en"
    chinese = "根据记忆，明天可能会下雨。"
    assert is_language_mismatch("What is likely to happen tomorrow?", chinese)
    fixed = enforce_reply_language(
        "What is likely to happen tomorrow?",
        chinese,
        fallback="Likely from memory: rain.",
    )
    assert fixed == "Likely from memory: rain."
    assert not _CJK.search(fixed)


def test_no_internal_score_leakage_in_prediction_speech() -> None:
    MemoryEngine._acm_authority_speak("Every Saturday I usually go fishing.")
    _, speech = MemoryEngine._acm_authority_speak(
        "What am I likely to do next Saturday?"
    )
    assert not _SCORE_LEAK.search(speech), speech
    assert "organ" not in speech.lower()
    assert "classification" not in speech.lower()
