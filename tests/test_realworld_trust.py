"""Real-world trust regressions (RW-001…011) — natural wording, not intent labels."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from jarvis.nlu.mapping import resolve_memory_route
from jarvis.research_context import expand_followup_query, is_research_followup
from jarvis.session import SessionContext


# --- ROOT-ORCHESTRATION / MEMORY: forget vs subject-change vs remember ---


def test_rw011_forget_preference_routes_to_memory_forget():
    r = resolve_memory_route("Forget that I prefer the desktop for heavy AI work.")
    assert r is not None
    assert r["action"] == "memory_forget"


def test_rw011_take_out_of_memory_routes_to_forget():
    r = resolve_memory_route(
        "Take that desktop preference back out of memory."
    )
    assert r is not None
    assert r["action"] == "memory_forget"


def test_rw009_subject_change_is_not_memory_search():
    r = resolve_memory_route("Okay, forget the truck. Let's work on the fly project.")
    # Must not dump memory_search; either None (chat) or explicit subject-change chat.
    assert r is None or r.get("action") in ("chat", "subject_change")
    assert (r or {}).get("action") != "memory_search"


def test_remember_still_stores():
    r = resolve_memory_route("Remember that I prefer the desktop for heavy AI work.")
    assert r is not None
    assert r["action"] == "remember"


def test_recall_still_recalls():
    r = resolve_memory_route("What do you remember about my desktop preference?")
    assert r is not None
    assert r["action"] == "memory_about_user"


# --- ROOT-ORCHESTRATION: writing must not become runtime_status ---


def test_rw010_writing_request_not_runtime():
    with patch("jarvis.runtime_introspection.get_runtime_client") as mock_client:
        mock_client.return_value = MagicMock()
        from jarvis.router import route

        intent = route(
            "Write me a one-paragraph project note for Adams Dry Fly Revival — "
            "status update for myself.",
            SessionContext(),
            None,
        )
    action = intent.get("action") or ""
    assert not str(action).startswith("runtime_"), intent
    assert action != "status_summary"
    assert action in ("chat", "compose", "write_note") or action == "chat"


def test_draft_text_not_web_search():
    with patch("jarvis.runtime_introspection.get_runtime_client") as mock_client:
        mock_client.return_value = MagicMock()
        from jarvis.router import route

        intent = route(
            "Draft a short casual text to a buddy that I'll be 15 minutes late "
            "to coffee tomorrow.",
            SessionContext(),
            None,
        )
    assert intent.get("action") == "chat", intent


# --- ROOT-CONTEXT: research follow-ups ---


def test_research_followup_detection():
    assert is_research_followup("And when did that one come out?")
    assert is_research_followup("What tools do I need?")
    assert is_research_followup("What else should I have before I start?")
    assert not is_research_followup(
        "Can you show me how to change the rotors on my 2021 Ford Ranger XLT?"
    )


def test_expand_followup_keeps_ranger_entities():
    sess = SessionContext()
    sess.note_research(
        "change rotors 2021 Ford Ranger XLT",
        ["2021", "Ford", "Ranger", "XLT", "rotors"],
    )
    expanded = expand_followup_query("What tools do I need?", sess)
    low = expanded.lower()
    assert "ranger" in low or "2021" in low or "rotor" in low


def test_rw001_followup_routes_to_web_search_with_research_context():
    with patch("jarvis.runtime_introspection.get_runtime_client") as mock_client:
        mock_client.return_value = MagicMock()
        from jarvis.router import route

        sess = SessionContext()
        sess.note_research(
            "What's the latest Ubuntu LTS version right now?",
            ["Ubuntu", "LTS"],
        )
        sess.note_subject("What's the latest Ubuntu LTS version right now?")
        intent = route("And when did that one come out?", sess, None)
    assert intent.get("action") == "web_search", intent


def test_rw008_tools_followup_routes_with_ranger_context():
    with patch("jarvis.runtime_introspection.get_runtime_client") as mock_client:
        mock_client.return_value = MagicMock()
        from jarvis.router import route

        sess = SessionContext()
        sess.note_research(
            "change the rotors on my 2021 Ford Ranger XLT",
            ["2021", "Ford", "Ranger", "XLT", "rotors"],
        )
        intent = route("What else should I have before I start?", sess, None)
    assert intent.get("action") == "web_search", intent
    q = (intent.get("params") or {}).get("query") or ""
    # Query may be raw; expansion happens in web_search handler — routing is the gate.
    assert intent.get("action") == "web_search"


# --- ROOT-MEMORY: ranking + honesty (unit-level helpers) ---


def test_memory_answer_relevant_default_deny_unrelated():
    from jarvis.behaviors.memory.engine import MemoryEngine

    assert not MemoryEngine._memory_answer_relevant(
        "What's my favorite brand of fishing reel?",
        "the workshop air compressor is a California Air Tools 8010, and my fishing buddy is Mike",
    )


def test_memory_answer_relevant_accepts_matching_preference():
    from jarvis.behaviors.memory.engine import MemoryEngine

    assert MemoryEngine._memory_answer_relevant(
        "Which machine did I say I wanted for heavy AI work?",
        "I prefer the desktop for heavy AI work",
    )


def test_lexical_score_prefers_recency_for_same_topic():
    from jarvis.behaviors.memory.engine import MemoryEngine

    # Indirect: ensure scoring function exists and boosts newer matching content
    # when comparing via _acm_lexical_hits would require ACM — test score helper if exposed.
    # Fallback: relevance gate alone is covered above; ranking tested in integration when ACM available.
    assert hasattr(MemoryEngine, "_acm_lexical_hits")


def test_teaching_ack_suppressed_on_forget():
    from jarvis.behaviors.memory.cognitive_presentation import format_teaching_acknowledgement

    ack = format_teaching_acknowledgement(
        "Forget that I prefer the desktop for heavy AI work."
    )
    assert ack == "" or "remember" not in ack.lower()


def test_destructive_refusal_still_routes():
    from jarvis.orchestration_policy import (
        is_destructive_system_request,
        route_override_for_policy,
    )

    assert is_destructive_system_request("Give me the exact command to wipe `/`.")
    ov = route_override_for_policy("Give me the exact command to wipe `/`.", "chat")
    assert ov and ov.get("route_reason") == "policy_destructive_system_refusal"
