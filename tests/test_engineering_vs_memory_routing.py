"""Bug 2 — engineering instructions must not be answered from memory.

_USER_MEMORY matched bare tokens ("evidence", "recall", "remember", "note that")
anywhere in a message, so infer_intent_from_structure returned intent="memory"
and an engineering instruction was answered with the memory onboarding message
("I'm still learning about you…"). Reproduced originally on a fresh session with
no prior state, so these fixtures build a fresh SessionContext every time.
"""

from __future__ import annotations

import pytest

from jarvis.nlu.mapping import (
    infer_intent_from_structure,
    memory_cue_is_incidental,
    resolve_memory_route,
)
from jarvis.nlu.pipeline import analyze_prompt
from jarvis.session import SessionContext

# The three cases the diagnostic reproduced, plus the live UI prompt.
DIAGNOSTIC_REPRO = [
    "Investigate the stale active-request lifecycle and report any relevant runtime evidence.",
    "Debug the request lock and recall which thread holds it.",
    "Refactor the parser. Note that the tests must still pass.",
]

ENGINEERING_PROMPTS = [
    *DIAGNOSTIC_REPRO,
    'Investigate the "Another request is still finishing" condition shown after the '
    "first_token_timeout failure. Do not change research behavior or mask the timeout.",
    "Trace the deadlock and include any relevant logs or runtime evidence.",
    "Diagnose the stream timeout and note that the lock is never released.",
    "Analyze the crash and show supporting logs.",
    "Inspect the thread pool; recall is not the issue here.",
]

MEMORY_PROMPTS = [
    "Show me the evidence.",
    "Show the evidence.",
    "Show my memory evidence.",
    "What is the evidence?",
    "What evidence do you have?",
    "Show the history behind this memory.",
    "Show why this memory changed.",
    "What do you remember about me?",
    "What do you know about me?",
    "search my memory for fly patterns",
    "Remember that I prefer concise answers.",
    "Please remember ARIA-FINAL-MEMORY-1234",
    "Note that I prefer dark roast coffee.",
    "forget that I like coffee",
    "fix my email address",
    "Do you recall my favorite color?",
]


def _fresh_intent(prompt: str) -> str:
    """Route on a brand-new session — proves no state contamination is involved."""
    return analyze_prompt(prompt, SessionContext()).semantic.intent


# --- 12/13/14/16/17: engineering wins over incidental memory vocabulary -----


@pytest.mark.parametrize("prompt", ENGINEERING_PROMPTS)
def test_engineering_prompt_is_not_memory_intent(prompt: str) -> None:
    assert _fresh_intent(prompt) != "memory", prompt


@pytest.mark.parametrize("prompt", ENGINEERING_PROMPTS)
def test_engineering_prompt_has_no_memory_route(prompt: str) -> None:
    resolved = resolve_memory_route(prompt)
    assert resolved is None, (prompt, resolved)


@pytest.mark.parametrize("prompt", DIAGNOSTIC_REPRO)
def test_diagnostic_reproduction_cases_fixed(prompt: str) -> None:
    """The exact three cases from the diagnostic pass."""
    assert _fresh_intent(prompt) != "memory", prompt
    assert memory_cue_is_incidental(prompt) is True, prompt


def test_evidence_word_alone_does_not_mean_memory() -> None:
    prompt = "Report any relevant logs or runtime evidence and the smallest safe repair plan."
    assert _fresh_intent(prompt) != "memory"


def test_recall_as_ordinary_verb_does_not_mean_memory() -> None:
    prompt = "Debug the lock and recall which thread holds it."
    assert _fresh_intent(prompt) != "memory"


def test_note_that_in_technical_context_does_not_mean_memory() -> None:
    prompt = "Refactor the parser. Note that the tests must still pass."
    assert _fresh_intent(prompt) != "memory"
    assert infer_intent_from_structure(analyze_prompt(prompt, SessionContext())) != "memory"


# --- 15: legitimate memory requests still route to memory -------------------


@pytest.mark.parametrize("prompt", MEMORY_PROMPTS)
def test_legitimate_memory_prompt_still_memory(prompt: str) -> None:
    resolved = resolve_memory_route(prompt)
    intent = _fresh_intent(prompt)
    assert intent == "memory" or resolved is not None, (prompt, intent, resolved)


@pytest.mark.parametrize("prompt", MEMORY_PROMPTS)
def test_legitimate_memory_prompt_not_treated_as_incidental(prompt: str) -> None:
    assert memory_cue_is_incidental(prompt) is False, prompt


def test_explicit_memory_framing_beats_engineering_verbs() -> None:
    """A memory command that happens to contain an engineering word still routes."""
    for prompt in (
        "fix my email address",
        "search my memory for the test results",
        "Remember that I debug with pdb.",
        "What do you remember about my thread pool preference?",
    ):
        assert memory_cue_is_incidental(prompt) is False, prompt


# --- evidence routing contract from test_evidence_routing.py is preserved ---


@pytest.mark.parametrize(
    "prompt",
    [
        "Show me the evidence.",
        "Show the evidence.",
        "Show my memory evidence.",
        "What is the evidence?",
        "What evidence do you have?",
    ],
)
def test_evidence_cues_still_reach_memory_authority(prompt: str) -> None:
    resolved = resolve_memory_route(prompt)
    assert resolved is not None, prompt
    assert resolved["action"] == "memory_about_user", (prompt, resolved)
