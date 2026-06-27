"""P5 integration, learning, and ops tests."""

from __future__ import annotations


def test_p5_flags():
    from jarvis.p5_flags import p5_flags

    flags = p5_flags()
    assert flags.get("cad_teaching") is not None
    assert flags.get("pin_lock") is not None


def test_upgrade_apply_confirm(monkeypatch):
    monkeypatch.setenv("JARVIS_TOOL_PERMISSIONS", "1")
    from jarvis.tool_permissions import set_permission

    set_permission("upgrade_apply", "ask")

    class FakeAssistant:
        session = type("S", (), {"last_proposal_id": "p1"})()

        def _upgrade_proposal(self, pid):
            return {"files": [], "verified": True}

    from jarvis.assistant import JarvisAssistant

    # Use minimal mock of method under test
    assistant = object.__new__(JarvisAssistant)
    assistant.session = FakeAssistant.session
    assistant.pending_proposals = {}
    assistant._upgrade_proposal = FakeAssistant()._upgrade_proposal

    from jarvis.assistant import JarvisAssistant as JA

    result = JA._upgrade_apply(assistant, {"proposal_id": "p1"}, "apply")
    assert result.get("type") == "confirm_required"
    assert result.get("confirm_id")


def test_debug_bundle_cad_section():
    from jarvis.debug_bundle import collect

    bundle = collect(log_bytes=500)
    assert "cad_print" in bundle


def test_usb_ports_list():
    from jarvis.engineering.usb_printer import list_serial_ports

    ports = list_serial_ports()
    assert isinstance(ports, list)


def test_voice_cheatsheet_default_exists():
    from jarvis.cheatsheets import default_keys

    assert "voice" in default_keys()
