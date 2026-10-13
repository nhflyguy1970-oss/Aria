"""System tray icon for Jarvis."""

import logging
import signal
import subprocess
import sys
import threading
from pathlib import Path

logger = logging.getLogger("jarvis.tray")

ICON_PATH = Path(__file__).resolve().parent.parent / "assets" / "jarvis-tray.png"
STATUS_POLL_S = 10
SYSTEM_DIST_PACKAGES = Path("/usr/lib/python3/dist-packages")


def _create_icon_image():
    from PIL import Image, ImageDraw

    if ICON_PATH.exists():
        return Image.open(ICON_PATH).convert("RGBA")

    img = Image.new("RGBA", (64, 64), (17, 20, 26, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse([8, 8, 56, 56], outline=(212, 160, 84, 255), width=3)
    draw.ellipse([24, 24, 40, 40], fill=(212, 160, 84, 255))
    img.save(ICON_PATH)
    return img


def enable_system_gi() -> bool:
    """Let the venv import the distro's PyGObject so pystray can use AppIndicator.

    Without ``gi`` pystray falls back to its Xorg backend, which GNOME/Zorin shows
    without a right-click menu. The system path is appended last, so every package
    the venv has still wins; it is only used when the interpreter versions match.
    """
    try:
        import gi  # noqa: F401

        return True
    except ImportError:
        pass
    site = SYSTEM_DIST_PACKAGES
    if sys.version_info[:2] != _system_python_version() or not (site / "gi").is_dir():
        return False
    sys.path.append(str(site))
    try:
        import gi  # noqa: F401,F811

        return True
    except ImportError:
        sys.path.remove(str(site))
        return False


def _system_python_version() -> tuple[int, int] | None:
    try:
        out = subprocess.run(["/usr/bin/python3", "-c", "import sys;print(*sys.version_info[:2])"],
                             capture_output=True, text=True, timeout=5, check=False).stdout.split()
        return int(out[0]), int(out[1])
    except Exception:  # noqa: BLE001
        return None


def run_tray_app(
    url: str,
    on_open=None,
    on_restart=None,
    on_quit=None,
    uncensored: bool = False,
    on_start=None,
    on_stop=None,
) -> None:
    if enable_system_gi():
        import os

        os.environ.setdefault("PYSTRAY_BACKEND", "appindicator")
    import pystray
    from pystray import MenuItem as Item

    from jarvis import tray_actions as actions
    from jarvis.branding import assistant_name

    name = assistant_name()
    title = f"{name} (Uncensored)" if uncensored else name
    state = {"snap": actions.Snapshot()}
    busy = threading.Lock()  # one menu action at a time

    def notify(message: str) -> None:
        try:
            icon.notify(message, title)
            return
        except Exception:  # noqa: BLE001 - backend without notifications
            pass
        try:
            subprocess.Popen(["notify-send", "-a", name, title, message])
        except Exception:  # noqa: BLE001
            logger.info("%s", message)

    def in_background(label: str, fn) -> None:
        def _do():
            if not busy.acquire(blocking=False):
                notify("Another tray action is still running")
                return
            try:
                ok, message = fn()
                notify(message)
                if not ok:
                    logger.warning("Tray %s: %s", label, message)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Tray %s failed", label)
                notify(f"{label} failed: {exc}"[:160])
            finally:
                busy.release()
                refresh()

        threading.Thread(target=_do, daemon=True, name=f"jarvis-tray-{label}").start()

    def open_gui(icon, item):
        from jarvis.gui_launcher import open_gui as launch_gui
        launch_gui(url)
        if on_open:
            on_open()

    def open_platform(icon, item):
        from jarvis.gui_launcher import open_gui as launch_gui

        launch_gui(f"{url}?app=1#workstation")

    def open_settings(icon, item):
        from jarvis.gui_launcher import open_gui as launch_gui

        launch_gui(actions.settings_url(url))

    def show_status(icon, item):
        def _do():
            state["snap"] = actions.snapshot(url)
            notify(state["snap"].detail())
            icon.update_menu()

        threading.Thread(target=_do, daemon=True, name="jarvis-tray-status").start()

    def start(icon, item):
        def _start():
            ok, message = actions.start_aria()
            if ok and on_start:
                on_start()
            return ok, message

        in_background("start", _start)

    def stop(icon, item):
        def _stop():
            if on_stop:
                on_stop()  # fence the watchdog first, or it would restart the server
            ok, message = actions.stop_aria()
            if not ok and on_start:
                on_start()
            return ok, message

        in_background("stop", _stop)

    def restart(icon, item):
        if on_restart:
            in_background("restart", lambda: actions.restart_aria(on_restart))

    def restart_backend(icon, item):
        in_background("backend restart", lambda: actions.restart_ai_backend(url))

    def open_logs_folder(icon, item):
        actions.open_path(actions.LOG_DIR)

    def open_server_log(icon, item):
        threading.Thread(target=lambda: actions.open_path(actions.server_log_snapshot()),
                         daemon=True, name="jarvis-tray-log").start()

    def open_tray_log(icon, item):
        actions.open_path(actions.LOG_DIR / "jarvis.log")

    quitting = threading.Event()

    def quit_app(icon, item=None, *, complete=True):
        if quitting.is_set():
            return
        quitting.set()

        def _shutdown():
            try:
                if on_quit:
                    on_quit(complete=complete)
                icon.stop()
            except Exception as exc:
                quitting.clear()
                logger.exception("ARIA quit cleanup failed; process retained")
                try:
                    icon.notify(f"Quit failed: {exc}"[:160], title)
                except NotImplementedError:
                    pass  # Xorg has no notification support; the failure is logged.

        threading.Thread(target=_shutdown, name="jarvis-quit", daemon=False).start()

    def quit_tray(icon, item=None):
        quit_app(icon, item, complete=False)

    def running(item) -> bool:
        return state["snap"].server

    menu = pystray.Menu(
        Item(f"Open {name}", open_gui, default=True),
        Item(lambda item: state["snap"].label, show_status),
        pystray.Menu.SEPARATOR,
        Item(f"Start {name}", start, enabled=lambda item: not state["snap"].server),
        Item(f"Stop {name}", stop, enabled=running),
        Item(f"Restart {name}", restart, enabled=running),
        Item("Restart AI Backend", restart_backend),
        pystray.Menu.SEPARATOR,
        Item("Logs", pystray.Menu(
            Item("Open logs folder", open_logs_folder),
            Item("Server log (recent)", open_server_log),
            Item("Tray log", open_tray_log),
        )),
        Item("Settings", open_settings, enabled=running),
        Item("AI Platform", open_platform, enabled=running),
        pystray.Menu.SEPARATOR,
        Item("Quit Tray", quit_tray),
        Item(f"Quit {name} Completely", quit_app),
    )

    icon = pystray.Icon(title, _create_icon_image(), title, menu)

    def refresh() -> None:
        snap = actions.snapshot(url)
        changed = (snap.label, snap.server) != (state["snap"].label, state["snap"].server)
        state["snap"] = snap
        if changed:
            try:
                icon.update_menu()
            except Exception:  # noqa: BLE001 - icon not running yet
                pass

    def poll() -> None:
        while not quitting.wait(STATUS_POLL_S):
            try:
                refresh()
            except Exception:  # noqa: BLE001
                logger.debug("Tray status poll failed", exc_info=True)

    state["snap"] = actions.snapshot(url)
    threading.Thread(target=poll, daemon=True, name="jarvis-tray-status-poll").start()
    logger.info("System tray active (backend: %s)", type(icon).__module__.rsplit(".", 1)[-1])
    try:
        icon.notify(f"{name} is running — {url}", title)
    except Exception:
        pass
    previous = {}
    for sig in (signal.SIGTERM, signal.SIGINT):
        previous[sig] = signal.signal(sig, lambda signum, frame: quit_app(icon, complete=False))
    try:
        icon.run()
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
