"""Desktop notifications for ARIA."""

from __future__ import annotations

import subprocess


def notify_jarvis(title: str, body: str, *, icon: str | None = None) -> None:
    from jarvis.branding import assistant_name

    app = assistant_name()
    try:
        cmd = ["notify-send", "-a", app, title, body]
        if icon:
            cmd = ["notify-send", "-a", app, "-i", icon, title, body]
        subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except Exception:
        pass
