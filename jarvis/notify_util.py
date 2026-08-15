"""Desktop notifications for ARIA."""

from __future__ import annotations

import subprocess


def notify_jarvis(
    title: str | None = None,
    body: str | None = None,
    *,
    icon: str | None = None,
    severity: str = "warning",
    source: str = "desktop",
    category: str = "system",
) -> bool:
    from jarvis.branding import assistant_name

    app = assistant_name()
    try:
        from jarvis.notifications_product.preferences import route_decision

        route = route_decision(
            {
                "title": title or "",
                "summary": body or "",
                "severity": severity,
                "source": source,
                "category": category,
            }
        )
        if not route.get("desktop"):
            return False
    except Exception:
        return False
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
        return True
    except Exception:
        return False
