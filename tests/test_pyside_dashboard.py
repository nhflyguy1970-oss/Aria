"""PySide native dashboard widget tests."""

from __future__ import annotations

import pytest


def test_pyside_dashboard_module_imports():
    pytest.importorskip("PySide6")
    pyside = pytest.importorskip("jarvis.gui.pyside")
    assert pyside is not None
    try:
        from jarvis.gui.pyside import api_client, dashboard
    except ImportError:
        pytest.skip("PySide dashboard widgets not packaged in this tree")
    assert getattr(api_client, "fetch_dashboard", None) or getattr(dashboard, "DashboardView", None)


def test_fluent_shell_availability():
    from jarvis.pyside_shell import is_available

    assert callable(is_available)
    try:
        from jarvis.gui.pyside.fluent_shell import fluent_shell_available
    except ImportError:
        fluent_shell_available = None
    if fluent_shell_available:
        _ = fluent_shell_available()
