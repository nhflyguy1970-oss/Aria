"""Request Jarvis HTTP server restart from the GUI (handled by tray parent)."""

from __future__ import annotations

import logging
import os
import signal
import time
from pathlib import Path

from jarvis.config import DATA_DIR

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


def request_restart(*, source: str = "api", detail: str = "") -> dict[str, object]:
    """Ask the tray/daemon parent to restart the serve subprocess."""
    from jarvis.restart_audit import log_restart_event

    log_restart_event(source, detail=detail or "request_restart")
    if not is_tray_managed():
        return {
            "ok": False,
            "message": (
                "Server restart needs the tray launcher. "
                "Run `./scripts/stop-jarvis.sh` then `./scripts/launch-jarvis.sh`, "
                "or `./scripts/restart-jarvis-server.sh` from a terminal."
            ),
        }

    if _signal_tray_restart():
        logger.info("Server restart requested — signaled tray (SIGUSR1)")
        return {"ok": True, "message": "Jarvis server restarting…"}

    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        RESTART_FLAG.write_text(str(time.time()), encoding="utf-8")
    except OSError as exc:
        return {"ok": False, "message": f"Could not queue restart: {exc}"}

    logger.info("Server restart requested — flag file (tray watcher)")
    return {"ok": True, "message": "Jarvis server restarting…"}


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
    import threading

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

    threading.Thread(target=_loop, name="jarvis-restart-watcher", daemon=True).start()
