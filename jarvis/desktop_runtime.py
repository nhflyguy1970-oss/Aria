"""Desktop GUI/runtime probes — PySide X11, system tray, browser fallback."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger("jarvis.desktop_runtime")

_XCB_CURSOR_CANDIDATES = (
    "/usr/lib/x86_64-linux-gnu/libxcb-cursor.so.0",
    "/usr/lib/aarch64-linux-gnu/libxcb-cursor.so.0",
    "/usr/lib/libxcb-cursor.so.0",
)

_APPINDICATOR_CANDIDATES = (
    "/usr/lib/x86_64-linux-gnu/libayatana-appindicator3.so.1",
    "/usr/lib/x86_64-linux-gnu/libappindicator3.so.1",
    "/usr/lib/aarch64-linux-gnu/libayatana-appindicator3.so.1",
    "/usr/lib/aarch64-linux-gnu/libappindicator3.so.1",
)


def libxcb_cursor_installed() -> bool:
    if any(Path(p).is_file() for p in _XCB_CURSOR_CANDIDATES):
        return True
    if shutil.which("dpkg"):
        try:
            proc = subprocess.run(
                ["dpkg", "-s", "libxcb-cursor0"],
                capture_output=True,
                timeout=5,
            )
            return proc.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            pass
    return False


def appindicator_installed() -> bool:
    if any(Path(p).is_file() for p in _APPINDICATOR_CANDIDATES):
        return True
    if shutil.which("dpkg"):
        for pkg in ("libayatana-appindicator3-1", "libappindicator3-1"):
            try:
                proc = subprocess.run(["dpkg", "-s", pkg], capture_output=True, timeout=5)
                if proc.returncode == 0:
                    return True
            except (OSError, subprocess.TimeoutExpired):
                pass
    return False


def pyside_import_ok() -> bool:
    try:
        from PySide6.QtWidgets import QApplication  # noqa: F401

        return True
    except ImportError:
        return False


def pyside_window_ready() -> bool:
    """True when PySide can create an X11/Wayland window (not just import)."""
    if not pyside_import_ok():
        return False
    session = (os.getenv("XDG_SESSION_TYPE") or "").strip().lower()
    if session == "wayland":
        return True
    return libxcb_cursor_installed()


def tray_panel_ready() -> bool:
    """GNOME/KDE need Ayatana AppIndicator for pystray icons to appear."""
    return appindicator_installed()


def desktop_deps_hint() -> str:
    missing: list[str] = []
    if not libxcb_cursor_installed():
        missing.append("libxcb-cursor0")
    if not appindicator_installed():
        missing.append("libayatana-appindicator3-1")
    if not missing:
        return ""
    return "sudo apt install " + " ".join(missing)


def log_desktop_status() -> dict[str, bool]:
    status = {
        "pyside_import": pyside_import_ok(),
        "pyside_window": pyside_window_ready(),
        "xcb_cursor": libxcb_cursor_installed(),
        "tray_indicator": tray_panel_ready(),
    }
    hint = desktop_deps_hint()
    if hint:
        logger.warning("Desktop deps missing (%s) — run: %s", status, hint)
    else:
        logger.info("Desktop runtime OK: %s", status)
    return status
