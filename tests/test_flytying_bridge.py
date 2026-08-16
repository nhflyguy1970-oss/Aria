"""Fly Tying bridge — status, search, materials suggest, POTD wiring."""

from __future__ import annotations

from unittest.mock import patch


def test_bridge_status_includes_pattern_of_the_day():
    from jarvis.flytying import bridge

    potd = {"ok": True, "name": "Adams", "type": "dry", "day": "2026-07-28"}
    with patch("jarvis.flytying.nightly.pattern_of_the_day", return_value=potd):
        with patch("jarvis.flytying.bridge.gold_available", return_value=False):
            bridge.reset_blackfly_cache()
            st = bridge.status(force=True)
    assert "pattern_of_the_day" in st
    assert st["pattern_of_the_day"]["name"] == "Adams"


def test_bridge_search_recipes_delegates():
    from jarvis.flytying import bridge

    with patch(
        "jarvis.flytying.bridge.unified_search",
        return_value={"ok": True, "results": [{"name": "BWO", "recipe_id": "1"}]},
    ):
        hits = bridge.search_recipes("bwo", limit=3)
    assert hits
    assert hits[0]["name"] == "BWO"


def test_suggest_from_materials_tolerates_empty():
    from jarvis.flytying import bridge

    with patch("jarvis.flytying.bridge.gold_available", return_value=False):
        out = bridge.suggest_from_materials([], limit=3)
    assert isinstance(out, list)
