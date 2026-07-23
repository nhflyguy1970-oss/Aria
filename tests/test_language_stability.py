"""Release-blocking language stability gates for Memory Authority / Prediction.

English conversations must never emit CJK/Cyrillic (or other mismatched scripts)
unless the user explicitly switches languages.
"""

from __future__ import annotations

import re

from jarvis.behaviors.memory.engine import MemoryEngine
from jarvis.lang_util import (
    conversation_language,
    enforce_reply_language,
    is_language_mismatch,
    language_reply_hint,
)
from jarvis.nlu.mapping import resolve_memory_route

_CJK = re.compile(r"[\u4e00-\u9fff]")
_CYRILLIC = re.compile(r"[\u0400-\u04FF]")

_ENGLISH_PROMPTS = (
    "It has rained every day this week.",
    "Every Saturday I usually go fishing.",
    "What is likely to happen tomorrow?",
    "What am I likely to do next Saturday?",
    "Will I definitely go fishing next Saturday?",
    "How did you make that prediction?",
    "When SHOULD I work?",
    "What am I likely to do on my birthday next year?",
    "How confident are you that I'll go hiking this weekend?",
    "If I drink coffee after 8 PM, what is likely to happen?",
)


def _assert_english(speech: str, *, prompt: str) -> None:
    assert conversation_language(prompt) == "en", prompt
    assert not _CJK.search(speech or ""), (prompt, speech)
    assert not _CYRILLIC.search(speech or ""), (prompt, speech)
    assert not is_language_mismatch(prompt, speech or ""), (prompt, speech)


def test_english_lock_hint_always_present_for_latin_prompts() -> None:
    hint = language_reply_hint(None)
    assert "English" in hint
    assert "unless the user explicitly asks" in hint.lower()


def test_english_mismatch_rejects_chinese_and_short_cjk() -> None:
    prompt = "What is likely to happen tomorrow?"
    assert is_language_mismatch(prompt, "根据记忆，明天可能会下雨。")
    assert is_language_mismatch(prompt, "下雨")  # short CJK still blocked
    fixed = enforce_reply_language(
        prompt,
        "根据记忆，明天可能会下雨。",
        fallback="Likely from memory: rain.",
    )
    assert fixed == "Likely from memory: rain."
    assert not _CJK.search(fixed)


def test_memory_authority_prediction_path_stays_english() -> None:
    for prompt in (
        "It has rained every day this week.",
        "Every Saturday I usually go fishing.",
        "I usually get more work done in the morning.",
        "Every weekend for the last year I have gone hiking.",
    ):
        route = resolve_memory_route(prompt)
        assert route is not None and route["action"] == "memory_about_user", prompt
        result, speech = MemoryEngine._acm_authority_speak(prompt)
        assert result.get("is_memory_request") or "teaching_encoded" in (
            result.get("reasoning_path") or []
        ), prompt
        _assert_english(speech, prompt=prompt)

    for prompt in (
        "What is likely to happen tomorrow?",
        "What am I likely to do next Saturday?",
        "Will I definitely go fishing next Saturday?",
        "How did you make that prediction?",
        "When SHOULD I work?",
        "What am I likely to do on my birthday next year?",
        "How confident are you that I'll go hiking this weekend?",
    ):
        route = resolve_memory_route(prompt)
        assert route is not None and route["action"] == "memory_about_user", prompt
        result, speech = MemoryEngine._acm_authority_speak(prompt)
        assert result.get("intent") in ("prediction", "pattern") or result.get(
            "is_memory_request"
        ), (prompt, result.get("intent"))
        _assert_english(speech, prompt=prompt)


def test_conversation_language_action_answers_english() -> None:
    from jarvis.behaviors.conversation import ConversationBehavior
    from jarvis.nlu.mapping import _CONVERSATION_LANGUAGE_QUERY

    q = "What language have we been speaking in during this conversation?"
    assert _CONVERSATION_LANGUAGE_QUERY.search(q)
    assert resolve_memory_route(q) is None

    behavior = ConversationBehavior()
    out = behavior._conversation_language_entry(None, {"question": q}, q)  # type: ignore[arg-type]
    assert out.get("ok")
    msg = (out.get("message") or "").lower()
    assert "english" in msg
    assert out.get("source") == "language_subsystem"
    assert "python" not in msg
