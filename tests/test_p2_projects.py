"""P2 projects, device router, scene presets tests."""

from __future__ import annotations

import json


def test_project_registry(tmp_path, monkeypatch):
    root = tmp_path / "projects"
    monkeypatch.setattr("jarvis.project_registry.PROJECTS_ROOT", root)
    monkeypatch.setattr("jarvis.active_project.ACTIVE_FILE", tmp_path / "active.json")
    import jarvis.project_registry as pr
    import jarvis.active_project as ap

    meta = pr.create_project("Lab Bench")
    assert meta["slug"] == "lab-bench"
    assert (root / "lab-bench" / "cad").is_dir()
    ap.set_active_slug(meta["slug"])
    assert ap.get_active_slug() == "lab-bench"
    listed = pr.list_projects()
    assert any(p["slug"] == "lab-bench" for p in listed)


def test_scene_presets(tmp_path, monkeypatch):
    presets = tmp_path / "scene_presets.json"
    presets.write_text(
        json.dumps({"test mode": {"label": "Test", "devices": []}}),
        encoding="utf-8",
    )
    monkeypatch.setattr("jarvis.scene_presets.PRESETS_FILE", presets)
    from jarvis.scene_presets import activate_preset, list_presets

    assert len(list_presets()) >= 1
    ok, msg = activate_preset("test mode")
    assert ok


def test_device_router_ha_fallback(monkeypatch):
    monkeypatch.setattr("jarvis.p2_flags.device_router_enabled", lambda: True)
    monkeypatch.setattr("jarvis.p2_flags.kasa_enabled", lambda: False)
    monkeypatch.setattr("jarvis.home_assistant.ha_enabled", lambda: True)

    def fake_control(target, action, **kwargs):
        return True, f"HA {target} {action}"

    monkeypatch.setattr("jarvis.home_assistant.control_entity", fake_control)
    from jarvis.device_router import control_device

    ok, msg, backend = control_device("office lights", "on")
    assert ok and backend == "ha"


def test_device_router_ha_entity_id_skips_kasa(monkeypatch):
    monkeypatch.setattr("jarvis.p2_flags.device_router_enabled", lambda: True)
    monkeypatch.setattr("jarvis.p2_flags.kasa_enabled", lambda: True)
    monkeypatch.setattr("jarvis.home_assistant.ha_enabled", lambda: True)

    def fake_control(target, action, **kwargs):
        return True, f"HA {target} bp={kwargs.get('brightness_pct')}"

    def boom(*_a, **_k):
        raise AssertionError("Kasa must not run for HA entity ids")

    monkeypatch.setattr("jarvis.home_assistant.control_entity", fake_control)
    monkeypatch.setattr("jarvis.kasa_devices._match_device", lambda _t: {"host": "1.2.3.4"})
    monkeypatch.setattr("jarvis.kasa_devices.control_device", boom)
    from jarvis.device_router import control_device

    ok, msg, backend = control_device("light.table_lamp", "on", brightness=25)
    assert ok and backend == "ha"
    assert "25" in msg


def test_device_router_ha_entity_id_keeps_ha_error(monkeypatch):
    monkeypatch.setattr("jarvis.p2_flags.device_router_enabled", lambda: True)
    monkeypatch.setattr("jarvis.p2_flags.kasa_enabled", lambda: True)
    monkeypatch.setattr("jarvis.home_assistant.ha_enabled", lambda: True)
    monkeypatch.setattr(
        "jarvis.home_assistant.control_entity",
        lambda *_a, **_k: (False, "HA said no"),
    )
    monkeypatch.setattr(
        "jarvis.kasa_devices.control_device",
        lambda *_a, **_k: (False, "No Kasa device matches 'light.table_lamp'"),
    )
    from jarvis.device_router import control_device

    ok, msg, backend = control_device("light.table_lamp", "on", brightness=25)
    assert not ok and backend == "ha"
    assert "HA said no" in msg


def test_shopping_parse():
    from jarvis.web_browse import parse_shopping_query

    spec = parse_shopping_query("find standing desk under $200 on amazon")
    assert spec and spec["max_price"] == 200.0
