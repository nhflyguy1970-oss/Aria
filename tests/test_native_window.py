"""Tests for native window launcher."""

from jarvis.gui_launcher import _app_url, gui_mode, open_gui
from jarvis.native_window import is_available


def test_gui_mode_defaults_app(monkeypatch):
    monkeypatch.delenv("JARVIS_GUI_MODE", raising=False)
    assert gui_mode() == "app"


def test_gui_mode_native(monkeypatch):
    monkeypatch.setenv("JARVIS_GUI_MODE", "native")
    assert gui_mode() == "native"


def test_open_gui_prefers_native_when_available(monkeypatch):
    monkeypatch.setenv("JARVIS_GUI_MODE", "native")
    calls = {"native": 0, "browser": 0}

    monkeypatch.setattr("jarvis.native_window.is_available", lambda: True)
    monkeypatch.setattr(
        "jarvis.native_window.launch_native_window",
        lambda url: calls.__setitem__("native", calls["native"] + 1) or True,
    )
    monkeypatch.setattr(
        "jarvis.browser_util.open_url",
        lambda url, app_window=None: calls.__setitem__("browser", calls["browser"] + 1) or True,
    )

    assert open_gui("http://127.0.0.1:8765") is True
    assert calls["native"] == 1
    assert calls["browser"] == 0


def test_open_gui_auto_uses_chrome_app(monkeypatch):
    monkeypatch.setenv("JARVIS_GUI_MODE", "auto")
    calls = {"url": None, "app_window": None}

    def fake_open(url, app_window=None):
        calls["url"] = url
        calls["app_window"] = app_window
        return True

    monkeypatch.setattr("jarvis.gui_launcher.open_url", fake_open)
    assert open_gui("http://127.0.0.1:8765") is True
    assert calls["url"] == "http://127.0.0.1:8765?app=1"
    assert calls["app_window"] is True


def test_open_gui_app_mode(monkeypatch):
    monkeypatch.setenv("JARVIS_GUI_MODE", "app")
    calls = {"url": None, "app_window": None}

    def fake_open(url, app_window=None):
        calls["url"] = url
        calls["app_window"] = app_window
        return True

    monkeypatch.setattr("jarvis.gui_launcher.open_url", fake_open)
    assert open_gui("http://127.0.0.1:8765") is True
    assert calls["url"] == "http://127.0.0.1:8765?app=1"
    assert calls["app_window"] is True


def test_is_available_with_qt(monkeypatch):
    monkeypatch.delenv("PYWEBVIEW_GUI", raising=False)
    monkeypatch.setattr("jarvis.native_window._can_use_gtk", lambda: False)
    monkeypatch.setattr("jarvis.native_window._can_use_qt", lambda: True)
    assert is_available() is True


def test_select_backend_prefers_qt_when_configured(monkeypatch):
    from jarvis.native_window import _select_backend

    monkeypatch.delenv("PYWEBVIEW_GUI", raising=False)
    monkeypatch.setenv("JARVIS_PREFER_QT_WEBVIEW", "1")
    monkeypatch.setattr("jarvis.native_window._can_use_gtk", lambda: True)
    monkeypatch.setattr("jarvis.native_window._can_use_qt", lambda: True)
    assert _select_backend() == "qt"


def test_app_url_adds_query():
    assert _app_url("http://127.0.0.1:8765") == "http://127.0.0.1:8765?app=1"
    assert _app_url("http://127.0.0.1:8765?x=1") == "http://127.0.0.1:8765?x=1&app=1"
    assert _app_url("http://127.0.0.1:8765?app=1") == "http://127.0.0.1:8765?app=1"
