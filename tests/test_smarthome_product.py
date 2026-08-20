"""Smart Home product — home, profiles, favorites, rooms, bridges, policy."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def test_product_status_pipeline():
    from jarvis.home_assistant_product.engine import product_status

    with patch(
        "jarvis.home_assistant.status_payload", return_value={"ok": True, "url": "http://ha"}
    ):
        st = product_status()
    assert st["ok"] is True
    assert st["product"] == "Smart Home"
    assert "smarthome_engine" in st["pipeline"]


def test_recovery_guided():
    from jarvis.home_assistant_product.engine import recovery_status

    with patch("jarvis.home_assistant.ha_url", return_value=""):
        with patch("jarvis.home_assistant.ha_token", return_value=""):
            with patch("jarvis.home_assistant.ha_feature_on", return_value=True):
                rec = recovery_status()
    assert rec["guided"] is True
    assert isinstance(rec["steps"], list)
    assert rec["ready"] is False


def test_home_payload_shape():
    from jarvis.home_assistant_product.engine import home_payload

    with patch(
        "jarvis.home_assistant_product.engine.recovery_status",
        return_value={
            "ready": True,
            "connection": {"ok": True},
            "steps": [],
            "hint": "ok",
            "status": {},
        },
    ):
        with patch(
            "jarvis.home_assistant_product.favorites.favorites_payload",
            return_value={"ok": True, "entities": [], "count": 0},
        ):
            with patch("jarvis.home_assistant_product.rooms.list_rooms", return_value=[]):
                with patch(
                    "jarvis.scene_presets.list_presets",
                    return_value=[{"id": "relax", "label": "Relax"}],
                ):
                    home = home_payload()
    assert home["ok"] is True
    assert "favorites" in home
    assert "scenes" in home


def test_profiles_builtins():
    from jarvis.home_assistant_product.profiles import list_profiles

    ids = {p["id"] for p in list_profiles()}
    for needed in ("home", "away", "office", "workshop", "night", "vacation", "quiet_hours"):
        assert needed in ids


def test_favorites_pin_unpin(tmp_path, monkeypatch):
    from jarvis.home_assistant_product import favorites as fav

    monkeypatch.setattr(fav, "FAVORITES_FILE", tmp_path / "fav.json")
    fav.pin("light.kitchen")
    assert "light.kitchen" in fav.list_favorites()
    fav.unpin("light.kitchen")
    assert "light.kitchen" not in fav.list_favorites()


def test_rooms_upsert(tmp_path, monkeypatch):
    from jarvis.home_assistant_product import rooms as rm

    monkeypatch.setattr(rm, "ROOMS_FILE", tmp_path / "rooms.json")
    row = rm.upsert_room({"name": "Kitchen", "entity_ids": ["light.kitchen"]})
    assert row.get("name") == "Kitchen" or row.get("id")
    assert any(
        r.get("name") == "Kitchen" or "kitchen" in str(r.get("id") or "").lower()
        for r in rm.list_rooms(seed=False)
    )


def test_history_redaction(tmp_path, monkeypatch):
    from jarvis.home_assistant_product import history as hist

    monkeypatch.setattr(hist, "HISTORY_FILE", tmp_path / "h.jsonl")
    entry = hist.add_entry(
        {
            "kind": "control",
            "summary": "open",
            "detail": "secret device note",
            "uncensored_origin": True,
        }
    )
    closed = hist.presentation_for_profile(entry, censored=True)
    assert closed["redacted"] is True
    assert "secret" not in closed["detail"]
    assert hist.get_entry(entry["id"])["detail"] == "secret device note"


def test_mission_panel():
    from jarvis.home_assistant_product.mission_bridge import smarthome_mission_panel

    with patch(
        "jarvis.home_assistant_product.engine.product_status",
        return_value={"ok": True, "ha": {}, "profiles": {}},
    ):
        with patch(
            "jarvis.home_assistant_product.engine.recovery_status",
            return_value={"ready": False, "hint": "setup", "steps": [], "connection": {}},
        ):
            panel = smarthome_mission_panel()
    assert panel["product"] == "Smart Home"
    assert "deep_links" in panel


def test_voice_home_status_no_speak():
    from jarvis.home_assistant_product.voice_bridge import home_command

    with patch(
        "jarvis.home_assistant_product.engine.house_status",
        return_value={"ok": True, "message": "All quiet"},
    ):
        out = home_command("status", speak=False)
    assert out["ok"] is True
    assert out["bridge"] == "voice_product"


def test_vision_camera_requires_path():
    from jarvis.home_assistant_product.vision_bridge import analyze_camera

    out = analyze_camera("camera.porch", path="")
    assert out.get("requires_confirmation") is True


def test_control_device_light_mocked():
    from jarvis.home_assistant_product.engine import control_device

    with patch("jarvis.home_assistant.ha_enabled", return_value=True):
        with patch(
            "jarvis.home_assistant_product.entities.resolve",
            return_value={"entity_ids": ["light.lamp"], "matches": []},
        ):
            with patch("jarvis.ha_light_control.set_lights", return_value=(True, "ok lamp")):
                out = control_device("lamp", "on", brightness=40, color_name="warm", source="test")
    assert out["ok"] is True
    assert out["pipeline"] == "smarthome_engine"


def test_experimental_gated():
    from jarvis.home_assistant_product.experimental import experimental_flags, websocket_status

    flags = experimental_flags()
    assert "websocket" in flags or "ha_websocket" in flags or "vision_camera" in flags
    out = websocket_status()
    assert out.get("experimental") or out.get("ok") is False


def test_cheatsheet():
    from jarvis.home_assistant_product.cheatsheet import cheatsheet_payload

    sheet = cheatsheet_payload()
    assert sheet["keyboard"]
    assert sheet["voice_home"]


def test_accessibility_home_contract():
    from pathlib import Path

    html = Path("jarvis/gui/static/index.html").read_text(encoding="utf-8")
    assert 'id="smarthomeHomePanel"' in html
    assert 'aria-label="Smart Home Home"' in html
    assert "smarthome_home.js" in html
    assert 'id="haSetupWizardBtn"' in html


def test_planner_calendar_candidates():
    from jarvis.home_assistant_product.planner_bridge import planner_candidates
    from jarvis.home_assistant_product.calendar_bridge import calendar_candidates

    p = planner_candidates(kind="focus_home")
    c = calendar_candidates(kind="meeting")
    assert p["ok"] and p["candidates"]
    assert c["ok"] and c["candidates"]


def test_candidate_routes_answer_over_http():
    """The bridges were tested directly, so route signatures that passed
    arguments the bridges never accepted returned 500 to every real caller."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from jarvis.home_assistant_product.api import register_product_routes

    app = FastAPI()
    register_product_routes(app, MagicMock())
    client = TestClient(app)

    for path in (
        "/api/smarthome/product/planner/candidates",
        "/api/smarthome/product/calendar/candidates",
        "/api/smarthome/product/automation/candidates",
    ):
        r = client.get(path)
        assert r.status_code == 200, f"{path} -> {r.status_code} {r.text[:200]}"
        body = r.json()
        assert body["ok"] is True and body["candidates"], path
