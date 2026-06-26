"""Collect diagnostics for support and the debug-bundle UI."""

from __future__ import annotations

import os
import platform
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "data" / "logs"


def _tail(path: Path, max_bytes: int = 6000) -> str:
    if not path.is_file():
        return ""
    try:
        data = path.read_text(encoding="utf-8", errors="replace")
        return data[-max_bytes:]
    except OSError:
        return ""


def collect(*, log_bytes: int = 6000) -> dict[str, Any]:
    bundle: dict[str, Any] = {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
    }

    bundle["server_version"] = os.getenv("JARVIS_APP_VERSION", "3.1.0")
    bundle["ui_version"] = os.getenv("JARVIS_UI_VERSION", "5.15.0")

    try:
        from jarvis.metrics import snapshot

        bundle["metrics"] = snapshot()
    except Exception as exc:
        bundle["metrics"] = {"error": str(exc)}

    try:
        from jarvis.environment import snapshot as env_snapshot

        bundle["environment"] = env_snapshot(include_resources=True)
    except Exception as exc:
        bundle["environment"] = {"error": str(exc)}

    try:
        from jarvis.jobs_center import snapshot as jobs_snapshot

        bundle["jobs"] = jobs_snapshot(recent_limit=8)
    except Exception as exc:
        bundle["jobs"] = {"error": str(exc)}

    try:
        from jarvis.media_jobs import has_active_work_persisted

        bundle["media_work_persisted"] = has_active_work_persisted()
    except Exception:
        bundle["media_work_persisted"] = None

    bundle["logs"] = {
        "jarvis": _tail(LOG_DIR / "jarvis.log", log_bytes),
        "serve": _tail(LOG_DIR / "serve.log", log_bytes),
    }

    bundle["text"] = format_text(bundle)
    return bundle


def format_text(bundle: dict[str, Any]) -> str:
    lines = [
        "ARIA debug bundle",
        f"Generated: {bundle.get('generated_at')}",
        f"Server: v{bundle.get('server_version')} · Python {bundle.get('python')}",
        f"Platform: {bundle.get('platform')}",
        "",
    ]
    env = bundle.get("environment") or {}
    if isinstance(env, dict) and not env.get("error"):
        gpu = env.get("gpu") or {}
        lines.append(
            f"Profile: {env.get('profile')} · Disk free: {env.get('disk_free_gb')}GB · "
            f"VRAM free: {gpu.get('free_vram_mb', '?')}MB"
        )
    metrics = bundle.get("metrics") or {}
    if isinstance(metrics, dict):
        lines.append(
            f"Uptime: {metrics.get('uptime_sec', '?')}s · "
            f"Watchdog restarts: {metrics.get('watchdog_restarts', 0)}"
        )
    jobs = bundle.get("jobs") or {}
    if isinstance(jobs, dict) and jobs.get("any_busy"):
        lines.append("Background jobs: BUSY")
        for job in (jobs.get("recent") or [])[:5]:
            if not job.get("done"):
                lines.append(f"  · [{job.get('queue')}] {job.get('label')}: {job.get('message')}")
    lines.append("")
    for name, content in (bundle.get("logs") or {}).items():
        if content:
            lines.append(f"--- {name}.log (tail) ---")
            lines.append(content.rstrip())
            lines.append("")
    return "\n".join(lines).strip()
