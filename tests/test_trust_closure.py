"""Trust-closure unit tests — memory phrasing, fiction, context, clarification."""

from __future__ import annotations

from jarvis.orchestration_policy import (
    is_personal_memory_question,
    prefers_local_reference,
    research_required,
)
from jarvis.research_context import (
    bare_referent_request,
    expand_followup_query,
    premise_supported_by_results,
)
from jarvis.router import route
from jarvis.session import SessionContext


def test_fiction_manual_requires_research_not_local():
    q = "According to the ACME HyperDrive Owner Manual Rev Z9, what is the flux capacitor service interval?"
    assert prefers_local_reference(q) is False
    assert research_required(q) is True
    assert route(q, SessionContext(), None).get("action") == "web_search"


def test_nonexistent_driver_requires_research():
    q = "Does NVIDIA driver version 999.99 exist for Linux?"
    assert research_required(q) is True
    assert route(q, SessionContext(), None).get("action") == "web_search"


def test_user_assertion_does_not_make_manual_local():
    q = "I just bought an ACME HyperDrive 9000. What does its official manual say?"
    assert prefers_local_reference(q) is False
    assert research_required(q) is True


def test_premise_unsupported_without_matching_sources():
    assert premise_supported_by_results(
        "ACME HyperDrive Rev Z9",
        [{"title": "Ford Ranger brakes", "snippet": "rotor tip", "url": "https://example.com"}],
    ) is False


def test_memory_phrasings_route_to_memory():
    for q in (
        "What GPU did I say was in my AI workstation?",
        "Which graphics card did I tell you I use?",
        "Who is my fishing buddy for Saturday?",
        "What air compressor do I have in the workshop?",
    ):
        assert is_personal_memory_question(q), q
        assert route(q, SessionContext(), None).get("action") == "memory_about_user", q


def test_torque_followup_expands_ranger_context():
    s = SessionContext()
    s.note_research("How do I change the rotors on my 2021 Ford Ranger XLT?")
    expanded = expand_followup_query("What is the torque specification?", s)
    assert "Ranger" in expanded or "2021" in expanded
    assert "torque" in expanded.lower()


def test_clarify_bare_fix_it():
    intent = route("Can you fix it?", SessionContext(), None)
    assert intent.get("action") == "clarify"
    assert "fix" in (intent.get("clarification_question") or "").lower()


def test_fix_it_uses_active_subject():
    s = SessionContext()
    s.note_subject("My scraper finds URLs but doesn't save anything.")
    intent = route("Can you fix it?", s, None)
    assert intent.get("action") == "chat"
    assert intent.get("route_reason") == "referent_from_subject"


def test_bare_referent_helper():
    assert bare_referent_request("Can you fix it?") is True
    assert bare_referent_request("Can you fix the scraper save bug?") is False
