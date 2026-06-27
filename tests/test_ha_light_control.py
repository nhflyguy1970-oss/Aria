"""HA light color parsing, service payloads, and sunlight scene."""

from __future__ import annotations

import json

import pytest

from jarvis.ha_light_control import (
    ASTRONOMICAL_TWILIGHT_ELEV,
    NAUTICAL_TWILIGHT_ELEV,
    build_light_service_data,
    daylight_levels_from_sun,
    parse_color_control,
    resolve_color_name,
)
from jarvis.home_assistant import parse_control


def test_resolve_color_name_movie():
    assert resolve_color_name("movie") == {"color_temp_kelvin": 2200, "brightness_pct": 12}
    assert resolve_color_name("uv") == {"hs_color": [275, 100]}


def test_build_light_service_data_rgb_and_brightness():
    svc, data = build_light_service_data(
        "light.kitchen",
        action="on",
        rgb=[10, 20, 30],
        brightness_pct=40,
    )
    assert svc == "turn_on"
    assert data["entity_id"] == "light.kitchen"
    assert data["rgb_color"] == [10, 20, 30]
    assert data["brightness_pct"] == 40


def test_build_light_service_data_color_name():
    svc, data = build_light_service_data("light.lamp", color_name="warm")
    assert svc == "turn_on"
    assert data["color_temp_kelvin"] == 2700


def test_build_light_service_data_off():
    svc, data = build_light_service_data("light.lamp", action="off")
    assert svc == "turn_off"
    assert data == {"entity_id": "light.lamp"}


def test_parse_color_control_phrases():
    assert parse_color_control("set table lamp to blue") == {
        "action": "on",
        "target": "table lamp",
        "color_name": "blue",
    }
    assert parse_color_control("dim table lamp to 30%") == {
        "action": "on",
        "target": "table lamp",
        "brightness_pct": 30,
    }
    assert parse_color_control("make family room uv") == {
        "action": "on",
        "target": "family room",
        "color_name": "uv",
    }


def test_parse_control_delegates_color():
    spec = parse_control("set table lamp to blue")
    assert spec and spec.get("color_name") == "blue"


@pytest.mark.parametrize(
    "elevation,rising,bright_min,bright_max,in_window",
    [
        (-20, False, 0, 0, False),
        (-15, True, 2, 10, True),
        (-10, True, 8, 30, True),
        (-10, False, 8, 30, True),
        (22, True, 30, 95, True),
        (50, True, 90, 100, True),
    ],
)
def test_daylight_levels_from_sun(elevation, rising, bright_min, bright_max, in_window):
    levels = daylight_levels_from_sun(
        {"attributes": {"elevation": elevation, "rising": rising}}
    )
    assert bright_min <= levels["brightness_pct"] <= bright_max
    assert levels["in_window"] is in_window
    assert 2000 <= levels["color_temp_kelvin"] <= 6500
    if elevation < ASTRONOMICAL_TWILIGHT_ELEV:
        assert levels["phase"] == "night"
    elif elevation < 0 and rising:
        assert levels["phase"] == "dawn"
    elif elevation < 0:
        assert levels["phase"] == "dusk"


def test_twilight_thresholds():
    assert NAUTICAL_TWILIGHT_ELEV < 0 < ASTRONOMICAL_TWILIGHT_ELEV + 6


def test_sunlight_activate_mocked(tmp_path, monkeypatch):
    presets = tmp_path / "scene_presets.json"
    presets.write_text(
        json.dumps(
            {
                "sunlight": {
                    "mode": "sunlight",
                    "devices": [{"target": "light.table_lamp"}],
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("jarvis.scene_presets.PRESETS_FILE", presets)
    monkeypatch.setattr("jarvis.p2_flags.scene_presets_enabled", lambda: True)
    monkeypatch.setattr(
        "jarvis.home_assistant.get_state",
        lambda eid: {"attributes": {"elevation": 30, "rising": True}},
    )
    calls: list[tuple] = []

    def fake_set_light(eid, **kwargs):
        calls.append((eid, kwargs))
        return True, f"ok {eid}"

    monkeypatch.setattr("jarvis.ha_light_control.set_light", fake_set_light)
    from jarvis.scene_presets import activate_preset

    ok, msg = activate_preset("sunlight")
    assert ok is True
    assert calls
    assert calls[0][0] == "light.table_lamp"
    assert "brightness_pct" in calls[0][1]


def test_tick_sunlight_when_auto_enabled(monkeypatch, tmp_path):
    monkeypatch.setattr("jarvis.sunlight_scene.ensure_scene_state", lambda: {"sunlight_auto": True})
    monkeypatch.setattr("jarvis.sunlight_scene.should_manage_sunlight", lambda: True)
    monkeypatch.setattr(
        "jarvis.home_assistant.get_state",
        lambda eid: {"attributes": {"elevation": 25, "rising": True}},
    )
    monkeypatch.setattr("jarvis.sunlight_scene._write_scene_state", lambda s: None)
    presets = tmp_path / "scene_presets.json"
    presets.write_text(json.dumps({"sunlight": {"devices": []}}), encoding="utf-8")
    monkeypatch.setattr("jarvis.scene_presets.PRESETS_FILE", presets)
    called = {"n": 0}

    def fake_apply(*a, **k):
        called["n"] += 1
        return True, "ok"

    monkeypatch.setattr("jarvis.sunlight_scene.apply_sunlight_levels", fake_apply)
    monkeypatch.setattr("jarvis.sunlight_scene.set_sunlight_active", lambda *a, **k: None)
    from jarvis.sunlight_scene import tick_sunlight

    tick_sunlight()
    assert called["n"] == 1


def test_tick_sunlight_skips_when_paused(monkeypatch):
    monkeypatch.setattr("jarvis.sunlight_scene.should_manage_sunlight", lambda: False)
    called = {"n": 0}

    def fake_apply(*a, **k):
        called["n"] += 1

    monkeypatch.setattr("jarvis.sunlight_scene.apply_sunlight_levels", fake_apply)
    from jarvis.sunlight_scene import tick_sunlight

    tick_sunlight()
    assert called["n"] == 0


def test_dawn_clears_pause(monkeypatch):
    state = {
        "sunlight_auto": True,
        "sunlight_paused": True,
        "active_preset": "movie mode",
        "_last_sun_elevation": -19,
    }
    from jarvis.sunlight_scene import _handle_dawn_transition

    out = _handle_dawn_transition(state, -17)
    assert "sunlight_paused" not in out
    assert "active_preset" not in out


def test_other_preset_pauses_sunlight(monkeypatch):
    written: list[dict] = []

    monkeypatch.setattr("jarvis.sunlight_scene.ensure_scene_state", lambda: {"active_preset": "sunlight"})
    monkeypatch.setattr("jarvis.sunlight_scene._write_scene_state", lambda s: written.append(s))
    from jarvis.sunlight_scene import deactivate_sunlight_if_other_preset

    deactivate_sunlight_if_other_preset("movie mode")
    assert written
    assert written[0].get("sunlight_paused") is True
