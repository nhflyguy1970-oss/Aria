"""Regression tests for desktop shortcut installation (RC blocker #desktop-path)."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESKTOP_DIR = ROOT / "desktop"
INSTALL_SCRIPT = ROOT / "scripts" / "install-desktop-shortcuts.sh"
LAUNCHER = ROOT / "scripts" / "desktop-launch-workstation.sh"

WORKSTATION_DESKTOPS = (
    "ai-workstation",
    "ai-workstation-start",
    "ai-workstation-stop",
    "ai-workstation-status",
    "ai-workstation-doctor",
    "ai-workstation-repair",
    "ai-workstation-acceptance",
)

# Bare command names in Exec fail under GNOME (PATH=/usr/bin:/bin only).
BARE_EXEC_RE = re.compile(
    r"^Exec=(?:workstation|aria)(?:\s|$)",
    re.MULTILINE,
)


def _read_desktop(name: str) -> str:
    return (DESKTOP_DIR / f"{name}.desktop").read_text(encoding="utf-8")


def _substitute_install(content: str, jarvis_root: str, home: str) -> str:
    return content.replace("@JARVIS_ROOT@", jarvis_root).replace("@HOME@", home)


def test_workstation_desktop_templates_use_absolute_exec():
    for name in WORKSTATION_DESKTOPS:
        text = _read_desktop(name)
        assert not BARE_EXEC_RE.search(text), f"{name}.desktop must not use bare workstation/aria"
        assert "@JARVIS_ROOT@/scripts/desktop-launch-workstation.sh" in text


def test_aria_desktop_uses_absolute_launch_script():
    text = _read_desktop("aria")
    assert not BARE_EXEC_RE.search(text)
    assert "Exec=@JARVIS_ROOT@/scripts/launch-jarvis.sh" in text


def test_installed_desktop_exec_survives_minimal_path(tmp_path):
    """Simulate install + GNOME desktop PATH (no ~/.local/bin)."""
    jarvis_root = str(ROOT)
    home = str(tmp_path)
    apps = tmp_path / ".local" / "share" / "applications"
    apps.mkdir(parents=True)

    for name in WORKSTATION_DESKTOPS:
        src = DESKTOP_DIR / f"{name}.desktop"
        installed = apps / f"{name}.desktop"
        installed.write_text(
            _substitute_install(src.read_text(encoding="utf-8"), jarvis_root, home),
            encoding="utf-8",
        )
        match = re.search(r"^Exec=(.+)$", installed.read_text(encoding="utf-8"), re.MULTILINE)
        assert match, f"missing Exec in {name}"
        exec_line = match.group(1).strip()
        # First token must be an absolute path (not a bare command name).
        cmd = exec_line.split()[0]
        assert cmd.startswith("/"), f"{name} Exec must use absolute path, got: {cmd}"

        env = {
            **os.environ,
            "PATH": "/usr/bin:/bin",
            "HOME": home,
        }
        # Dry-run: launcher exists and is executable; only validate start entry invokes script.
        if name in ("ai-workstation", "ai-workstation-start"):
            proc = subprocess.run(
                ["bash", "-n", cmd],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            assert proc.returncode == 0, proc.stderr


def test_desktop_launcher_script_exists_and_executable():
    assert LAUNCHER.is_file()
    assert os.access(LAUNCHER, os.X_OK)


def test_install_script_references_desktop_launcher():
    text = INSTALL_SCRIPT.read_text(encoding="utf-8")
    assert "desktop-launch-workstation.sh" in text
