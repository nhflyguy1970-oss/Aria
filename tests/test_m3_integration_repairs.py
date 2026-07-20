"""M3 integration repairs — live validation regression tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from jarvis.behaviors.memory.cognitive_presentation import (
    _reconstruct_fragment,
    polish_fragment_recall,
)
from jarvis.knowledge.doc_guards import is_developer_doc_request, is_internal_doc
from jarvis.nlu.episodic_patterns import (
    is_episodic_teaching,
    is_live_hardware_question,
    is_past_event_memory_question,
    reformulate_for_acm_recall,
)
from jarvis.nlu.mapping import resolve_memory_route
from jarvis.routing_explain import is_routing_explain_query, try_routing_explain
from jarvis.session import SessionContext


def test_trout_teaching_recognized() -> None:
    assert is_episodic_teaching("Yesterday I caught three trout.")


def test_where_did_i_go_routes_to_memory() -> None:
    resolved = resolve_memory_route("Where did I go last Friday?")
    assert resolved is not None
    assert resolved["action"] == "memory_about_user"


def test_where_reformulation() -> None:
    assert reformulate_for_acm_recall("Where did I go last Friday?") == (
        "What did I do last Friday?"
    )


def test_fish_catch_reformulation() -> None:
    assert reformulate_for_acm_recall("What fish did I catch?") == "What did I catch?"


def test_preference_kind_reformulation() -> None:
    assert reformulate_for_acm_recall("What kind of hooks do I prefer?") == (
        "What do I prefer about hooks?"
    )


def test_preference_recall_routing() -> None:
    resolved = resolve_memory_route("What kind of hooks do I prefer?")
    assert resolved is not None
    assert resolved["action"] == "memory_about_user"


def test_disk_space_routes_runtime_not_memory() -> None:
    assert resolve_memory_route("How much disk space is available?") is None
    assert is_live_hardware_question("How much disk space is available?")


def test_storage_devices_routes_runtime() -> None:
    assert resolve_memory_route("Show my storage devices.") is None
    assert is_live_hardware_question("Show my storage devices.")


def test_explain_intercepts_without_debug() -> None:
    assert is_routing_explain_query("Why did you choose that model?")
    hit = try_routing_explain("Why did you choose that model?")
    assert hit and hit["action"] == "chat"


def test_explain_mission_control_not_runtime() -> None:
    from jarvis.runtime_routing import is_runtime_routing_question

    assert is_routing_explain_query("Why did this go to Mission Control?")
    assert not is_runtime_routing_question("Why did this go to Mission Control?")


def test_presentation_gpu_double_verb() -> None:
    out = polish_fragment_recall(
        "installed you installed a GPU.",
        "Did I tell you what GPU I installed yesterday?",
    )
    assert "Installed you installed" not in out
    assert "GPU" in out


def test_presentation_fishing_fragment() -> None:
    out = _reconstruct_fragment("fishing.", "What fish did I catch?")
    assert out
    assert "fish" in out.lower() or "caught" in out.lower()


def test_presentation_ram_fragment() -> None:
    out = _reconstruct_fragment("my RAM.", "What RAM did I upgrade?")
    assert out
    assert "RAM" in out
    assert "upgraded" in out.lower()


def test_internal_doc_guard() -> None:
    assert is_internal_doc("docs/acm_integration/MEMORY_REPLACEMENT_BLUEPRINT.md")
    assert is_internal_doc("docs/adr/ADR-0020-workstation-ownership.md")
    assert not is_internal_doc("docs/USER_GUIDE.md")
    assert not is_developer_doc_request("help me plan my day")


def test_planning_hint_routes_planner() -> None:
    from jarvis.router_hints import try_hint_route

    hit = try_hint_route("Help me plan my day.")
    assert hit is not None
    assert hit["action"] == "planner_today"


def test_coding_chat_uses_registry_not_legacy() -> None:
    from jarvis.assistant import JarvisAssistant
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import has_action

    assert not hasattr(JarvisAssistant, "_coding_chat")
    ensure_handlers_loaded()
    assert has_action("coding_chat")


def test_brain_routing_specs_use_deep() -> None:
    from jarvis.brain_routing import needs_deep_thinking

    assert needs_deep_thinking("What are the specs of the Ryzen 5800X?")


def test_hardware_router_not_memory() -> None:
    with patch("jarvis.runtime_introspection.get_runtime_client") as mock_client:
        mock_client.return_value = MagicMock()
        from jarvis.router import route

        intent = route("How much disk space is available?", SessionContext(), None)
        action = intent.get("action") or ""
        assert action.startswith("runtime_") or action == "status_summary", intent
