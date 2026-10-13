"""scripts/rotate-credentials.py: backs up, replaces, never prints a secret."""
from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OLD_KEY, OLD_SECRET = "old-lan-key-0123456789abcdef", "old-hook-secret-0123456789abcdef"


def _run(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    data = tmp_path / "data"
    env = {**os.environ, "JARVIS_DATA_DIR": str(data)}
    return subprocess.run([sys.executable, str(REPO / "scripts/rotate-credentials.py"),
                           "--env-file", str(data / "jarvis.env"), *args],
                          capture_output=True, text=True, env=env, timeout=120, cwd=tmp_path)


def _setup(tmp_path: Path) -> Path:
    data = tmp_path / "data"
    data.mkdir()
    env_file = data / "jarvis.env"
    env_file.write_text(f'export JARVIS_API_KEY="{OLD_KEY}"\nexport JARVIS_AUTOMATION_SECRET="{OLD_SECRET}"\n')
    return env_file


def test_rotation_replaces_backs_up_and_prints_no_secret(tmp_path):
    env_file = _setup(tmp_path)
    proc = _run(tmp_path, "--lan-api-key", "--automation-secret")
    assert proc.returncode == 0, proc.stderr[-800:]
    text = env_file.read_text()
    assert OLD_KEY not in text and OLD_SECRET not in text
    new_key = text.split("JARVIS_API_KEY=")[1].split("\n")[0].strip('"')
    new_secret = text.split("JARVIS_AUTOMATION_SECRET=")[1].split("\n")[0].strip('"')
    out = proc.stdout + proc.stderr
    for secret in (OLD_KEY, OLD_SECRET, new_key, new_secret):
        assert secret not in out
    backups = list((tmp_path / "data/backups").glob("jarvis.env.before-rotation-*"))
    assert len(backups) == 1 and OLD_KEY in backups[0].read_text()
    assert stat.S_IMODE(backups[0].stat().st_mode) == 0o600
    key_files = list((tmp_path / "data/security").glob("new-lan-api-key-*.txt"))
    assert key_files and key_files[0].read_text().strip() == new_key
    assert stat.S_IMODE(key_files[0].stat().st_mode) == 0o600
    assert stat.S_IMODE(env_file.stat().st_mode) == 0o600


def test_nothing_selected_changes_nothing(tmp_path):
    env_file = _setup(tmp_path)
    before = env_file.read_text()
    proc = _run(tmp_path)
    assert proc.returncode != 0
    assert env_file.read_text() == before
