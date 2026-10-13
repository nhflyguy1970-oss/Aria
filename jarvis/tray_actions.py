"""What the tray menu does, kept apart from pystray so it can be tested.

The tray is a client: the HTTP server is the systemd --user ``jarvis.service``
and the AI backend is the system ``ollama.service`` (port 11434) plus ARIA's
user ``aria-vulkan-helper.service``. Nothing here touches fans, clocks or
power limits, and the fly-tying Ollama instances (11435/11436) are not ARIA's.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

logger = logging.getLogger("jarvis.tray")

LOG_DIR = DATA_DIR / "logs"
OLLAMA_URL = os.getenv("OLLAMA_HOST_URL", "http://127.0.0.1:11434")
BACKEND_SYSTEM_UNIT = "ollama.service"
BACKEND_USER_UNITS = ("aria-vulkan-helper.service",)
BACKEND_READY_TIMEOUT_S = 60.0


@dataclass
class Snapshot:
    """One status poll. ``server`` is the only field the menu's enabled states use."""

    server: bool = False
    backend: bool = False
    models_loaded: list[str] = field(default_factory=list)
    busy: str = ""
    gpu: str = ""

    @property
    def label(self) -> str:
        if not self.server:
            return "Status: stopped"
        if not self.backend:
            return "Status: running — AI backend offline"
        return f"Status: running — {self.busy}" if self.busy else "Status: running"

    def detail(self) -> str:
        lines = [
            f"Server: {'running' if self.server else 'stopped'}",
            f"AI backend: {'online' if self.backend else 'offline'}",
        ]
        if self.models_loaded:
            lines.append("Loaded: " + ", ".join(self.models_loaded))
        if self.busy:
            lines.append(f"Busy: {self.busy}")
        if self.gpu:
            lines.append(self.gpu)
        return "\n".join(lines)


def _get_json(url: str, timeout: float = 3) -> dict[str, Any] | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode() or "{}")
    except Exception:  # noqa: BLE001 - any failure means "not answering"
        return None


def busy_reason(scheduler: dict[str, Any] | None) -> str:
    """Why restarting the backend now would cut off work ('' = safe)."""
    if not scheduler:
        return ""
    if scheduler.get("heavy_active"):
        return f"GPU job running ({scheduler['heavy_active']})"
    if int(scheduler.get("shared_active") or 0) > 0:
        return "a reply is being generated"
    if int(scheduler.get("waiting") or 0) > 0:
        return "jobs are queued for the GPU"
    return ""


def snapshot(url: str) -> Snapshot:
    snap = Snapshot()
    snap.server = _get_json(f"{url}/api/ping") is not None
    ps = _get_json(f"{OLLAMA_URL}/api/ps")
    snap.backend = ps is not None
    if ps:
        snap.models_loaded = [m.get("name", "?") for m in ps.get("models") or []]
    if snap.server:
        sched = _get_json(f"{url}/api/gpu-scheduler/status")
        snap.busy = busy_reason(sched)
        cuda = (sched or {}).get("cuda") or {}
        if cuda.get("ok"):
            snap.gpu = f"RTX 3060: {cuda.get('temp_c')}°C, {cuda.get('used_mib')} MiB used"
    return snap


# ------------------------------------------------------------------ server


def start_aria(start_fallback=None) -> tuple[bool, str]:
    from jarvis.launch_ownership import systemd_start, systemd_unit_installed

    if systemd_unit_installed():
        return (True, "ARIA started") if systemd_start() else (False, "systemctl start jarvis.service failed")
    if start_fallback is not None:
        start_fallback()
        return True, "ARIA server started"
    return False, "No jarvis.service installed"


def stop_aria() -> tuple[bool, str]:
    from jarvis.launch_ownership import systemd_stop, systemd_unit_installed

    if not systemd_unit_installed():
        return False, "Stop needs jarvis.service; use Quit ARIA Completely"
    return (True, "ARIA stopped (tray stays available)") if systemd_stop() else (False, "systemctl stop failed")


def restart_aria(restart) -> tuple[bool, str]:
    restart()
    return True, "ARIA server restarting"


# ------------------------------------------------------------------ AI backend


def _run(cmd: list[str], timeout: float) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)


def _user_unit_active(unit: str) -> bool:
    try:
        return _run(["systemctl", "--user", "is-active", unit], 8).stdout.strip() == "active"
    except Exception:  # noqa: BLE001
        return False


def _wait_backend(timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _get_json(f"{OLLAMA_URL}/api/version", timeout=2) is not None:
            return True
        time.sleep(1)
    return False


def restart_ai_backend(url: str, *, ready_timeout: float = BACKEND_READY_TIMEOUT_S) -> tuple[bool, str]:
    """Restart ARIA's Ollama; refuses while a reply or GPU job would be cut off.

    ``ollama.service`` is a system unit, so systemd asks for the owner's password
    through the desktop's polkit dialog; cancelling it changes nothing.
    """
    reason = busy_reason(_get_json(f"{url}/api/gpu-scheduler/status"))
    if reason:
        return False, f"Not restarted: {reason}. Try again when it finishes."
    try:
        result = _run(["systemctl", "restart", BACKEND_SYSTEM_UNIT], 120)
    except subprocess.TimeoutExpired:
        return False, "Restart timed out waiting for authorization"
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()
        return False, "AI backend not restarted: " + (detail[-1] if detail else f"exit {result.returncode}")
    for unit in BACKEND_USER_UNITS:
        if _user_unit_active(unit):
            _run(["systemctl", "--user", "restart", unit], 60)
    if not _wait_backend(ready_timeout):
        return False, "AI backend restarted but is not answering yet"
    return True, "AI backend restarted"


# ------------------------------------------------------------------ logs / settings


def open_path(path: Path) -> bool:
    try:
        subprocess.Popen(["xdg-open", str(path)], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not open %s: %s", path, exc)
        return False


def server_log_snapshot(lines: int = 1000) -> Path:
    """The server logs to the journal; write the recent part where an editor can open it."""
    out = LOG_DIR / "server-journal.log"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        text = _run(["journalctl", "--user", "-u", "jarvis.service", "-n", str(lines),
                     "--no-pager", "-o", "short-iso"], 20).stdout
    except Exception as exc:  # noqa: BLE001
        text = f"journalctl failed: {exc}\n"
    out.write_text(text, encoding="utf-8")
    return out


def settings_url(url: str) -> str:
    return f"{url}#settings"
