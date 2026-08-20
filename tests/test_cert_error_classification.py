"""Live certification: a failure must be reported as the kind of failure it is.

A refused action told the caller ARIA had broken; a bad capability name in a
request surfaced as an internal execution failure. Both are decisions about the
caller's input, and callers route on error_kind.
"""

from __future__ import annotations

import pytest

from jarvis.handlers import ensure_handlers_loaded
from jarvis.handlers.registry import call_action


@pytest.fixture(autouse=True)
def _handlers():
    ensure_handlers_loaded()


def test_an_unknown_capability_is_an_invalid_request(data_dir):
    result = call_action(
        None, "model_route", {"task_type": "general", "required_capabilities": ["telepathy"]}, "x"
    )
    assert result["ok"] is False
    assert result["error_kind"] == "invalid_request"
    assert "telepathy" in result["message"]


def test_a_known_capability_still_routes(data_dir):
    result = call_action(
        None, "model_route", {"task_type": "general", "required_capabilities": ["vision"]}, "x"
    )
    assert result["ok"] is True


def test_a_refused_browser_action_is_permission_denied(data_dir):
    from jarvis.computer_use import engine, sessions

    session = sessions.create(owner="research_specialist")
    out = engine.perform(
        session["id"],
        "download",
        {"url": "https://example.com/x.zip"},
        agent_id="research_specialist",
    )
    assert out["error_kind"] == engine.ERR_PERMISSION


def test_an_unregistered_action_is_named_not_a_bare_keyerror(data_dir):
    from jarvis.handlers.registry import UnknownAction

    with pytest.raises(UnknownAction) as excinfo:
        call_action(None, "no_such_action_anywhere", {}, "x")
    assert "no_such_action_anywhere" in str(excinfo.value)


def test_an_unhonoured_model_preference_is_stated_not_swallowed(data_dir):
    """The status was recorded but never said out loud: a caller who asked for
    a specific model got a different one with no mention of it."""
    result = call_action(
        None,
        "model_route",
        {"task_type": "general", "preferred_model": "totally-not-a-model:999b"},
        "x",
    )
    assert result["ok"] is True
    decision = result["decision"]
    assert decision["preferred_model_used"] is False
    assert decision["preferred_model_status"] == "not_registered"
    assert "totally-not-a-model:999b" in decision["reason"], "the caller is not told"


def test_an_honoured_preference_does_not_carry_a_warning(data_dir):
    baseline = call_action(None, "model_route", {"task_type": "general"}, "x")
    chosen = baseline["decision"]["selected_model"]

    result = call_action(
        None, "model_route", {"task_type": "general", "preferred_model": chosen}, "x"
    )
    decision = result["decision"]
    assert decision["preferred_model_used"] is True
    assert "was not used" not in decision["reason"]
