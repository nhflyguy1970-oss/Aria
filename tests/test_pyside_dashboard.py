"""PySide native dashboard widget tests."""

from __future__ import annotations


def test_pyside_dashboard_module_imports():
    from jarvis.gui.pyside import api_client, dashboard, styles

    assert api_client.fetch_dashboard
    assert dashboard.DashboardView
    assert styles.AURA_STYLESHEET


def test_fluent_shell_availability():
    from jarvis.gui.pyside.fluent_shell import fluent_shell_available
    from jarvis.pyside_shell import _native_dashboard_enabled, is_available

    assert is_available()
    # fluent_shell_available depends on optional pip package
    _ = fluent_shell_available()
    _ = _native_dashboard_enabled()
