"""Jarvis background daemon: services + server + watchdog + system tray."""

import logging
import os
import signal
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

from jarvis.env_loader import load_jarvis_env

PROJECT_ROOT = Path(__file__).resolve().parent.parent

from jarvis.lan import bind_port, client_base_url  # noqa: E402

PORT = bind_port()
CLIENT_URL = client_base_url()
HEALTH_URL = f"{CLIENT_URL}/api/health"
LIVE_URL = f"{CLIENT_URL}/api/live"
PING_URL = f"{CLIENT_URL}/api/ping"
LOG_DIR = PROJECT_ROOT / "data" / "logs"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
logger = logging.getLogger("jarvis.daemon")

_server_proc: subprocess.Popen | None = None
_serve_log_handle = None
_watchdog = None
_services_watchdog = None
_restart_lock = threading.Lock()
_restart_in_progress = False


def _setup_file_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(LOG_DIR / "jarvis.log", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(name)s %(message)s"))
    logging.getLogger().addHandler(fh)


def _notify(title: str, body: str) -> None:
    try:
        subprocess.run(
            ["notify-send", "-a", "Jarvis", title, body],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except Exception as exc:
        logger.debug("notify-send failed: %s", exc)


def ensure_ollama() -> bool:
    """Backward-compatible wrapper."""
    from jarvis.services import ensure_ollama as _ensure
    return _ensure()


def start_server(open_browser: bool = False) -> subprocess.Popen:
    global _server_proc, _serve_log_handle
    load_jarvis_env()
    env = os.environ.copy()
    env["JARVIS_NO_BROWSER"] = "1" if not open_browser else "0"
    env["JARVIS_SERVICES_MANAGED"] = "1"
    cmd = [sys.executable, str(PROJECT_ROOT / "main.py"), "serve"]
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    _serve_log_handle = open(LOG_DIR / "serve.log", "a", encoding="utf-8")
    _server_proc = subprocess.Popen(
        cmd,
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=_serve_log_handle,
        stderr=subprocess.STDOUT,
        text=True,
    )
    for _ in range(120):
        time.sleep(0.5)
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=2):
                if _server_proc.poll() is None:
                    logger.info("Jarvis server ready on port %d", PORT)
                    return _server_proc
                logger.warning(
                    "Port %d is up but managed server child exited — attaching without child process",
                    PORT,
                )
                _server_proc = None
                return None
        except Exception:
            if _server_proc.poll() is not None:
                log_tail = ""
                serve_log_path = LOG_DIR / "serve.log"
                if serve_log_path.is_file():
                    log_tail = serve_log_path.read_text(encoding="utf-8", errors="replace")[-4000:]
                raise RuntimeError(f"Server failed to start:\n{log_tail}")
    raise RuntimeError("Server health check timed out")


def stop_server() -> None:
    global _server_proc
    if _server_proc and _server_proc.poll() is None:
        _server_proc.send_signal(signal.SIGTERM)
        try:
            _server_proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            _server_proc.kill()
            try:
                _server_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                pass
    _server_proc = None


def restart_server() -> subprocess.Popen:
    global _watchdog, _restart_in_progress
    with _restart_lock:
        if _restart_in_progress:
            logger.info("Restart already in progress — skipping duplicate request")
            if _server_proc and _server_proc.poll() is None:
                return _server_proc
        _restart_in_progress = True
        try:
            try:
                from jarvis.coding_jobs import has_active_work as coding_active
                from jarvis.media_jobs import has_active_work
                from jarvis.request_activity import active as chat_active

                if has_active_work() or chat_active() or coding_active():
                    if has_active_work():
                        label = "media job"
                    elif coding_active():
                        label = "coding job"
                    else:
                        label = "active chat/coding request"
                    logger.info("Waiting for %s before server restart…", label)
                    for _ in range(600):
                        if not has_active_work() and not chat_active() and not coding_active():
                            break
                        time.sleep(1)
                    if has_active_work() or chat_active() or coding_active():
                        logger.warning("Restart refused — %s still active", label)
                        _notify("Jarvis", "Server restart skipped — coding/chat in progress")
                        if _server_proc and _server_proc.poll() is None:
                            return _server_proc
                        return start_server()
            except Exception:
                pass
            logger.info("Restarting Jarvis server…")
            from jarvis.restart_audit import log_restart_event
            from jarvis.restart_flag import clear_restart_flag, mark_restart_started

            log_restart_event("daemon", detail="restart_server()")
            mark_restart_started()
            try:
                stop_server()
                proc = start_server()
                if _watchdog:
                    _watchdog.set_server_process(proc)
                logger.info("Jarvis server restart complete")
                return proc
            finally:
                clear_restart_flag()
        finally:
            _restart_in_progress = False


_restart_signal_thread: threading.Thread | None = None


def _restart_from_signal() -> None:
    try:
        from jarvis.restart_audit import log_restart_event

        log_restart_event("sigusr1", detail="tray received SIGUSR1")
        restart_server()
        _notify("Jarvis", "Server restarted")
    except Exception as exc:
        logger.exception("Server restart failed")
        _notify("Jarvis", f"Restart failed: {str(exc)[:120]}")


def _install_restart_signal_handler() -> None:
    global _restart_signal_thread

    def _handler(signum, frame):
        global _restart_signal_thread
        logger.info("Received restart signal (SIGUSR1)")
        if _restart_signal_thread and _restart_signal_thread.is_alive():
            logger.info("Restart signal ignored — restart already running")
            return
        _restart_signal_thread = threading.Thread(
            target=_restart_from_signal,
            name="jarvis-signal-restart",
            daemon=True,
        )
        _restart_signal_thread.start()

    signal.signal(signal.SIGUSR1, _handler)


def _server_responsive() -> bool:
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=2):
            return True
    except Exception:
        return False


def run_tray(uncensored: bool = False) -> None:
    global _watchdog, _services_watchdog
    from jarvis.audio_device import apply_system_default
    from jarvis.ha_docker import ensure_homeassistant_background
    from jarvis.services import (
        ServicesWatchdog,
        ensure_comfyui_background,
        pull_missing_models_background,
    )
    from jarvis.services import ensure_ollama as svc_ollama
    from jarvis.tray import run_tray_app
    from jarvis.watchdog import ServerWatchdog

    _setup_file_logging()
    load_jarvis_env()
    from jarvis.platform_attachment import attach_platform_infrastructure, validate_platform_startup
    from jarvis.platform_inference import attach_platform_inference, validate_platform_inference
    from jarvis.platform_memory import attach_platform_memory, validate_platform_memory

    attach_report = attach_platform_infrastructure()
    startup_issues = validate_platform_startup()
    if startup_issues:
        logger.warning("Platform startup validation: %s", "; ".join(startup_issues))
    elif attach_report.get("attached"):
        logger.info("AI Platform infrastructure attached for Aria")
    inference_report = attach_platform_inference()
    inference_issues = validate_platform_inference()
    if inference_issues:
        logger.warning("Platform inference validation: %s", "; ".join(inference_issues))
    elif inference_report.get("attached"):
        logger.info("AI Platform inference attached for Aria")
    memory_report = attach_platform_memory()
    memory_issues = validate_platform_memory()
    if memory_issues:
        logger.warning("Platform memory validation: %s", "; ".join(memory_issues))
    elif memory_report.get("attached"):
        logger.info("AI Platform memory adapter attached for Aria")
    _install_restart_signal_handler()
    if uncensored:
        os.environ["JARVIS_UNCENSORED"] = "1"

    url = CLIENT_URL

    try:
        apply_system_default()
        svc_ollama()
        ensure_homeassistant_background()
        if os.getenv("JARVIS_GRAPH_BACKEND", "sqlite").strip().lower() == "memgraph":
            try:
                from jarvis.memgraph_docker import ensure_memgraph_background

                ensure_memgraph_background()
            except Exception as exc:
                logger.warning("Memgraph autostart skipped: %s", exc)
        if _server_responsive():
            logger.info("API already listening on port %d — tray attaching (no duplicate server)", PORT)
            proc = None
        else:
            proc = start_server()

        if os.getenv("JARVIS_NO_BROWSER") != "1":
            _notify("Jarvis", f"Ready — {url}")
            _open_browser()

        if os.getenv("JARVIS_AUTO_PULL_MODELS", "1") != "0":
            pull_missing_models_background()
        from jarvis.services import warmup_chat_model_background
        warmup_chat_model_background()
        ensure_comfyui_background()

        _services_watchdog = ServicesWatchdog(interval=30)
        _services_watchdog.start()

        _watchdog = ServerWatchdog(
            health_url=PING_URL,
            interval=15,
            on_restart=lambda: restart_server(),
        )
        _watchdog.set_server_process(proc)
        _watchdog.start()

        from jarvis.server_restart import start_restart_watcher

        start_restart_watcher(restart_server)

        if os.getenv("JARVIS_WAKEWORD", "0") == "1":
            try:
                from jarvis.audio_wakeword import start_listener, wakeword_available

                if wakeword_available():
                    try:
                        from jarvis.assistant_instance import get_assistant
                        from jarvis.audio_wakeword import configure

                        configure(chat_processor=get_assistant().process)
                    except Exception:
                        pass
                    start_listener()
                    logger.info("Wake word listener started (JARVIS_WAKEWORD=1)")
                else:
                    logger.warning("JARVIS_WAKEWORD=1 but openwakeword not installed")
            except Exception as e:
                logger.warning("Wake word start failed: %s", e)

        def on_quit():
            try:
                from jarvis.proactive_scheduler import stop as stop_scheduler

                stop_scheduler()
            except Exception:
                pass
            try:
                from jarvis.audio_wakeword import stop_listener
                stop_listener()
            except Exception:
                pass
            _watchdog.stop()
            if _services_watchdog:
                _services_watchdog.stop()
            stop_server()

        from jarvis.config import is_uncensored
        from jarvis.proactive_scheduler import start as start_scheduler

        start_scheduler()

        try:
            run_tray_app(
                url=url,
                on_restart=lambda: restart_server(),
                on_quit=on_quit,
                uncensored=uncensored and is_uncensored(),
            )
        except Exception as exc:
            logger.warning("Tray unavailable (%s) — server keeps running without tray icon", exc)
            if proc and proc.poll() is None:
                proc.wait()
    except Exception as e:
        _notify("Jarvis failed", str(e)[:180])
        logger.exception("Jarvis tray startup failed")
        raise


def _open_browser() -> None:
    from jarvis.gui_launcher import open_gui

    if not open_gui(CLIENT_URL):
        logger.warning("Could not open GUI — open %s manually", CLIENT_URL)
