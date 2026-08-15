"""Request Jarvis HTTP server restart from the GUI.

Supports two paths:
1. Tray-managed (JARVIS_SERVICES_MANAGED=1): signal parent tray via SIGUSR1 / flag file.
2. Standalone serve (no tray): spawn a successor process, then graceful SIGTERM self.
"""

from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

from jarvis.config import DATA_DIR, PROJECT_ROOT
from jarvis.security.owner.env_boundary import copy_process_env

logger = logging.getLogger("jarvis.server_restart")

RESTART_FLAG = DATA_DIR / "restart_server.request"


def is_tray_managed() -> bool:
    return os.getenv("JARVIS_SERVICES_MANAGED") == "1"


def _signal_tray_restart() -> bool:
    """Ask serve's parent (tray) to restart via SIGUSR1."""
    try:
        parent = os.getppid()
        if parent <= 1:
            return False
        os.kill(parent, signal.SIGUSR1)
        return True
    except OSError as exc:
        logger.warning("Could not signal tray for restart: %s", exc)
        return False


def _schedule_self_exit(delay_s: float = 0.4) -> None:
    """Gracefully stop this serve process after the HTTP response is sent."""

    def _exit() -> None:
        time.sleep(delay_s)
        logger.info("Self-restart: sending SIGTERM to pid %s", os.getpid())
        try:
            os.kill(os.getpid(), signal.SIGTERM)
        except OSError:
            os._exit(0)

    threading.Thread(target=_exit, name="jarvis-self-restart-exit", daemon=True).start()


def _spawn_successor_serve() -> bool:
    """Detach a helper that waits for this process to exit, then starts a new serve."""
    old_pid = os.getpid()
    py = sys.executable
    root = str(PROJECT_ROOT)
    log_path = str(DATA_DIR / "logs" / "serve.log")
    helper = f"""
import os, subprocess, sys, time, urllib.request
old = {old_pid}
root = {root!r}
py = {py!r}
log_path = {log_path!r}
port = os.environ.get("JARVIS_PORT", "8765")
host = os.environ.get("JARVIS_HOST", "127.0.0.1")
if host in ("0.0.0.0", "::", "::0"):
    host = "127.0.0.1"
live = f"http://{{host}}:{{port}}/api/live"

def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True

for _ in range(240):
    if not alive(old):
        break
    time.sleep(0.25)
else:
    sys.exit(2)

time.sleep(0.6)
os.makedirs(os.path.dirname(log_path), exist_ok=True)
from jarvis.security.owner.env_boundary import copy_process_env
env = copy_process_env(extra={"JARVIS_NO_BROWSER": "1"})
env.pop("JARVIS_SERVICES_MANAGED", None)
with open(log_path, "a", encoding="utf-8") as log:
    log.write(f"\\n# self-restart successor after pid {{old}}\\n")
    log.flush()
    proc = subprocess.Popen(
        [py, os.path.join(root, "main.py"), "serve"],
        cwd=root,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
for _ in range(90):
    time.sleep(0.5)
    try:
        with urllib.request.urlopen(live, timeout=2) as r:
            if r.status == 200 and proc.poll() is None:
                sys.exit(0)
    except Exception:
        if proc.poll() is not None:
            sys.exit(3)
sys.exit(4)
"""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        (DATA_DIR / "logs").mkdir(parents=True, exist_ok=True)
        subprocess.Popen(
            [py, "-c", helper],
            cwd=root,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=copy_process_env(),
        )
        return True
    except OSError as exc:
        logger.exception("Failed to spawn successor serve: %s", exc)
        return False


def _schedule_systemd_restart(delay_s: float = 0.4) -> None:
    def _run() -> None:
        time.sleep(delay_s)
        from jarvis.launch_ownership import systemd_restart

        if not systemd_restart():
            logger.error("systemd restart of jarvis.service failed")

    threading.Thread(target=_run, name="jarvis-systemd-restart", daemon=True).start()


def request_restart(*, source: str = "api", detail: str = "") -> dict[str, object]:
    """Restart the HTTP server — systemd (canonical), tray-managed, or self-reexec."""
    from jarvis.restart_audit import log_restart_event

    log_restart_event(source, detail=detail or "request_restart")

    from jarvis.launch_ownership import launch_owner

    if launch_owner() == "systemd":
        _schedule_systemd_restart()
        logger.info("Server restart requested — systemd --user jarvis.service")
        return {"ok": True, "message": "Jarvis server restarting…", "mode": "systemd"}

    if is_tray_managed():
        if _signal_tray_restart():
            logger.info("Server restart requested — signaled tray (SIGUSR1)")
            return {"ok": True, "message": "Jarvis server restarting…", "mode": "tray"}

        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            RESTART_FLAG.write_text(str(time.time()), encoding="utf-8")
        except OSError as exc:
            return {"ok": False, "message": f"Could not queue restart: {exc}"}

        logger.info("Server restart requested — flag file (tray watcher)")
        return {"ok": True, "message": "Jarvis server restarting…", "mode": "tray_flag"}

    # No tray / no systemd: spawn successor then graceful shutdown of this process.
    if not _spawn_successor_serve():
        return {
            "ok": False,
            "message": "Could not start successor server process for restart.",
        }
    _schedule_self_exit()
    logger.info("Server restart requested — self-restart (no tray)")
    return {"ok": True, "message": "Jarvis server restarting…", "mode": "self"}


def consume_restart_request() -> bool:
    """True if a restart was requested (flag cleared). Called from tray process only."""
    if not RESTART_FLAG.is_file():
        return False
    try:
        RESTART_FLAG.unlink()
    except OSError:
        pass
    return True


def start_restart_watcher(on_restart) -> None:
    """Poll for GUI restart requests (tray process only). Backup if SIGUSR1 missed."""
    import threading as _threading

    def _loop() -> None:
        while True:
            time.sleep(1.0)
            try:
                if consume_restart_request():
                    logger.info("Processing GUI restart request (flag file)")
                    from jarvis.restart_audit import log_restart_event

                    log_restart_event("flag", detail="restart_server.request file")
                    on_restart()
            except Exception:
                logger.exception("Restart watcher error")

    _threading.Thread(target=_loop, name="jarvis-restart-watcher", daemon=True).start()
