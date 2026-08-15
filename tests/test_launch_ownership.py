"""Canonical systemd launch ownership — one production HTTP server."""

from __future__ import annotations


def test_launch_owner_explicit_systemd(monkeypatch):
    monkeypatch.setenv("JARVIS_LAUNCH_OWNER", "systemd")
    monkeypatch.setenv("JARVIS_SERVICES_MANAGED", "1")
    from jarvis.launch_ownership import launch_owner

    assert launch_owner() == "systemd"


def test_launch_owner_tray_when_managed(monkeypatch):
    monkeypatch.delenv("JARVIS_LAUNCH_OWNER", raising=False)
    monkeypatch.setenv("JARVIS_SERVICES_MANAGED", "1")
    from jarvis.launch_ownership import launch_owner

    assert launch_owner() == "tray"


def test_launch_owner_self_default(monkeypatch):
    monkeypatch.delenv("JARVIS_LAUNCH_OWNER", raising=False)
    monkeypatch.delenv("JARVIS_SERVICES_MANAGED", raising=False)
    monkeypatch.delenv("INVOCATION_ID", raising=False)
    from jarvis.launch_ownership import launch_owner

    assert launch_owner() == "self"


def test_canonical_owns_server_from_env(monkeypatch):
    monkeypatch.setenv("JARVIS_LAUNCH_OWNER", "systemd")
    from jarvis.launch_ownership import canonical_owns_server

    assert canonical_owns_server() is True
