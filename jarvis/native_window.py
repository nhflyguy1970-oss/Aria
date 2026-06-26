"""Native desktop window for Jarvis via pywebview (WebKitGTK on Linux)."""

from __future__ import annotations

import fcntl
import logging
import os
import signal
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

logger = logging.getLogger("jarvis.native_window")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ICON_PATH = PROJECT_ROOT / "assets" / "jarvis-tray.png"
DEFAULT_WIDTH = int(os.getenv("JARVIS_NATIVE_WIDTH", "1280"))
DEFAULT_HEIGHT = int(os.getenv("JARVIS_NATIVE_HEIGHT", "860"))


def _app_url(url: str) -> str:
    if "app=1" in url:
        return url
    join = "&" if "?" in url else "?"
    return f"{url}{join}app=1"


def _window_title() -> str:
    from jarvis.branding import assistant_window_title
    from jarvis.config import is_uncensored

    return assistant_window_title(uncensored=is_uncensored())


def _can_use_gtk() -> bool:
    try:
        import gi  # noqa: F401
        gi.require_version("Gtk", "3.0")
        gi.require_version("WebKit2", "4.1")
        from gi.repository import Gtk, WebKit2  # noqa: F401
        import webview.platforms.gtk  # noqa: F401
        return True
    except Exception:
        return False


def _can_use_qt() -> bool:
    try:
        import qtpy  # noqa: F401
        import webview.platforms.qt  # noqa: F401
        return True
    except Exception:
        return False


def _select_backend() -> str | None:
    forced = os.getenv("PYWEBVIEW_GUI", "").strip().lower()
    if forced in ("gtk", "qt"):
        return forced if (forced == "gtk" and _can_use_gtk()) or (forced == "qt" and _can_use_qt()) else None
    prefer_qt = os.getenv("JARVIS_PREFER_QT_WEBVIEW", "1").lower() in ("1", "true", "yes", "on")
    if prefer_qt and _can_use_qt():
        return "qt"
    if _can_use_gtk():
        return "gtk"
    if _can_use_qt():
        return "qt"
    return None


def is_available() -> bool:
    """True if pywebview can load a GTK or Qt backend."""
    try:
        import webview  # noqa: F401
    except ImportError:
        return False
    return _select_backend() is not None


def missing_dependency_hint() -> str:
    if not is_available():
        try:
            import webview  # noqa: F401
        except ImportError:
            return (
                "pywebview is not installed.\n"
                "Run: ./scripts/install-native-window.sh"
            )
        return (
            "No pywebview GUI backend found.\n"
            "Run: ./scripts/install-native-window.sh\n"
            "(installs Qt WebEngine via pip, or GTK via apt if you prefer)"
        )
    return ""


def _ensure_backend() -> str:
    backend = _select_backend()
    if not backend:
        raise RuntimeError(missing_dependency_hint() or "No pywebview backend")
    os.environ["PYWEBVIEW_GUI"] = backend
    return backend


def wait_for_server(url: str, timeout_sec: float = 60.0) -> bool:
    live = url.rstrip("/") + "/api/live"
    health = url.rstrip("/") + "/api/health"
    import time

    deadline = time.time() + timeout_sec
    notified_wait = False
    notified_recover = False
    while time.time() < deadline:
        for endpoint in (live, health):
            try:
                with urllib.request.urlopen(endpoint, timeout=2):
                    if notified_wait and not notified_recover:
                        from jarvis.branding import assistant_name
                        _notify_tray(f"{assistant_name()} ready", "Server is responding — opening window.")
                        notified_recover = True
                    return True
            except (urllib.error.URLError, TimeoutError, OSError):
                continue
        if not notified_wait and time.time() > deadline - timeout_sec + 8:
            from jarvis.branding import assistant_name
            name = assistant_name()
            _notify_tray(name, "Waiting for server to start…")
            notified_wait = True
        time.sleep(0.4)
    if notified_wait:
        from jarvis.branding import assistant_name
        _notify_tray(assistant_name(), "Server did not respond in time — try the shortcut again.")
    return False


def _notify_tray(title: str, body: str) -> None:
    try:
        from jarvis.branding import assistant_name
        subprocess.run(
            ["notify-send", "-a", assistant_name(), title, body],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except Exception:
        pass


def run_window_blocking(
    url: str,
    *,
    title: str | None = None,
    width: int | None = None,
    height: int | None = None,
    wait_for_ready: bool = True,
) -> int:
    """Open a blocking native window. Returns 0 on clean exit, 1 on failure."""
    if not is_available():
        sys.stderr.write(missing_dependency_hint() + "\n")
        return 1

    import webview

    launch_url = _app_url(url)
    if wait_for_ready and not wait_for_server(url):
        from jarvis.branding import assistant_name
        sys.stderr.write(f"{assistant_name()} server not ready at {url}\n")
        return 1

    for key, val in (
        ("WEBKIT_DISABLE_COMPOSITING_MODE", "1"),
        ("WEBKIT_DISABLE_DMABUF_RENDERER", "1"),
    ):
        os.environ.setdefault(key, val)
    flags = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
    if "disable-gpu-compositing" not in flags:
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = f"{flags} --disable-gpu-compositing".strip()

    kwargs: dict = {
        "width": width or DEFAULT_WIDTH,
        "height": height or DEFAULT_HEIGHT,
        "min_size": (720, 480),
        "resizable": True,
        "background_color": "#0a0c10",
        "text_select": True,
    }
    backend = _ensure_backend()
    icon = str(ICON_PATH) if ICON_PATH.is_file() else None
    if icon and backend == "gtk":
        kwargs["icon"] = icon

    window = webview.create_window(title or _window_title(), launch_url, **kwargs)

    def on_closed():
        logger.info("Native window closed")
        _clear_pid()
        _release_instance_lock()

    if not _acquire_instance_lock():
        logger.info("Native window already open — focusing existing window")
        _focus_existing_window(_window_title())
        return 0

    _terminate_duplicate_windows()
    _write_pid()

    try:
        window.events.closed += on_closed
    except Exception:
        pass

    webview.start(debug=os.getenv("JARVIS_NATIVE_DEBUG", "0") in ("1", "true", "yes"))
    return 0


PID_FILE = PROJECT_ROOT / "data" / "native_window.pid"
LOCK_FILE = PROJECT_ROOT / "data" / "native_window.lock"
_lock_handle = None


def _terminate_duplicate_windows() -> None:
    """Remove stale PID file entries only; flock prevents duplicate live instances."""
    if not PID_FILE.is_file():
        return
    try:
        old_pid = int(PID_FILE.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return
    if old_pid != os.getpid() and not _pid_alive(old_pid):
        try:
            PID_FILE.unlink(missing_ok=True)
        except OSError:
            pass


def _acquire_instance_lock() -> bool:
    """Exclusive lock — one native window per machine."""
    global _lock_handle
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    _lock_handle = open(LOCK_FILE, "a+", encoding="utf-8")
    try:
        fcntl.flock(_lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        try:
            _lock_handle.close()
        except OSError:
            pass
        _lock_handle = None
        return False
    _lock_handle.seek(0)
    _lock_handle.truncate()
    _lock_handle.write(str(os.getpid()))
    _lock_handle.flush()
    return True


def _release_instance_lock() -> None:
    global _lock_handle
    if _lock_handle is not None:
        try:
            fcntl.flock(_lock_handle.fileno(), fcntl.LOCK_UN)
            _lock_handle.close()
        except OSError:
            pass
        _lock_handle = None


def _focus_existing_window(title: str | None = None) -> bool:
    if title is None:
        from jarvis.branding import assistant_name
        title = assistant_name()
    import shutil

    needle = title.casefold()
    if shutil.which("wmctrl"):
        try:
            listed = subprocess.run(
                ["wmctrl", "-l"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            if any(needle in line.casefold() for line in (listed.stdout or "").splitlines()):
                subprocess.run(
                    ["wmctrl", "-a", title],
                    timeout=2,
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True
        except Exception:
            pass
    if shutil.which("xdotool"):
        try:
            found = subprocess.run(
                ["xdotool", "search", "--name", title],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            wid = (found.stdout or "").strip().splitlines()
            if wid:
                subprocess.run(
                    ["xdotool", "windowactivate", "--sync", wid[0]],
                    timeout=2,
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True
        except Exception:
            pass
    return False


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _write_pid() -> None:
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")


def _clear_pid() -> None:
    try:
        PID_FILE.unlink(missing_ok=True)
    except OSError:
        pass


def _existing_window_running() -> bool:
    if not PID_FILE.is_file():
        return False
    try:
        pid = int(PID_FILE.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return False
    if not _pid_alive(pid):
        _clear_pid()
        return False
    return True


def launch_native_window(url: str) -> bool:
    """Spawn or focus a single native window process."""
    if not is_available():
        return False
    if _existing_window_running():
        _focus_existing_window(_window_title())
        return True
    if LOCK_FILE.is_file():
        try:
            with open(LOCK_FILE, encoding="utf-8") as fh:
                pid = int(fh.read().strip() or "0")
            if pid and _pid_alive(pid):
                _focus_existing_window(_window_title())
                return True
        except (OSError, ValueError):
            pass
    cmd = [sys.executable, "-m", "jarvis.native_window", url, "--no-wait"]
    try:
        subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return True
    except OSError as exc:
        logger.warning("Native window launch failed: %s", exc)
        return False


def main(argv: list[str] | None = None) -> int:
    from jarvis.env_loader import load_jarvis_env

    load_jarvis_env()
    args = argv if argv is not None else sys.argv[1:]
    wait_for_ready = True
    if args and args[-1] == "--no-wait":
        wait_for_ready = False
        args = args[:-1]

    host = os.getenv("JARVIS_HOST", "127.0.0.1")
    port = os.getenv("JARVIS_PORT", "8765")
    url = args[0] if args else f"http://{host}:{port}"
    return run_window_blocking(url, wait_for_ready=wait_for_ready)


if __name__ == "__main__":
    raise SystemExit(main())
