"""Ada local + Ada v2 feature parity tests."""

from __future__ import annotations


def test_kasa_room_grouping():
    from jarvis.kasa_rooms import group_devices_by_room, list_rooms

    devices = [
        {"alias": "Office Lamp", "host": "192.168.1.10"},
        {"alias": "Kitchen Strip", "host": "192.168.1.11"},
        {"alias": "mystery plug", "host": "192.168.1.12"},
    ]
    groups = group_devices_by_room(devices)
    assert "Office" in groups
    assert "Kitchen" in groups
    assert "Other" in groups
    rooms = list_rooms(devices)
    assert rooms[0] == "All"
    assert "Office" in rooms


def test_focus_relax_presets_in_defaults():
    from jarvis.scene_presets import DEFAULT_PRESETS

    assert "focus mode" in DEFAULT_PRESETS
    assert DEFAULT_PRESETS["focus mode"].get("kasa_all") == "off"
    assert "relax" in DEFAULT_PRESETS
    assert DEFAULT_PRESETS["relax"].get("kasa_brightness") == 40


def test_curated_news_categories():
    from jarvis.curated_news import get_curated_headlines

    data = get_curated_headlines(use_ai=False, force_refresh=True)
    cats = data.get("categories") or []
    assert "Markets" in cats
    assert "Culture" in cats
    assert "breaking" in data or data.get("headlines") is not None


def test_system_info_intelligence_block():
    from unittest.mock import MagicMock

    from jarvis.system_info import build_system_info

    info = build_system_info(assistant=MagicMock())
    assert "planner" in info
    assert "feature_flags" in info
    assert "home_assistant" in info
    assert info.get("greeting")


def test_iterate_cad_handler_registered():
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import get_action

    ensure_handlers_loaded()
    fn = get_action("iterate_cad")
    assert fn is not None
