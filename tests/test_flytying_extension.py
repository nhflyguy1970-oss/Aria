"""Fly Tying extension — routes + handlers wiring."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def test_flytying_routes_nonempty():
    from jarvis.extensions.flytying.routes import flytying_routes

    rules = flytying_routes()
    assert rules
    actions = {r.action for r in rules}
    for needed in ("fly_status", "fly_recipe", "fly_ask", "fly_search", "fly_gold_build"):
        assert needed in actions


def test_extension_routes_method():
    from jarvis.extensions.flytying.extension import EXTENSION

    rules = EXTENSION.routes()
    assert len(rules) >= 5


def test_fly_status_handler():
    from jarvis.extensions.flytying import handlers

    with patch("jarvis.flytying.bridge.status", return_value={"loaded": True, "record_count": 10, "pattern_of_the_day": {"ok": True, "name": "Adams"}}):
        out = handlers.fly_status(MagicMock(), {}, "")
    assert out.get("ok") is True or out.get("success") is True or "Fly Tying" in str(out.get("message") or out.get("text") or out)


def test_fly_search_handler():
    from jarvis.extensions.flytying import handlers

    with patch(
        "jarvis.flytying.search.unified_search",
        return_value={"ok": True, "results": [{"name": "BWO", "type": "dry"}]},
    ):
        out = handlers.fly_search(MagicMock(), {"query": "bwo"}, "search flies bwo")
    assert out["ok"] is True
    assert "BWO" in out["message"]
