"""Request full Jarvis shutdown from the GUI (handled by tray parent)."""

from __future__ import annotations

import logging
import os
import signal
import threading
import time
from pathlib import Path

from jarvis.config import DATA_DIR

logger = logging.getLogger("jarvis.server_shutdown")

SHUTDOWN_FLAG = DATA_DIR / "shutdown_jarvis.request"


def is_tray_managed() -> bool:
    return os.getenv("JARVIS_SERVICES_MANAGED") == "1"


def _signal_tray_shutdown() -> bool:
    """Ask serve's parent (tray) to quit via SIGUSR2."""
    try:
        parent = os.getppid()
        if parent <= 1:
            return False
        os.kill(parent, signal.SIGUSR2)
        return True
    except OSError as exc:
        logger.warning("Could not signal tray for shutdown: %s", exc)
        return False


def _free_vram_best_effort() -> None:
    try:
        from jarvis.vram_guard import free_vram

        free_vram()
    except Exception as exc:
        logger.debug("VRAM free before shutdown skipped: %s", exc)


def _exit_serve_process(delay: float = 0.35) -> None:
    def _do() -> None:
        time.sleep(delay)
        try:
            os.kill(os.getpid(), signal.SIGTERM)
        except OSError:
            os._exit(0)

    threading.Thread(target=_do, name="jarvis-serve-exit", daemon=True).start()


def request_shutdown(
    *,
    source: str = "api",
    detail: str = "",
    free_vram: bool = False,
) -> dict[str, object]:
    """Stop Jarvis completely — tray + server + watchdog (not a restart)."""
    from jarvis.restart_audit import log_restart_event

    log_restart_event(source, detail=detail or "request_shutdown")

    if free_vram:
        _free_vram_best_effort()

    if is_tray_managed():
        if _signal_tray_shutdown():
            logger.info("Shutdown requested — signaled tray (SIGUSR2)")
            return {"ok": True, "message": "ARIA is shutting down…"}
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            SHUTDOWN_FLAG.write_text(str(time.time()), encoding="utf-8")
        except OSError as exc:
            return {"ok": False, "message": f"Could not queue shutdown: {exc}"}
        logger.info("Shutdown requested — flag file (tray watcher)")
        return {"ok": True, "message": "ARIA is shutting down…"}

    _exit_serve_process()
    return {
        "ok": True,
        "message": "Server stopping (standalone mode — tray not running).",
    }


def consume_shutdown_request() -> bool:
    """True if shutdown was requested (flag cleared). Tray process only."""
    if not SHUTDOWN_FLAG.is_file():
        return False
    try:
        SHUTDOWN_FLAG.unlink()
    except OSError:
        pass
    return True


def start_shutdown_watcher(on_shutdown) -> None:
    """Poll for GUI shutdown requests (tray process only)."""

    def _loop() -> None:
        while True:
            time.sleep(1.0)
            try:
                if consume_shutdown_request():
                    logger.info("Processing GUI shutdown request (flag file)")
                    on_shutdown()
            except Exception:
                logger.exception("Shutdown watcher error")

    threading.Thread(target=_loop, name="jarvis-shutdown-watcher", daemon=True).start()
