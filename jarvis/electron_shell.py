"""Electron desktop shell for ARIA (P4 #88)."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

from jarvis.desktop_shell import (
    InstanceLock,
    PROJECT_ROOT,
    app_url,
    default_url,
    focus_existing_window,
    spawn_detached,
    wait_for_server,
    window_title,
)

logger = logging.getLogger("jarvis.electron_shell")

ELECTRON_DIR = PROJECT_ROOT / "scripts" / "electron-shell"
LOCK = InstanceLock("electron_shell")


def electron_dir() -> Path:
    return ELECTRON_DIR


def electron_binary() -> Path | None:
    candidates = [
        ELECTRON_DIR / "node_modules" / "electron" / "dist" / "electron",
        ELECTRON_DIR / "node_modules" / ".bin" / "electron",
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None


def is_installed() -> bool:
    return electron_binary() is not None


def is_available() -> bool:
    if not is_installed():
        return False
    return bool(shutil.which("node") or shutil.which("nodejs"))


def missing_dependency_hint() -> str:
    if not shutil.which("node") and not shutil.which("nodejs"):
        return (
            "Node.js is required for the Electron shell.\n"
            "Install Node 18+, then run: ./scripts/install-electron-shell.sh"
        )
    if not is_installed():
        return (
            "Electron shell is not installed.\n"
            "Run: ./scripts/install-electron-shell.sh"
        )
    return ""


def _shell_env(url: str) -> dict[str, str]:
    env = os.environ.copy()
    env["JARVIS_URL"] = app_url(url)
    env["JARVIS_WINDOW_TITLE"] = window_title()
    env["JARVIS_SHELL"] = "electron"
    return env


def launch_electron_shell(url: str) -> bool:
    """Spawn Electron shell detached (single instance)."""
    if not is_available():
        return False
    if LOCK.another_running():
        focus_existing_window()
        return True
    binary = electron_binary()
    if not binary:
        return False
    return spawn_detached([str(binary), str(ELECTRON_DIR)], env=_shell_env(url))


def run_electron_blocking(
    url: str,
    *,
    wait_for_ready: bool = True,
) -> int:
    if not is_available():
        sys.stderr.write(missing_dependency_hint() + "\n")
        return 1
    if not LOCK.acquire():
        focus_existing_window()
        return 0
    try:
        if wait_for_ready and not wait_for_server(url):
            sys.stderr.write(f"Server not ready at {url}\n")
            return 1
        binary = electron_binary()
        if not binary:
            sys.stderr.write(missing_dependency_hint() + "\n")
            return 1
        env = _shell_env(url)
        env["JARVIS_ELECTRON_QUIT_ON_CLOSE"] = "1"
        proc = subprocess.Popen([str(binary), str(ELECTRON_DIR)], env=env)
        code = proc.wait()
        return code if code is not None else 0
    finally:
        LOCK.release()


def install_shell() -> dict:
    if not shutil.which("npm"):
        return {"ok": False, "error": "npm not found — install Node.js 18+"}
    try:
        proc = subprocess.run(
            ["npm", "install"],
            cwd=str(ELECTRON_DIR),
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
        if proc.returncode != 0:
            return {
                "ok": False,
                "error": (proc.stderr or proc.stdout or "npm install failed")[:500],
            }
        return {"ok": True, "path": str(ELECTRON_DIR), "binary": str(electron_binary() or "")}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def status() -> dict:
    return {
        "available": is_available(),
        "installed": is_installed(),
        "path": str(ELECTRON_DIR),
        "binary": str(electron_binary() or ""),
        "running": LOCK.another_running(),
    }


def main(argv: list[str] | None = None) -> int:
    from jarvis.env_loader import load_jarvis_env

    load_jarvis_env()
    args = argv if argv is not None else sys.argv[1:]
    wait_for_ready = True
    if args and args[-1] == "--no-wait":
        wait_for_ready = False
        args = args[:-1]
    url = args[0] if args else default_url()
    return run_electron_blocking(url, wait_for_ready=wait_for_ready)


if __name__ == "__main__":
    raise SystemExit(main())
