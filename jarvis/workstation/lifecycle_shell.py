"""Shell script delegation for workstation lifecycle commands."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]


def _scripts_dir() -> Path:
    return _ROOT / "scripts"


def run_script(name: str, *args: str) -> int:
    script = _scripts_dir() / name
    if not script.is_file():
        print(f"Missing script: {script}", file=sys.stderr)
        return 1
    proc = subprocess.run(["bash", str(script), *args], cwd=str(_ROOT))
    return int(proc.returncode)


def install(*args: str) -> int:
    return run_script("install.sh", *args)


def configure() -> int:
    return run_script("workstation-configure.sh")


def start() -> int:
    return run_script("launch-jarvis.sh")


def stop() -> int:
    return run_script("stop-jarvis.sh")


def update() -> int:
    return run_script("workstation-update.sh")


def backup() -> int:
    return run_script("backup-workstation.sh")


def restore(archive: str) -> int:
    return run_script("restore-workstation.sh", archive)


def verify() -> int:
    return run_script("workstation-verify.sh")


def hardware() -> int:
    return run_script("workstation-hardware.sh")


def doctor() -> int:
    from jarvis.workstation import operations

    report = operations.diagnose(force=True)
    print(operations.format_report(force=True))
    code = 0 if report.get("ok") else 1
    py = _ROOT / "venv" / "bin" / "python"
    if not py.is_file():
        py = Path(sys.executable)
    try:
        import aiplatform  # noqa: F401
    except ImportError:
        print("\nAI-Platform: not installed (optional)")
        return code
    print("\n=== AI-Platform doctor ===")
    plat = subprocess.run([str(py), "-m", "aiplatform.cli", "doctor"], cwd=str(_ROOT))
    if plat.returncode != 0:
        code = 1
    return code
