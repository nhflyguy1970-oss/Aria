"""Unified environment snapshot — time, profile, services, disk, resources."""

from __future__ import annotations

import os
import shutil
import time
from datetime import datetime
from typing import Any

from jarvis.config import DATA_DIR


def disk_free_gb(path: str | None = None) -> float:
    target = path or str(DATA_DIR)
    try:
        usage = shutil.disk_usage(target)
        return round(usage.free / (1024**3), 1)
    except OSError:
        return 0.0


def active_profile_name() -> str:
    try:
        from jarvis.profiles import active_profile

        return active_profile().get("name") or active_profile().get("id") or "default"
    except Exception:
        return os.getenv("JARVIS_PROFILE", "default")


def snapshot(*, include_resources: bool = True) -> dict[str, Any]:
    """Machine + Jarvis context for briefing, routing, and /api/environment."""
    from jarvis.services import get_status

    now = datetime.now()
    services = get_status(force=True)
    payload: dict[str, Any] = {
        "timestamp": now.isoformat(timespec="seconds"),
        "date": now.date().isoformat(),
        "time": now.strftime("%H:%M"),
        "profile": active_profile_name(),
        "disk_free_gb": disk_free_gb(),
        "data_dir": str(DATA_DIR),
        "services_ready": bool(services.get("ready")),
        "services": services.get("services") or [],
        "ollama_running": bool((services.get("ollama") or {}).get("running")),
    }
    if include_resources:
        try:
            from jarvis.resource_router import snapshot as resource_snapshot

            payload["resources"] = resource_snapshot()
        except Exception:
            payload["resources"] = {}
    try:
        from jarvis.gpu import detect_gpu, free_vram_mb

        gpu = detect_gpu()
        payload["gpu"] = {
            "name": gpu.get("name"),
            "vram_mb": gpu.get("vram_mb"),
            "free_vram_mb": free_vram_mb(),
            "low_vram": gpu.get("vram_mb", 0) and gpu.get("vram_mb", 0) <= 10240,
        }
    except Exception:
        payload["gpu"] = {}
    return payload


def briefing_line() -> str:
    """One-line environment hint for morning briefing."""
    snap = snapshot(include_resources=False)
    parts = [f"Profile: **{snap['profile']}**"]
    if snap.get("disk_free_gb"):
        parts.append(f"{snap['disk_free_gb']}GB free on data disk")
    gpu = snap.get("gpu") or {}
    if gpu.get("free_vram_mb"):
        parts.append(f"{gpu['free_vram_mb']}MB VRAM free")
    elif gpu.get("vram_mb"):
        parts.append(f"{gpu['vram_mb']}MB GPU")
    down = [
        s.get("label") or s.get("name")
        for s in snap.get("services") or []
        if s.get("required") and not s.get("running")
    ]
    if down:
        parts.append(f"offline: {', '.join(down[:3])}")
    return " · ".join(parts)
