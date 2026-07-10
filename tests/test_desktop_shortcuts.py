"""Regression tests for simplified desktop launcher installation."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESKTOP_DIR = ROOT / "desktop"
INSTALL_SCRIPT = ROOT / "scripts" / "install-desktop-shortcuts.sh"

CANONICAL_IDS = ("ai-platform", "aria", "aria-uncensored")

STALE_IDS = (
    "ai-workstation",
    "ai-workstation-start",
    "ai-workstation-stop",
    "ai-workstation-status",
    "ai-workstation-doctor",
    "ai-workstation-repair",
    "ai-workstation-acceptance",
    "aria-pyside",
    "aria-app",
    "aria-native",
    "jarvis",
    "jarvis-uncensored",
)

BARE_EXEC_RE = re.compile(
    r"^Exec=(?:workstation|aria)(?:\s|$)",
    re.MULTILINE,
)


def _read_desktop(name: str) -> str:
    return (DESKTOP_DIR / f"{name}.desktop").read_text(encoding="utf-8")


def _substitute_install(content: str, jarvis_root: str, home: str) -> str:
    return content.replace("@JARVIS_ROOT@", jarvis_root).replace("@HOME@", home)


def test_only_three_canonical_templates_exist():
    templates = sorted(p.stem for p in DESKTOP_DIR.glob("*.desktop"))
    assert templates == list(CANONICAL_IDS)


def test_canonical_desktop_templates_use_absolute_exec():
    expected_exec = {
        "ai-platform": "@JARVIS_ROOT@/scripts/desktop-launch-platform.sh",
        "aria": "@JARVIS_ROOT@/scripts/launch-jarvis.sh",
        "aria-uncensored": "@JARVIS_ROOT@/scripts/launch-jarvis-uncensored.sh",
    }
    for name, exec_line in expected_exec.items():
        text = _read_desktop(name)
        assert not BARE_EXEC_RE.search(text), f"{name} must not use bare command in Exec"
        assert f"Exec={exec_line}" in text


def test_install_script_lists_stale_ids_for_cleanup():
    text = INSTALL_SCRIPT.read_text(encoding="utf-8")
    for stale in STALE_IDS:
        assert stale in text, f"install script must remove stale launcher {stale}"


def test_install_script_installs_exactly_three(tmp_path, monkeypatch):
    """Simulate install into isolated XDG dirs — no duplicates."""
    home = tmp_path
    apps = home / ".local" / "share" / "applications"
    desktop = home / "Desktop"
    apps.mkdir(parents=True)
    desktop.mkdir()

    # Pre-seed stale launchers (regression: repair must remove these).
    for stale in STALE_IDS:
        (apps / f"{stale}.desktop").write_text("[Desktop Entry]\n", encoding="utf-8")
        (desktop / f"{stale}.desktop").write_text("[Desktop Entry]\n", encoding="utf-8")

    env = {
        **os.environ,
        "HOME": str(home),
        "XDG_DATA_HOME": str(home / ".local" / "share"),
        "XDG_DESKTOP_DIR": str(desktop),
    }
    proc = subprocess.run(
        ["bash", str(INSTALL_SCRIPT)],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout

    app_files = sorted(p.name for p in apps.glob("*.desktop"))
    desktop_files = sorted(p.name for p in desktop.glob("*.desktop"))
    expected = sorted(f"{i}.desktop" for i in CANONICAL_IDS)

    assert app_files == expected, f"app menu duplicates: {app_files}"
    assert desktop_files == expected, f"desktop duplicates: {desktop_files}"

    for stale in STALE_IDS:
        assert not (apps / f"{stale}.desktop").exists()
        assert not (desktop / f"{stale}.desktop").exists()


def test_installed_exec_survives_minimal_path(tmp_path):
    jarvis_root = str(ROOT)
    home = str(tmp_path)
    apps = tmp_path / ".local" / "share" / "applications"
    apps.mkdir(parents=True)

    for name in CANONICAL_IDS:
        src = DESKTOP_DIR / f"{name}.desktop"
        installed = apps / f"{name}.desktop"
        installed.write_text(
            _substitute_install(src.read_text(encoding="utf-8"), jarvis_root, home),
            encoding="utf-8",
        )
        match = re.search(r"^Exec=(.+)$", installed.read_text(encoding="utf-8"), re.MULTILINE)
        assert match, f"missing Exec in {name}"
        cmd = match.group(1).strip().split()[0]
        assert cmd.startswith("/"), f"{name} Exec must use absolute path, got: {cmd}"
        proc = subprocess.run(["bash", "-n", cmd], capture_output=True, text=True, check=False)
        assert proc.returncode == 0, proc.stderr


def test_platform_launcher_script_exists_and_executable():
    launcher = ROOT / "scripts" / "desktop-launch-platform.sh"
    assert launcher.is_file()
    assert os.access(launcher, os.X_OK)


def test_install_script_chmod_platform_launcher():
    text = INSTALL_SCRIPT.read_text(encoding="utf-8")
    assert "desktop-launch-platform.sh" in text
    assert "update-desktop-database" in text


def test_platform_launcher_opens_native_mission_control():
    text = (ROOT / "scripts" / "desktop-launch-platform.sh").read_text(encoding="utf-8")
    assert "workstation" in text and "start" in text
    assert "--console" in text
    assert "api/health" in text
    assert "aiplatform.mission_control.desktop" in text
    assert "desktop_window_visible" in text
    assert "gui_launcher" not in text
    assert "#workstation" not in text
    assert "xdg-open" not in text
