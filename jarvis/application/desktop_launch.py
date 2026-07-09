"""Desktop launch helpers — start Aria server and open GUI."""

from __future__ import annotations

import contextlib
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

from jarvis.env_loader import PROJECT_ROOT, load_jarvis_env

logger = logging.getLogger("jarvis.application.desktop_launch")

_SERVER_PROC: subprocess.Popen | None = None


def _client_host() -> str:
    host = os.getenv("JARVIS_HOST", "127.0.0.1")
    if host in ("0.0.0.0", "::", "::0"):
        return "127.0.0.1"
    return host


def api_responsive(timeout: float = 2) -> bool:
    """True when the Aria HTTP API answers a lightweight probe."""
    from jarvis.services import _http_ok

    port = os.getenv("JARVIS_PORT", "8765")
    base = f"http://{_client_host()}:{port}"
    return _http_ok(f"{base}/api/live", timeout=timeout) or _http_ok(
        f"{base}/api/health", timeout=timeout
    )


def _python_exe() -> str:
    venv = PROJECT_ROOT / "venv" / "bin" / "python"
    if venv.is_file():
        return str(venv)
    return sys.executable


def _tray_available() -> bool:
    if os.getenv("JARVIS_TRAY", "1") == "0":
        return False
    display = os.getenv("DISPLAY", "")
    if not display:
        return False
    try:
        from pystray import Icon  # noqa: F401
        from Xlib import display as xdisplay  # type: ignore[import-untyped]

        xdisplay.Display().close()
        return True
    except Exception:
        return False


def start_aria_server(*, timeout: float = 90) -> bool:
    """Start tray (preferred) or serve in the background and wait for API health."""
    global _SERVER_PROC

    load_jarvis_env()
    from jarvis.services import _jarvis_port_open

    if api_responsive():
        return True

    if _jarvis_port_open() and not api_responsive():
        stop_aria_server()

    env = os.environ.copy()
    env.setdefault("JARVIS_NO_BROWSER", "1")
    env.setdefault("JARVIS_SERVICES_MANAGED", "1")
    main_py = str(PROJECT_ROOT / "main.py")
    log_dir = PROJECT_ROOT / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "jarvis.log"

    mode = "tray" if _tray_available() else "serve"
    if mode == "tray":
        logger.info("Starting Aria tray (owns API server)")
    else:
        logger.info("Tray unavailable — starting headless serve")

    with open(log_file, "a", encoding="utf-8") as log_handle:
        _SERVER_PROC = subprocess.Popen(
            [_python_exe(), main_py, mode],
            cwd=str(PROJECT_ROOT),
            env=env,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    deadline = time.time() + timeout
    while time.time() < deadline:
        if api_responsive():
            return True
        if _SERVER_PROC.poll() is not None and not api_responsive():
            logger.error("Aria %s exited before becoming healthy", mode)
            return False
        time.sleep(0.5)
    return api_responsive()


def stop_aria_server() -> None:
    """Best-effort stop of tray, serve, and GUI processes."""
    global _SERVER_PROC
    if _SERVER_PROC is not None and _SERVER_PROC.poll() is None:
        with contextlib.suppress(Exception):
            _SERVER_PROC.terminate()
            _SERVER_PROC.wait(timeout=5)
    _SERVER_PROC = None

    script = PROJECT_ROOT / "scripts" / "stop-jarvis.sh"
    if script.is_file():
        subprocess.run(["bash", str(script)], cwd=str(PROJECT_ROOT), check=False)
        return

    for pattern in (
        f"{PROJECT_ROOT}/main.py tray",
        f"{PROJECT_ROOT}/main.py serve",
        f"{PROJECT_ROOT}/jarvis/pyside_shell",
        "python -m jarvis.pyside_shell",
    ):
        subprocess.run(["pkill", "-f", pattern], check=False, capture_output=True)


def open_desktop_gui(*, blocking: bool = True) -> int:
    """Open the Aria desktop window via the shared launcher script."""
    script = PROJECT_ROOT / "scripts" / "launch-jarvis.sh"
    if not script.is_file():
        logger.error("Missing launcher script: %s", script)
        return 1
    load_jarvis_env()
    cmd = ["bash", str(script)]
    if blocking:
        return int(subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode)
    subprocess.Popen(cmd, cwd=str(PROJECT_ROOT), start_new_session=True)
    return 0


def desktop_display_available() -> bool:
    """True when a graphical session is available for GUI launch."""
    if os.getenv("JARVIS_HEADLESS", "").strip() in ("1", "true", "yes"):
        return False
    if os.getenv("DISPLAY", "").strip():
        return True
    return Path("/tmp/.X11-unix").is_dir() and any(Path("/tmp/.X11-unix").glob("X*"))
