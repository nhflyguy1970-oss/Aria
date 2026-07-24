"""Desktop notifications for ARIA."""

from __future__ import annotations

import subprocess


def notify_jarvis(title: str | None = None, body: str | None = None, *, icon: str | None = None) -> None:
    from jarvis.branding import assistant_name

    app = assistant_name()
    try:
        cmd = ["notify-send", "-a", app, title or "", body or ""]
        if icon:
            cmd = ["notify-send", "-a", app, "-i", icon, title or "", body or ""]
        subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except Exception:
        return None
