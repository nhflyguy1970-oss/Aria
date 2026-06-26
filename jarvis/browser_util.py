"""Open URLs in a preferred browser (Chrome by default on Linux)."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

# Common install locations when not on PATH (.deb, Flatpak exports, distro packages).
CHROME_PATHS = (
    "/opt/google/chrome/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/google-chrome",
    "/var/lib/flatpak/exports/bin/com.google.Chrome",
    str(Path.home() / ".local/share/flatpak/exports/bin/com.google.Chrome"),
    "/usr/bin/chromium-browser",
    "/usr/bin/chromium",
    "/snap/bin/chromium",
)


def browser_candidates() -> list[str]:
    env = os.getenv("JARVIS_BROWSER", "google-chrome").strip()
    names: list[str] = []
    if env:
        names.append(env)
    names.extend([
        "google-chrome-stable",
        "google-chrome",
        "chromium-browser",
        "chromium",
        "chrome",
    ])
    seen: set[str] = set()
    out: list[str] = []
    for name in names:
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(name)
    return out


def _allow_xdg_fallback() -> bool:
    return os.getenv("JARVIS_BROWSER_ALLOW_XDG", "0").lower() in ("1", "true", "yes")


def resolve_browser() -> str | None:
    """Return executable path for the configured browser, or None."""
    path_env = os.getenv("JARVIS_BROWSER_PATH", "").strip()
    if path_env:
        p = Path(path_env).expanduser()
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)

    for name in browser_candidates():
        exe = shutil.which(name)
        if exe:
            return exe

    for candidate in CHROME_PATHS:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate

    if shutil.which("flatpak"):
        try:
            probe = subprocess.run(
                ["flatpak", "info", "com.google.Chrome"],
                capture_output=True,
                timeout=5,
            )
            if probe.returncode == 0:
                return "flatpak:com.google.Chrome"
        except (OSError, subprocess.TimeoutExpired):
            pass

    return None


def open_url(url: str, *, app_window: bool | None = None) -> bool:
    """Launch *url* in Chrome (or JARVIS_BROWSER). Avoids xdg-open unless explicitly allowed."""
    if app_window is None:
        app_window = os.getenv("JARVIS_APP_WINDOW", "0").lower() in ("1", "true", "yes")
    exe = resolve_browser()
    if exe:
        if app_window and "?" in url:
            launch_url = url if "app=1" in url else f"{url}{'&' if '?' in url else '?'}app=1"
        elif app_window:
            launch_url = f"{url}?app=1"
        else:
            launch_url = url
        cmd = (
            ["flatpak", "run", "com.google.Chrome", f"--app={launch_url}", "--class=Jarvis"]
            if exe == "flatpak:com.google.Chrome" and app_window
            else ["flatpak", "run", "com.google.Chrome", launch_url]
            if exe == "flatpak:com.google.Chrome"
            else [exe, f"--app={launch_url}", "--class=Jarvis"]
            if app_window
            else [exe, launch_url]
        )
        try:
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return True
        except OSError:
            pass

    if _allow_xdg_fallback():
        for cmd in (["xdg-open", url], ["gio", "open", url]):
            if shutil.which(cmd[0]):
                try:
                    subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True,
                    )
                    return True
                except OSError:
                    continue

    _notify_browser_missing(url)
    return False


def _notify_browser_missing(url: str) -> None:
    want = os.getenv("JARVIS_BROWSER", "google-chrome")
    msg = (
        f"Could not find {want}. Install Chrome: ./scripts/install-google-chrome.sh\n"
        f"Or set JARVIS_BROWSER_PATH in data/jarvis.env\nOpen manually: {url}"
    )
    try:
        subprocess.run(
            ["notify-send", "-a", "Jarvis", "Jarvis — browser not found", msg],
            check=False,
            timeout=3,
        )
    except Exception:
        pass


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python -m jarvis.browser_util <url>", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(0 if open_url(sys.argv[1]) else 1)
