"""Shared helpers for optional desktop shells (Electron, PySide6, native)."""

from __future__ import annotations

import fcntl
import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger("jarvis.desktop_shell")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ICON_PATH = PROJECT_ROOT / "assets" / "jarvis-tray.png"
DEFAULT_WIDTH = int(os.getenv("JARVIS_NATIVE_WIDTH", "1280"))
DEFAULT_HEIGHT = int(os.getenv("JARVIS_NATIVE_HEIGHT", "860"))


def app_url(url: str, *, shell: str | None = None) -> str:
    out = url
    if "app=1" not in out:
        out = f"{out}{'&' if '?' in out else '?'}app=1"
    if shell and f"shell={shell}" not in out:
        out = f"{out}&shell={shell}"
    return out


def window_title() -> str:
    from jarvis.branding import assistant_window_title
    from jarvis.config import is_uncensored

    return assistant_window_title(uncensored=is_uncensored())


def default_url() -> str:
    host = os.getenv("JARVIS_HOST", "127.0.0.1")
    if host in ("0.0.0.0", "::"):
        host = "127.0.0.1"
    port = os.getenv("JARVIS_PORT", "8765")
    return f"http://{host}:{port}"


def wait_for_server(url: str, timeout_sec: float = 60.0) -> bool:
    from jarvis.native_window import wait_for_server as _wait

    return _wait(url, timeout_sec=timeout_sec)


def focus_existing_window(title: str | None = None) -> bool:
    from jarvis.native_window import _focus_existing_window

    return _focus_existing_window(title or window_title())


def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


class InstanceLock:
    """Exclusive flock for one shell window per name."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.lock_file = PROJECT_ROOT / "data" / f"{name}.lock"
        self.pid_file = PROJECT_ROOT / "data" / f"{name}.pid"
        self._handle = None

    def acquire(self) -> bool:
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        self._handle = open(self.lock_file, "a+", encoding="utf-8")
        try:
            fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            try:
                self._handle.close()
            except OSError:
                pass
            self._handle = None
            return False
        self._handle.seek(0)
        self._handle.truncate()
        self._handle.write(str(os.getpid()))
        self._handle.flush()
        self.pid_file.write_text(str(os.getpid()), encoding="utf-8")
        return True

    def release(self) -> None:
        if self._handle is not None:
            try:
                fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
                self._handle.close()
            except OSError:
                pass
            self._handle = None
        try:
            self.pid_file.unlink(missing_ok=True)
        except OSError:
            pass

    def another_running(self) -> bool:
        if not self.lock_file.is_file():
            return False
        try:
            with open(self.lock_file, encoding="utf-8") as fh:
                pid = int(fh.read().strip() or "0")
            return bool(pid and pid_alive(pid) and pid != os.getpid())
        except (OSError, ValueError):
            return False


GUI_SHELL_LOCK = InstanceLock("gui_shell")
_ACTIVE_SHELL_FILE = PROJECT_ROOT / "data" / "gui_shell_active.txt"


def acquire_gui_shell_lock(shell_name: str) -> bool:
    if not GUI_SHELL_LOCK.acquire():
        return False
    try:
        _ACTIVE_SHELL_FILE.write_text(shell_name, encoding="utf-8")
    except OSError:
        pass
    return True


def release_gui_shell_lock() -> None:
    GUI_SHELL_LOCK.release()
    try:
        _ACTIVE_SHELL_FILE.unlink(missing_ok=True)
    except OSError:
        pass


def gui_shell_running() -> bool:
    return GUI_SHELL_LOCK.another_running()


def spawn_detached(cmd: list[str], *, env: dict[str, str] | None = None, extra_env: dict[str, str] | None = None) -> bool:
    try:
        proc_env = dict(os.environ)
        if env:
            proc_env.update(env)
        if extra_env:
            proc_env.update(extra_env)
        subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            env=proc_env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True,
        )
        return True
    except OSError as exc:
        logger.warning("Detached launch failed: %s", exc)
        return False


def python_exe() -> str:
    return sys.executable
