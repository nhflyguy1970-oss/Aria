"""Desktop shell tests (P4 #88 / #89)."""

from __future__ import annotations


def test_gui_mode_electron_pyside(monkeypatch):
    from jarvis.gui_launcher import gui_mode

    monkeypatch.setenv("JARVIS_GUI_MODE", "electron")
    assert gui_mode() == "electron"
    monkeypatch.setenv("JARVIS_GUI_MODE", "pyside")
    assert gui_mode() == "pyside"
    monkeypatch.setenv("JARVIS_GUI_MODE", "fluent")
    assert gui_mode() == "fluent"


def test_open_gui_electron(monkeypatch):
    from jarvis.gui_launcher import open_gui

    monkeypatch.setenv("JARVIS_GUI_MODE", "electron")
    calls = {"n": 0}
    monkeypatch.setattr("jarvis.electron_shell.is_available", lambda: True)
    monkeypatch.setattr(
        "jarvis.electron_shell.launch_electron_shell",
        lambda url: calls.__setitem__("n", calls["n"] + 1) or True,
    )
    assert open_gui("http://127.0.0.1:8765") is True
    assert calls["n"] == 1


def test_open_gui_pyside(monkeypatch):
    from jarvis.gui_launcher import open_gui

    monkeypatch.setenv("JARVIS_GUI_MODE", "pyside")
    calls = {"n": 0}
    monkeypatch.setattr("jarvis.pyside_shell.is_available", lambda: True)
    monkeypatch.setattr(
        "jarvis.pyside_shell.launch_pyside_shell",
        lambda url: calls.__setitem__("n", calls["n"] + 1) or True,
    )
    assert open_gui("http://127.0.0.1:8765") is True
    assert calls["n"] == 1


def test_desktop_shell_app_url():
    from jarvis.desktop_shell import app_url

    assert "app=1" in app_url("http://127.0.0.1:8765")


def test_electron_status_shape():
    from jarvis.electron_shell import status

    st = status()
    assert "available" in st
    assert "installed" in st


def test_pyside_status_shape():
    from jarvis.pyside_shell import status

    st = status()
    assert "available" in st
    assert "fluent" in st


def test_p4_shell_flags():
    from jarvis.p4_flags import electron_shell_enabled, pyside_shell_enabled

    assert isinstance(electron_shell_enabled(), bool)
    assert isinstance(pyside_shell_enabled(), bool)
