"""Safe remote actions from LAN automation webhooks."""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

from jarvis.config import DATA_DIR, PROJECT_ROOT

log = logging.getLogger("jarvis")

SCRIPTS_DIR = DATA_DIR / "scripts"


def run_whitelisted_script(name: str, *, timeout: int = 120) -> tuple[bool, str]:
    """Run an executable script from data/scripts/ only."""
    raw = (name or "").strip()
    if not raw:
        return False, "Script name required."
    base = Path(raw).name
    if base != raw or ".." in raw or "/" in raw or "\\" in raw:
        return False, "Use a simple script filename only (no paths)."
    script = (SCRIPTS_DIR / base).resolve()
    try:
        script.relative_to(SCRIPTS_DIR.resolve())
    except ValueError:
        return False, "Script must live in data/scripts/."
    if not script.is_file():
        return False, f"Not found: data/scripts/{base}"
    if not os.access(script, os.X_OK):
        return False, f"Not executable: data/scripts/{base} — chmod +x first."
    try:
        proc = subprocess.run(
            [str(script)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False, f"Script timed out after {timeout}s."
    out = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    if proc.returncode != 0:
        return False, out[:2000] or f"Exit code {proc.returncode}"
    return True, out[:2000] or "OK"


def wake_on_lan(mac: str | None = None) -> tuple[bool, str]:
    """Send magic packet if JARVIS_WOL_MAC or mac arg is set."""
    target = (mac or os.getenv("JARVIS_WOL_MAC") or "").strip()
    if not target:
        return False, "Set JARVIS_WOL_MAC or pass mac in webhook body."
    try:
        from wakeonlan import send_magic_packet

        send_magic_packet(target)
        return True, f"Wake-on-LAN sent to {target}."
    except ImportError:
        pass
    # Fallback: etherwake if installed
    wake = subprocess.run(["which", "etherwake"], capture_output=True, text=True)
    if wake.returncode == 0:
        proc = subprocess.run(["sudo", "etherwake", target], capture_output=True, text=True, timeout=10)
        if proc.returncode == 0:
            return True, f"etherwake sent to {target}."
        return False, (proc.stderr or proc.stdout or "etherwake failed")[:500]
    return False, "Install wakeonlan (`pip install wakeonlan`) or etherwake for WOL."
