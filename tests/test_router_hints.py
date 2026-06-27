"""Router hint tests (P1 #23)."""

from __future__ import annotations


def test_hint_timer():
    from jarvis.router_hints import try_hint_route

    hit = try_hint_route("set a timer for 5 minutes")
    assert hit is not None
    assert hit["action"] == "planner_set_timer"
    assert hit["params"].get("duration") == "5 minutes"
    assert hit["router"] == "hint"


def test_hint_morning_not_timer():
    from jarvis.router_hints import try_hint_route

    hit = try_hint_route("good morning briefing")
    assert hit["action"] == "morning_briefing"


def test_hint_ha_control():
    from jarvis.router_hints import try_hint_route

    hit = try_hint_route("turn on office lights")
    assert hit["action"] == "ha_control"
    assert hit["params"].get("action") == "on"


def test_contradicts_timer_vs_briefing():
    from jarvis.router_hints import contradicts_hint, try_hint_route

    assert contradicts_hint("set a timer for 5 minutes", "morning_briefing")
    override = try_hint_route("set a timer for 5 minutes")
    assert override["action"] == "planner_set_timer"


def test_export_functiongemma_core_rows(tmp_path, monkeypatch):
    out = tmp_path / "fg.jsonl"
    monkeypatch.setattr("jarvis.router_training.FG_OUT", out)
    from jarvis.router_training import export_functiongemma_jsonl

    path = export_functiongemma_jsonl()
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 40
    assert any("planner_set_timer" in line for line in lines)
