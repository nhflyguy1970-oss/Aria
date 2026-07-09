"""Apply measured hardware recommendations to jarvis.env."""

from __future__ import annotations

import os
import re
from pathlib import Path

from jarvis.application.standalone.workstation_impl.hardware_report import collect_hardware
from jarvis.env_loader import PROJECT_ROOT

_ENV_FILE = PROJECT_ROOT / "data" / "jarvis.env"
_EXAMPLE = PROJECT_ROOT / "jarvis.env.example"


def _upsert_env(path: Path, key: str, value: str) -> None:
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    pattern = re.compile(rf"^export {re.escape(key)}=.*$", re.MULTILINE)
    line = f'export {key}="{value}"'
    if pattern.search(text):
        text = pattern.sub(line, text)
    else:
        if text and not text.endswith("\n"):
            text += "\n"
        text += line + "\n"
    path.write_text(text, encoding="utf-8")


def apply_optimization(*, dry_run: bool = False) -> dict:
    """Configure workload placement from hardware measurements."""
    report = collect_hardware(benchmark=True)
    rec = report.get("recommended_placement") or {}
    changes: dict[str, str] = {}

    llm = str(rec.get("llm_inference") or "cpu")
    if llm == "nvidia":
        changes["JARVIS_GPU_PREFER"] = "nvidia"
    elif llm == "rocm":
        changes["JARVIS_GPU_PREFER"] = "amd"

    image = str(rec.get("image_generation") or "cpu")
    if image == "amd":
        changes["JARVIS_COMFYUI_DEVICE"] = "rocm"
    elif image == "nvidia":
        changes["JARVIS_COMFYUI_DEVICE"] = "cuda"

    ram = float(report.get("ram_gb") or 0)
    if ram and ram < 20:
        changes["JARVIS_VRAM_GUARD"] = "1"
        changes["JARVIS_WHISPER_MODEL"] = "small"

    if dry_run:
        return {"ok": True, "dry_run": True, "changes": changes, "report": report}

    _ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not _ENV_FILE.is_file() and _EXAMPLE.is_file():
        _ENV_FILE.write_text(_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")

    for key, value in changes.items():
        _upsert_env(_ENV_FILE, key, value)
        os.environ[key] = value

    try:
        from jarvis.env_loader import load_jarvis_env

        load_jarvis_env(force=True)
    except Exception:
        pass

    return {
        "ok": True,
        "changes": changes,
        "env_file": str(_ENV_FILE),
        "bottlenecks": report.get("bottlenecks") or [],
    }
