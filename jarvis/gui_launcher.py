"""Unified GUI launcher: Chrome app window (default) or optional pywebview native."""

from __future__ import annotations

import logging
import os
import sys

from jarvis.browser_util import open_url

logger = logging.getLogger("jarvis.gui_launcher")


def gui_mode() -> str:
    """Return app | browser | native | auto (auto → Chrome app window)."""
    mode = os.getenv("JARVIS_GUI_MODE", "app").strip().lower()
    if mode in ("native", "browser", "app", "auto"):
        return mode
    return "app"


def _app_url(url: str) -> str:
    if "app=1" in url:
        return url
    join = "&" if "?" in url else "?"
    return f"{url}{join}app=1"


def open_gui(url: str) -> bool:
    """Open Jarvis UI in Chrome app mode, browser tab, or optional native window."""
    mode = gui_mode()

    if mode == "native":
        from jarvis.native_window import is_available, launch_native_window, missing_dependency_hint

        if is_available():
            if launch_native_window(url):
                return True
            logger.warning("Native window launch failed")
            return False
        logger.warning(missing_dependency_hint())
        return False

    use_app_window = mode in ("app", "auto")
    launch_url = _app_url(url) if use_app_window else url
    if open_url(launch_url, app_window=use_app_window):
        return True
    if mode == "browser":
        return False
    # app/auto: retry without --app-window if Chrome missing app flags
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
