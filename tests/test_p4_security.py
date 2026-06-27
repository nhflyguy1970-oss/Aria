"""P4 security, presence, and shell tests."""

from __future__ import annotations

import base64
import os


def test_p4_flags_includes_p3():
    from jarvis.p4_flags import p4_flags

    flags = p4_flags()
    assert "cad" in flags or "projects" in flags
    assert "pin_lock" in flags
    assert "floating_panels" in flags


def test_pin_set_and_verify(tmp_path, monkeypatch):
    pin_file = tmp_path / "pin.json"
    monkeypatch.setattr("jarvis.security.pin_lock.PIN_FILE", pin_file)
    from jarvis.security.pin_lock import pin_configured, set_pin, verify_pin

    assert not pin_configured()
    set_pin("1234")
    assert pin_configured()
    assert verify_pin("1234")
    assert not verify_pin("9999")


def test_pin_rejects_invalid():
    from jarvis.security.pin_lock import set_pin

    try:
        set_pin("12")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_session_lifecycle(tmp_path, monkeypatch):
    sess_file = tmp_path / "sessions.json"
    monkeypatch.setattr("jarvis.security.pin_lock.SESSIONS_FILE", sess_file)
    monkeypatch.setenv("JARVIS_PIN_LOCK", "1")
    monkeypatch.setattr("jarvis.security.pin_lock.PIN_FILE", tmp_path / "pin.json")
    from jarvis.security.pin_lock import create_session, revoke_session, session_valid, set_pin, touch_session

    set_pin("4321")
    token = create_session(device_id="test-dev")
    assert session_valid(token)
    assert touch_session(token)
    revoke_session(token)
    assert not session_valid(token)


def test_trusted_device(tmp_path, monkeypatch):
    store = tmp_path / "trusted.json"
    monkeypatch.setattr("jarvis.security.trusted_devices.STORE", store)
    monkeypatch.setenv("JARVIS_TRUSTED_LAN", "1")
    from jarvis.security.trusted_devices import is_trusted, trust_device

    trust_device("dev-abc", label="Test", client_ip="10.0.0.5")
    assert is_trusted("dev-abc", client_ip="10.0.0.5")
    assert not is_trusted("dev-other", client_ip="10.0.0.5")


def test_brain_mode_status():
    from jarvis.security.brain_mode import brain_mode_status

    st = brain_mode_status()
    assert st["mode"] in ("local", "cloud", "hybrid", "offline")
    assert "label" in st


def test_tools_status():
    from jarvis.security.tools_status import tools_status

    rows = tools_status()
    assert isinstance(rows, list)
    assert any(r.get("name") == "PIN lock" for r in rows)


def test_face_enroll_verify(tmp_path, monkeypatch):
    face_file = tmp_path / "face_profile.json"
    face_img = tmp_path / "face_enroll.jpg"
    monkeypatch.setattr("jarvis.security.face_auth.FACE_FILE", face_file)
    monkeypatch.setattr("jarvis.security.face_auth.FACE_IMG", face_img)
    monkeypatch.setenv("JARVIS_FACE_AUTH", "1")
    from jarvis.security.face_auth import enroll_face, verify_face

    # 1x1 white JPEG
    tiny = base64.b64encode(
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\x27 ,#\x1c\x1c(7),01444\x1f\x27=9=82<.7\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfe\x8a(\xa2\x8f\xff\xd9"
    ).decode()
    data_url = f"data:image/jpeg;base64,{tiny}"
    er = enroll_face(data_url)
    assert er.get("ok") is True
    vr = verify_face(data_url)
    assert vr.get("ok") is True


def test_lock_status():
    from jarvis.security.pin_lock import lock_status

    st = lock_status()
    assert "pin_lock_enabled" in st
    assert "idle_seconds" in st
