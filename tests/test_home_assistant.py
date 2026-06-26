"""Home Assistant integration tests."""

import pytest

from jarvis.home_assistant import (
    activate_scene,
    check_connection,
    control_entity,
    find_entities,
    ha_enabled,
    home_summary,
    parse_control,
    parse_scene,
    verify_automation_secret,
)


@pytest.fixture
def ha_env(monkeypatch):
    monkeypatch.setenv("JARVIS_HA_URL", "http://homeassistant.local:8123")
    monkeypatch.setenv("JARVIS_HA_TOKEN", "test-token")
    monkeypatch.setenv("JARVIS_HA_ENABLED", "1")
    monkeypatch.setenv("JARVIS_AUTOMATION_SECRET", "hook-secret")
    monkeypatch.setenv("JARVIS_HA_SCENE_LEAVE", "scene.leaving")


def test_ha_enabled_requires_url_and_token(monkeypatch):
    monkeypatch.delenv("JARVIS_HA_URL", raising=False)
    monkeypatch.delenv("JARVIS_HA_TOKEN", raising=False)
    assert ha_enabled() is False


def test_parse_control():
    assert parse_control("turn off the porch light") == {
        "action": "off",
        "target": "porch light",
    }
    assert parse_control("switch living room on") == {
        "action": "on",
        "target": "living room",
    }


def test_parse_scene_and_leave(ha_env):
    assert parse_scene("activate scene movie night") == "movie night"
    assert parse_scene("I'm heading out") == "scene.leaving"
    assert parse_scene("good night house") == "scene.leaving"


def test_find_entities_fuzzy(ha_env, monkeypatch):
    states = [
        {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"friendly_name": "Living Room"},
        },
        {
            "entity_id": "switch.garage",
            "state": "off",
            "attributes": {"friendly_name": "Garage Door"},
        },
    ]
    monkeypatch.setattr("jarvis.home_assistant.list_states", lambda **k: states)
    matches = find_entities("living room")
    assert matches[0]["entity_id"] == "light.living_room"


def test_find_entities_with_mock_states(ha_env, monkeypatch):
    states = [
        {
            "entity_id": "scene.goodnight",
            "state": "unknown",
            "attributes": {"friendly_name": "Goodnight"},
        },
    ]
    monkeypatch.setattr("jarvis.home_assistant.list_states", lambda **k: states)
    matches = find_entities("goodnight", domain="scene")
    assert matches[0]["entity_id"] == "scene.goodnight"


def test_control_entity_mocked(ha_env, monkeypatch):
    states = [
        {
            "entity_id": "light.kitchen",
            "state": "on",
            "attributes": {"friendly_name": "Kitchen"},
        },
    ]
    calls = []

    def fake_call(domain, service, data=None):
        calls.append((domain, service, data))
        return {}

    monkeypatch.setattr("jarvis.home_assistant.list_states", lambda **k: states)
    monkeypatch.setattr("jarvis.home_assistant.call_service", fake_call)
    ok, msg = control_entity("kitchen", "off")
    assert ok is True
    assert calls == [("light", "turn_off", {"entity_id": "light.kitchen"})]
    assert "Kitchen" in msg


def test_activate_scene_mocked(ha_env, monkeypatch):
    states = [
        {
            "entity_id": "scene.leaving",
            "state": "unknown",
            "attributes": {"friendly_name": "Leaving"},
        },
    ]
    monkeypatch.setattr("jarvis.home_assistant.list_states", lambda **k: states)
    monkeypatch.setattr(
        "jarvis.home_assistant.call_service",
        lambda d, s, data=None: {"entity_id": data.get("entity_id")},
    )
    monkeypatch.setattr(
        "jarvis.home_assistant.get_state",
        lambda eid: states[0],
    )
    ok, msg = activate_scene("scene.leaving")
    assert ok is True
    assert "Leaving" in msg


def test_check_connection_mocked(ha_env, monkeypatch):
    monkeypatch.setattr(
        "jarvis.home_assistant._request",
        lambda method, path, body=None, timeout=15: {"message": "API running.", "version": "2024.1.0"},
    )
    result = check_connection()
    assert result["ok"] is True
    assert result["version"] == "2024.1.0"


def test_home_summary_mocked(ha_env, monkeypatch):
    states = [
        {"entity_id": "person.jeff", "state": "home", "attributes": {"friendly_name": "Jeff"}},
        {"entity_id": "light.office", "state": "on", "attributes": {"friendly_name": "Office"}},
    ]
    monkeypatch.setattr("jarvis.home_assistant.list_states", lambda **k: states)
    ok, text = home_summary()
    assert ok is True
    assert "Office" in text


def test_verify_automation_secret(ha_env):
    assert verify_automation_secret("hook-secret") is True
    assert verify_automation_secret("wrong") is False


def test_router_ha_routes(ha_env):
    from jarvis.router import route
    from jarvis.session import SessionContext

    session = SessionContext()
    assert route("house status", session)["action"] == "ha_status"
    assert route("home status", session)["action"] == "ha_status"
    assert route("status of my home", session)["action"] == "ha_status"
    assert route("whats on at home", session)["action"] == "ha_status"
    assert route("what's on at home?", session)["action"] == "ha_status"
    assert route("turn off the kitchen light", session)["action"] == "ha_control"
    assert route("activate scene goodnight", session)["action"] == "ha_scene"


def test_router_ha_routes_without_token(monkeypatch):
    from jarvis.router import route
    from jarvis.session import SessionContext

    monkeypatch.delenv("JARVIS_HA_TOKEN", raising=False)
    monkeypatch.setenv("JARVIS_HA_ENABLED", "1")
    session = SessionContext()
    assert route("what lights are on", session)["action"] == "ha_status"
    assert route("check light status", session)["action"] == "ha_status"


def test_automation_inbound_chat(chat_app, ha_env):
    res = chat_app.post(
        "/api/automation/inbound?secret=hook-secret",
        json={"action": "chat", "message": "house status"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data.get("ok") is True or data.get("action") == "ha_status"


def test_automation_inbound_rejects_bad_secret(chat_app, ha_env):
    res = chat_app.post(
        "/api/automation/inbound",
        headers={"X-Jarvis-Automation-Secret": "nope"},
        json={"action": "chat", "message": "hi"},
    )
    assert res.status_code == 401


def test_automation_inbound_disabled_without_secret(chat_app, monkeypatch):
    monkeypatch.setenv("JARVIS_AUTOMATION_SECRET", "")
    res = chat_app.post("/api/automation/inbound", json={"action": "chat", "message": "hi"})
    assert res.status_code == 503


def test_parse_ha_token_message():
    from jarvis.home_assistant import parse_ha_token_message

    assert parse_ha_token_message("set home assistant token: eyJhbG.test.sig") == "eyJhbG.test.sig"
    assert parse_ha_token_message("eyJhbGciOiJIUzI1NiJ9.abc.defghijklmnopqrstuvwxyz") == "eyJhbGciOiJIUzI1NiJ9.abc.defghijklmnopqrstuvwxyz"


def test_router_ha_set_token():
    from jarvis.router import route
    from jarvis.session import SessionContext

    intent = route("set ha token: eyJhbG.test.signature", SessionContext())
    assert intent["action"] == "ha_set_token"
    assert intent["params"]["token"] == "eyJhbG.test.signature"


def test_normalize_ha_token():
    from jarvis.home_assistant import normalize_ha_token

    assert normalize_ha_token('  "eyJabc.def.ghi"  ') == "eyJabc.def.ghi"
    assert normalize_ha_token("Bearer eyJx.y.z") == "eyJx.y.z"
    assert normalize_ha_token("eyJx\ny\nz") == "eyJxyz"


def test_test_connection_401_message():
    from jarvis.home_assistant import test_connection

    result = test_connection(url="http://127.0.0.1:8123", token="not-a-real-token")
    assert result["ok"] is False
    assert "401" in result["message"] or "Invalid" in result["message"]


def test_save_config(data_dir, monkeypatch):
    env_file = data_dir / "jarvis.env"
    monkeypatch.setattr("jarvis.env_loader.ENV_FILE", env_file)
    from jarvis.home_assistant import save_config, status_payload

    result = save_config(
        url="http://127.0.0.1:8123",
        enabled=True,
        ensure_automation_secret=True,
    )
    assert "JARVIS_HA_URL" in result.get("changed", [])
    assert env_file.is_file()
    payload = status_payload()
    assert payload["url"] == "http://127.0.0.1:8123"
    assert payload["automation_secret_set"] is True
