"""System tray icon for Jarvis."""

import logging
import os
import threading
import time
from pathlib import Path

logger = logging.getLogger("jarvis.tray")

ICON_PATH = Path(__file__).resolve().parent.parent / "assets" / "jarvis-tray.png"


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


def run_tray_app(
    url: str,
    on_open=None,
    on_restart=None,
    on_quit=None,
    uncensored: bool = False,
) -> None:
    import pystray
    from pystray import MenuItem as Item
    from jarvis.branding import assistant_name

    title = f"{assistant_name()} (Uncensored)" if uncensored else assistant_name()

    def open_gui(icon, item):
        from jarvis.gui_launcher import open_gui as launch_gui
        launch_gui(url)
        if on_open:
            on_open()

    def restart(icon, item):
        if on_restart:
            def _do():
                try:
                    on_restart()
                    icon.notify(f"{assistant_name()} server restarted", title)
                except Exception as exc:
                    icon.notify(f"Restart failed: {exc}"[:120], title)

            threading.Thread(target=_do, daemon=True, name="jarvis-tray-restart").start()

    def quit_app(icon, item):
        icon.visible = False

        def _force_exit() -> None:
            time.sleep(8)
            os._exit(0)

        def _shutdown() -> None:
            try:
                if on_quit:
                    on_quit()
            except Exception:
                logger.exception("Jarvis quit cleanup failed")
            finally:
                os._exit(0)

        threading.Thread(target=_force_exit, name="jarvis-quit-timeout", daemon=True).start()
        threading.Thread(target=_shutdown, name="jarvis-quit", daemon=True).start()
        try:
            icon.stop()
        except Exception:
            os._exit(0)

    def status(icon, item):
        name = assistant_name()
        try:
            import urllib.request
            with urllib.request.urlopen(f"{url}/api/health", timeout=3):
                icon.notify(f"{name} is running", title)
        except Exception:
            icon.notify(f"{name} is offline", title)

    def open_workstation(icon, item):
        from jarvis.gui_launcher import open_gui as launch_gui

        launch_gui(f"{url}?app=1#workstation")

    def workstation_status(icon, item):
        try:
            import json
            import urllib.request

            with urllib.request.urlopen(f"{url}/api/workstation/dashboard", timeout=5) as resp:
                data = json.loads(resp.read().decode())
            mode = (data.get("runtime") or {}).get("mode", "?")
            acc = ((data.get("health") or {}).get("acceptance") or {}).get("overall", "?")
            icon.notify(f"Mode: {mode} · Acceptance: {acc}%", title)
        except Exception as exc:
            icon.notify(f"Dashboard unavailable: {exc}"[:120], title)

    menu = pystray.Menu(
        Item(f"Open {assistant_name()}", open_gui, default=True),
        Item("Workstation dashboard", open_workstation),
        Item("Workstation status", workstation_status),
        Item("Restart server", restart),
        Item("Check status", status),
        pystray.Menu.SEPARATOR,
        Item("Quit", quit_app),
    )

    icon = pystray.Icon(title, _create_icon_image(), title, menu)
    logger.info(
        "System tray active — on Linux/GNOME use left-click for menu; "
        "or use the Jarvis window sidebar / scripts/jarvis-ctl.sh"
    )
    try:
        icon.notify(f"{assistant_name()} is running — {url}", title)
    except Exception:
        pass
    icon.run()
