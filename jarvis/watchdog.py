import logging
import socket
import subprocess
import threading
import urllib.request

logger = logging.getLogger("jarvis.watchdog")


def _media_work_active() -> bool:
    """True while a GPU image/video job is running or queued."""
    try:
        from jarvis.media_jobs import busy_state, has_active_work, has_active_work_persisted
        from jarvis.restart_flag import controlled_restart_active
        from jarvis.request_activity import active as chat_active

        if controlled_restart_active():
            return True
        if chat_active():
            return True
        try:
            from jarvis.coding_jobs import has_active_work as coding_active

            if coding_active():
                return True
        except Exception:
            pass
        if has_active_work_persisted():
            return True
        if has_active_work():
            return True
        st = busy_state()
        return bool(st.get("busy") or st.get("pending"))
    except Exception as exc:
        logger.debug("Media work check failed: %s", exc)
        return False


class ServerWatchdog:
    """Monitor Jarvis health and restart the server process if it dies."""

    def __init__(
        self,
        health_url: str = "http://127.0.0.1:8765/api/ping",
        interval: int = 15,
        on_restart=None,
        failures_before_restart: int = 3,
        timeout: float = 8,
    ):
        self.health_url = health_url
        self.interval = interval
        self.on_restart = on_restart
        self.failures_before_restart = max(1, failures_before_restart)
        self.timeout = timeout
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._server_proc: subprocess.Popen | None = None
        self._restart_count = 0
        self._consecutive_failures = 0

    def set_server_process(self, proc: subprocess.Popen | None) -> None:
        self._server_proc = proc
        self._consecutive_failures = 0

    def _healthy(self) -> bool:
        try:
            with urllib.request.urlopen(self.health_url, timeout=self.timeout) as resp:
                return resp.status == 200
        except Exception as exc:
            logger.debug("Health check failed: %s", exc)
            return False

    def _port_open(self) -> bool:
        try:
            from urllib.parse import urlparse

            parsed = urlparse(self.health_url)
            host = parsed.hostname or "127.0.0.1"
            port = parsed.port or 8765
            with socket.create_connection((host, port), timeout=self.timeout):
                return True
        except OSError:
            return False

    def _restart_server(self) -> None:
        self._restart_count += 1
        fail_count = self._consecutive_failures
        self._consecutive_failures = 0
        try:
            from jarvis.restart_audit import log_restart_event

            log_restart_event(
                "watchdog",
                detail=f"unhealthy restart #{self._restart_count}",
                failures=fail_count,
            )
        except Exception as exc:
            logger.debug("Could not write restart audit: %s", exc)
        try:
            from jarvis.metrics import note_watchdog_restart

            note_watchdog_restart()
        except Exception as exc:
            logger.debug("Could not record watchdog restart metric: %s", exc)
        logger.warning("Jarvis unhealthy — restart #%d", self._restart_count)
        if self._server_proc and self._server_proc.poll() is not None:
            self._server_proc = None
        if self.on_restart:
            self._server_proc = self.on_restart()
        else:
            logger.error("No restart callback configured")

    def _loop(self) -> None:
        while not self._stop.wait(self.interval):
            if self._server_proc and self._server_proc.poll() is not None:
                code = self._server_proc.returncode
                try:
                    from jarvis.restart_flag import controlled_restart_active

                    if controlled_restart_active() or _media_work_active():
                        logger.info(
                            "Server process exited (code %s) during restart/media — not escalating",
                            code,
                        )
                        self._consecutive_failures = 0
                        continue
                except Exception as exc:
                    logger.debug("Restart/media gate check failed: %s", exc)
                logger.warning("Server process exited (code %s)", code)
                self._restart_server()
                continue
            if self._healthy():
                self._consecutive_failures = 0
                continue
            if _media_work_active():
                if self._consecutive_failures:
                    logger.info("Health check slow during media job — not restarting server")
                self._consecutive_failures = 0
                continue
            self._consecutive_failures += 1
            threshold = self.failures_before_restart
            if self._consecutive_failures < threshold:
                logger.info(
                    "Health check failed (%d/%d) — server may be busy",
                    self._consecutive_failures,
                    threshold,
                )
                continue
            if not self._port_open():
                if _media_work_active():
                    logger.info("Port closed during media job — waiting before restart")
                    self._consecutive_failures = 0
                    continue
                self._restart_server()
            else:
                if _media_work_active():
                    logger.info("Wedged probe during media job — not restarting server")
                    self._consecutive_failures = 0
                    continue
                logger.warning(
                    "Liveness probe failed %d times with port open — restarting wedged server",
                    self._consecutive_failures,
                )
                self._restart_server()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="jarvis-watchdog")
        self._thread.start()
        logger.info("Watchdog started (interval=%ds)", self.interval)

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)
