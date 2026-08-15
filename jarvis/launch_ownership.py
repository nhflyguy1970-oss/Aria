"""Canonical production launch ownership — systemd owns the HTTP server.

Tray and desktop launchers attach to the existing server. They must not spawn
a second serve process when systemd is the owner.
"""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger("jarvis.launch_ownership")

UNIT = "jarvis.service"


def launch_owner() -> str:
    """Who is authoritative for the production HTTP server: systemd | tray | self."""
    explicit = (os.getenv("JARVIS_LAUNCH_OWNER") or "").strip().lower()
    if explicit in ("systemd", "tray", "self"):
        return explicit
    if os.getenv("INVOCATION_ID") and _parent_is_systemd():
        return "systemd"
    if os.getenv("JARVIS_SERVICES_MANAGED") == "1":
        return "tray"
    return "self"


def _parent_is_systemd() -> bool:
    try:
        ppid = os.getppid()
        if ppid <= 1:
            return True
        comm = Path(f"/proc/{ppid}/comm").read_text(encoding="utf-8").strip()
        return comm == "systemd"
    except OSError:
        return False


def unit_path() -> Path:
    return Path.home() / ".config" / "systemd" / "user" / UNIT


def systemd_unit_installed() -> bool:
    return unit_path().is_file()


def _systemctl(*args: str, timeout: float = 45) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["systemctl", "--user", *args],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def systemd_is_active() -> bool:
    try:
        result = _systemctl("is-active", UNIT, timeout=8)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and result.stdout.strip() == "active"


def systemd_is_enabled() -> bool:
    try:
        result = _systemctl("is-enabled", UNIT, timeout=8)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and result.stdout.strip() == "enabled"


def systemd_start() -> bool:
    try:
        result = _systemctl("start", UNIT)
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.warning("systemctl start failed: %s", exc)
        return False
    if result.returncode != 0:
        logger.warning("systemctl start %s: %s", UNIT, (result.stderr or result.stdout).strip())
        return False
    return True


def systemd_stop() -> bool:
    try:
        result = _systemctl("stop", UNIT)
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.warning("systemctl stop failed: %s", exc)
        return False
    return result.returncode == 0


def systemd_restart() -> bool:
    try:
        result = _systemctl("restart", UNIT)
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.warning("systemctl restart failed: %s", exc)
        return False
    if result.returncode != 0:
        logger.warning("systemctl restart %s: %s", UNIT, (result.stderr or result.stdout).strip())
        return False
    return True


def canonical_owns_server() -> bool:
    """True when systemd is (or should be) the single production server owner."""
    if launch_owner() == "systemd":
        return True
    return systemd_unit_installed() and systemd_is_active()


def ensure_canonical_server() -> bool:
    """Start the systemd unit if installed and the server is not up. Never spawn a second serve."""
    if not systemd_unit_installed():
        return False
    if systemd_is_active():
        return True
    return systemd_start()
