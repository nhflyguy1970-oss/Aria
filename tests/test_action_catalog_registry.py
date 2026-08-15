from __future__ import annotations

import re


def test_router_actions_are_generated_from_registry() -> None:
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import action_names
    from jarvis import router

    ensure_handlers_loaded()
    listed = set(re.findall(r"^- ([a-zA-Z0-9_]+):", str(router.ACTIONS), re.M))

    assert listed
    assert listed <= action_names()
    assert "params: {}" in str(router.ACTIONS)


def test_capability_map_derived_from_registered_actions() -> None:
    from jarvis.capability_routing import action_capability_map, capability_for_action
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import action_names

    ensure_handlers_loaded()
    cmap = action_capability_map()

    assert set(cmap) >= action_names()
    assert capability_for_action("coding_fix") == "debugging"
    assert capability_for_action("memory_search") == "memory"
