"""Home Assistant core client tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest


def test_normalize_ha_token_strips_bearer_and_quotes():
    from jarvis.home_assistant import normalize_ha_token

    assert normalize_ha_token(' Bearer abc.def.ghi ') == "abc.def.ghi"
    assert normalize_ha_token('"token"') == "token"
    assert normalize_ha_token("'token'") == "token"


def test_ha_enabled_requires_url_and_token(monkeypatch):
    from jarvis import home_assistant as ha

    monkeypatch.delenv("JARVIS_HA_ENABLED", raising=False)
    monkeypatch.setenv("JARVIS_HA_URL", "")
    monkeypatch.setenv("JARVIS_HA_TOKEN", "")
    assert ha.ha_enabled() is False
    monkeypatch.setenv("JARVIS_HA_URL", "http://127.0.0.1:8123")
    monkeypatch.setenv("JARVIS_HA_TOKEN", "tok")
    assert ha.ha_enabled() is True
    monkeypatch.setenv("JARVIS_HA_ENABLED", "0")
    assert ha.ha_enabled() is False


def test_parse_control_on_off_and_color():
    from jarvis.home_assistant import parse_control

    assert parse_control("turn on kitchen lights") == {"action": "on", "target": "kitchen lights"}
    assert parse_control("turn the lamp off") == {"action": "off", "target": "lamp"}
    color = parse_control("set table lamp to blue")
    assert color and color.get("color_name") == "blue"


def test_find_entities_uses_aliases(tmp_path, monkeypatch):
    from jarvis import ha_aliases
    from jarvis.home_assistant import find_entities

    monkeypatch.setattr(ha_aliases, "ALIASES_FILE", tmp_path / "aliases.json")
    ha_aliases.set_alias("kitchen", ["light.kitchen_main"])
    with patch(
        "jarvis.home_assistant.get_state",
        return_value={"entity_id": "light.kitchen_main", "state": "on", "attributes": {"friendly_name": "Kitchen"}},
    ):
        hits = find_entities("kitchen")
    assert hits and hits[0]["entity_id"] == "light.kitchen_main"


def test_list_entities_filters_domain():
    from jarvis.home_assistant import list_entities

    states = [
        {"entity_id": "light.a", "state": "on", "attributes": {"friendly_name": "A"}},
        {"entity_id": "switch.b", "state": "off", "attributes": {"friendly_name": "B"}},
        {"entity_id": "light.bathroom", "state": "on", "attributes": {"friendly_name": "Bath"}},
    ]
    with patch("jarvis.home_assistant.list_states", return_value=states):
        with patch("jarvis.ha_entity_filter.entity_hidden_from_jarvis", side_effect=lambda st: "bath" in (st.get("entity_id") or "")):
            rows = list_entities(domain="light", limit=10)
    assert [r["entity_id"] for r in rows] == ["light.a"]


def test_control_entity_light_color_mocked():
    from jarvis.home_assistant import control_entity

    with patch(
        "jarvis.home_assistant.find_entities",
        return_value=[{"entity_id": "light.lamp", "attributes": {"friendly_name": "Lamp"}, "state": "on"}],
    ):
        with patch("jarvis.ha_light_control.set_light", return_value=(True, "ok")) as set_light:
            ok, msg = control_entity("lamp", "on", color_name="blue", brightness_pct=40)
    assert ok is True
    set_light.assert_called_once()
    kwargs = set_light.call_args.kwargs
    assert kwargs.get("color_name") == "blue"
    assert kwargs.get("brightness_pct") == 40


def test_quick_route_status_and_scene():
    from jarvis.home_assistant import quick_route_home_assistant

    assert quick_route_home_assistant("house status")["action"] == "ha_status"
    scene = quick_route_home_assistant("activate movie mode")
    # may be scene or control depending on parse_scene
    assert scene is None or scene.get("action") in ("ha_scene", "ha_control")


def test_device_router_list_unified_uses_list_entities():
    from jarvis.device_router import list_unified_devices

    with patch("jarvis.home_assistant.ha_enabled", return_value=True):
        with patch(
            "jarvis.home_assistant.list_entities",
            return_value=[{"entity_id": "light.x", "friendly_name": "X", "state": "on"}],
        ):
            with patch("jarvis.p2_flags.kasa_enabled", return_value=False):
                rows = list_unified_devices()
    assert rows and rows[0]["backend"] == "ha"
    assert rows[0]["id"] == "light.x"
