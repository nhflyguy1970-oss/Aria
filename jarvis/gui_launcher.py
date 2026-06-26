"""Unified GUI launcher: Chrome app, Electron, PySide6, or legacy pywebview native."""

from __future__ import annotations

import logging
import os
import sys

from jarvis.browser_util import open_url

logger = logging.getLogger("jarvis.gui_launcher")

_SHELL_MODES = frozenset(
    {"app", "browser", "native", "auto", "electron", "pyside", "fluent"}
)


def gui_mode() -> str:
    """Return app | browser | native | electron | pyside | fluent | auto."""
    mode = os.getenv("JARVIS_GUI_MODE", "fluent").strip().lower()
    if mode in _SHELL_MODES:
        return mode
    return "fluent"


def _app_url(url: str) -> str:
    from jarvis.desktop_shell import app_url

    return app_url(url)


def _chrome_fallback(url: str) -> bool:
    launch_url = _app_url(url)
    if open_url(launch_url, app_window=True):
        return True
    return open_url(launch_url, app_window=False)


def open_gui(url: str) -> bool:
    """Open Jarvis UI in the configured desktop shell."""
    mode = gui_mode()

    if mode == "electron":
        from jarvis.electron_shell import is_available, launch_electron_shell, missing_dependency_hint

        if is_available():
            if launch_electron_shell(url):
                return True
            logger.warning("Electron shell launch failed")
        else:
            logger.warning(missing_dependency_hint())
        return _chrome_fallback(url)

    if mode in ("pyside", "fluent"):
        from jarvis.pyside_shell import can_run_window, is_available, launch_pyside_shell, missing_dependency_hint

        if is_available() and can_run_window():
            if launch_pyside_shell(url):
                return True
            logger.warning("PySide shell launch failed — falling back to Chrome app window")
        else:
            logger.warning(missing_dependency_hint())
        return _chrome_fallback(url)

    if mode == "native":
        from jarvis.native_window import is_available, launch_native_window, missing_dependency_hint

        if is_available():
            if launch_native_window(url):
                return True
            logger.warning("Native window launch failed")
        else:
            logger.warning(missing_dependency_hint())
        return _chrome_fallback(url)

    use_app_window = mode in ("app", "auto")
    launch_url = _app_url(url) if use_app_window else url
    if open_url(launch_url, app_window=use_app_window):
        return True
    if mode == "browser":
        return False
    return open_url(launch_url, app_window=False)


def main(argv: list[str] | None = None) -> int:
    from jarvis.env_loader import load_jarvis_env

    load_jarvis_env()
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print("Usage: python -m jarvis.gui_launcher <url>", file=sys.stderr)
        return 2
    return 0 if open_gui(args[0]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
