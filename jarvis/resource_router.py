"""Resource-aware routing — VRAM/RAM, queues, and safe defaults before heavy work."""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.request
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.gpu import detect_gpu, is_low_vram
from jarvis.ml_memory import system_ram_gb, unload_ollama_models

log = logging.getLogger("jarvis")

_SETTINGS_FILE = DATA_DIR / "resource_settings.json"
_HEAVY_ACTIONS = frozenset(
    {
        "generate_image",
        "generate_video",
        "generate_meme",
        "upscale_image",
        "inpaint_image",
        "edit_image",
    }
)
_VRAM_ACTIONS = _HEAVY_ACTIONS


def routing_enabled() -> bool:
    return os.getenv("JARVIS_RESOURCE_ROUTING", "1").lower() not in ("0", "false", "no", "off")


def strict_queue() -> bool:
    return os.getenv("JARVIS_RESOURCE_STRICT", "0").lower() in ("1", "true", "yes")


def max_media_queue() -> int:
    try:
        return max(1, int(os.getenv("JARVIS_MEDIA_MAX_QUEUE", "6")))
    except ValueError:
        return 6


def _load_settings() -> dict:
    if _SETTINGS_FILE.exists():
        try:
            return json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"last_success": {}}


def _save_settings(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    _SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def record_media_outcome(action: str, *, ok: bool, method: str = "", detail: str = "") -> None:
    if not ok or action not in _HEAVY_ACTIONS:
        return
    data = _load_settings()
    entry = {
        "at": time.time(),
        "method": method,
        "detail": detail[:200],
        "vram_mb": detect_gpu().get("vram_mb"),
        "low_vram": is_low_vram(10240),
    }
    data.setdefault("last_success", {})[action] = entry
    _save_settings(data)


def suggested_for_action(action: str) -> dict[str, Any]:
    return dict(_load_settings().get("last_success", {}).get(action) or {})


def ollama_loaded_models() -> list[dict[str, Any]]:
    host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    try:
        with urllib.request.urlopen(f"{host}/api/ps", timeout=2) as resp:
            data = json.loads(resp.read().decode())
        return list(data.get("models") or [])
    except Exception:
        return []


def ram_available_gb() -> float:
    try:
        mem_total = mem_avail = 0
        with open("/proc/meminfo", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    mem_total = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    mem_avail = int(line.split()[1])
        if mem_avail:
            return round(mem_avail / (1024 * 1024), 1)
        return round(mem_total / (1024 * 1024), 1) if mem_total else 0.0
    except OSError:
        return 0.0


def snapshot() -> dict[str, Any]:
    from jarvis.coding_jobs import job_stats as coding_stats
    from jarvis.media_jobs import busy_state
    from jarvis.media_jobs import job_stats as media_stats
    from jarvis.vram_guard import status as vram_status

    gpu = detect_gpu()
    vram = vram_status()
    media = busy_state()
    coding = coding_stats()
    loaded = ollama_loaded_models()
    low = bool(vram.get("low_vram"))
    from jarvis.gpu import free_vram_mb

    return {
        "routing_enabled": routing_enabled(),
        "low_vram": low,
        "vram_mb": gpu.get("vram_mb"),
        "free_vram_mb": free_vram_mb(),
        "ram_total_gb": round(system_ram_gb(), 1),
        "ram_available_gb": ram_available_gb(),
        "ollama_using_gpu": gpu.get("ollama_using_gpu"),
        "ollama_models_loaded": len(loaded),
        "ollama_models": [m.get("name") or m.get("model") for m in loaded[:6]],
        "media_queue": media,
        "media_stats": media_stats(),
        "coding_queue": coding,
        "vram_guard": vram,
        "recommendations": vram.get("recommendations") or [],
    }


def _queue_warnings(media: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    pending = int(media.get("pending") or 0)
    if media.get("busy"):
        label = media.get("label") or "media job"
        warnings.append(f"GPU media job running: **{label}**. New jobs queue behind it.")
    if pending > 0:
        warnings.append(f"{pending} media job(s) already queued — yours will wait in line.")
    if pending + (1 if media.get("busy") else 0) >= max_media_queue() - 1:
        warnings.append(
            f"Media queue is nearly full (max {max_media_queue()}). "
            "Cancel stale jobs or wait before starting more renders."
        )
    return warnings


def preflight(action: str = "video") -> dict[str, Any]:
    """Preflight check for GUI and chat before heavy GPU work."""
    from jarvis.vram_guard import recommendations

    action = (action or "video").strip().lower()
    snap = snapshot()
    media = snap["media_queue"]
    warnings = _queue_warnings(media)
    tips = recommendations()[:5]
    adjustments: list[str] = []
    suggested: dict[str, Any] = {}
    is_video = action in ("video", "generate_video")
    is_image = action in ("generate_image", "image")

    if snap["low_vram"]:
        if action in _VRAM_ACTIONS or is_video:
            gpu_name = (snap.get("vram_guard") or {}).get("gpu_name") or ""
            label = "8GB-class GPU"
            if gpu_name:
                label = gpu_name
            elif (snap.get("vram_mb") or 0) > 10240:
                label = f"{round((snap['vram_mb'] or 0) / 1024)}GB GPU"
            warnings.append(
                f"{label} detected — Jarvis will unload Ollama before ComfyUI when the job runs."
            )
        if is_video:
            from jarvis.video_settings import (
                effective_animatediff_frames,
                effective_animatediff_size,
                effective_engine,
            )

            eng = effective_engine()
            ad_w, ad_h = effective_animatediff_size()
            frames = effective_animatediff_frames(4.0, 8)
            if eng in ("auto", "animatediff"):
                adjustments.append("AnimateDiff may fall back to Ken Burns if VRAM is tight.")
                if snap["low_vram"]:
                    tips.insert(0, "Ken Burns uses less VRAM than AnimateDiff on 8GB GPUs.")
                else:
                    tips.insert(
                        0, "AnimateDiff uses your NVIDIA GPU; Ken Burns is the CPU fallback."
                    )
            suggested = {
                "engine": eng,
                "width": ad_w,
                "height": ad_h,
                "frames": min(frames, 16),
                "low_vram_max_frames": 8,
            }
        if is_image:
            adjustments.append("Prefer SDXL Turbo or 768² — Flux uses more VRAM on 8GB.")
        if snap["ollama_models_loaded"] > 0:
            warnings.append(
                f"Ollama has {snap['ollama_models_loaded']} model(s) loaded — "
                "use **Free VRAM** or let Jarvis unload them when the job starts."
            )

    if snap["ram_available_gb"] and snap["ram_available_gb"] < 4:
        warnings.append(
            f"Low system RAM available ({snap['ram_available_gb']}GB) — close heavy apps if renders fail."
        )

    last = suggested_for_action(action if action in _HEAVY_ACTIONS else "generate_video")
    if last.get("method"):
        tips.insert(0, f"Last successful {action}: {last['method']} on this machine.")

    blocked = False
    queue_depth = int(media.get("queue_depth") or 0)
    if strict_queue() and queue_depth >= max_media_queue():
        blocked = True
        warnings.append("Queue full — cancel a job or wait (JARVIS_RESOURCE_STRICT=1).")

    return {
        "ok": not blocked and len(warnings) == 0,
        "allow": not blocked,
        "blocked": blocked,
        "action": action,
        "warnings": warnings,
        "adjustments": adjustments,
        "tips": tips,
        "suggested": suggested,
        "resources": snap,
    }


def check_media_enqueue(action: str) -> dict[str, Any]:
    """Gate media job enqueue; returns advisory text and optional block."""
    pf = preflight(action)
    media = pf["resources"]["media_queue"]
    pending = int(media.get("pending") or 0)
    position = pending + (1 if media.get("busy") else 0) + 1
    parts: list[str] = []
    if pf["adjustments"]:
        parts.append(" ".join(pf["adjustments"][:2]))
    if routing_enabled() and action in _VRAM_ACTIONS and pf["resources"]["low_vram"]:
        parts.append("Ollama will be unloaded before this job starts.")
    return {
        "allowed": pf["allow"],
        "blocked": pf["blocked"],
        "message": pf["warnings"][0] if pf["blocked"] else "",
        "warnings": pf["warnings"],
        "adjustments": pf["adjustments"],
        "queue_position": position,
        "advisory": " ".join(parts).strip(),
    }


def prepare_for_media_job(action: str) -> dict[str, Any]:
    """Run right before a queued media job executes."""
    if not routing_enabled():
        return {"skipped": True}
    if action not in _VRAM_ACTIONS:
        return {"skipped": True}

    from jarvis.services import ensure_comfyui_nvidia
    from jarvis.vram_guard import prepare_for_comfyui, vram_guard_enabled

    result: dict[str, Any] = {"action": action, "prepared": False}
    ensure_comfyui_nvidia(block=True, timeout=120)
    if vram_guard_enabled():
        prep = prepare_for_comfyui()
        result.update(prep)
        result["prepared"] = True
    elif is_low_vram(10240):
        unloaded = unload_ollama_models()
        result["unloaded_ollama"] = unloaded
        result["prepared"] = bool(unloaded)
    return result


def should_prefer_ken_burns() -> bool:
    """Extra guard beyond video_settings when Ollama still holds GPU."""
    if not routing_enabled():
        return False
    if not is_low_vram(10240):
        return False
    if ollama_loaded_models() and detect_gpu().get("ollama_using_gpu"):
        return True
    return False


def chat_busy_hint() -> str | None:
    snap = snapshot()
    media = snap["media_queue"]
    if not media.get("busy") and not media.get("pending"):
        return None
    label = media.get("label") or "media render"
    return (
        f"Note: GPU queue busy ({label}) — chat still works; heavy image/video jobs are serialized."
    )


def status_line() -> str:
    snap = snapshot()
    parts = []
    if snap["vram_mb"]:
        parts.append(f"{round(snap['vram_mb'] / 1024, 1)}GB VRAM")
    media = snap["media_queue"]
    if media.get("busy"):
        parts.append(f"busy: {media.get('label') or 'media'}")
    elif media.get("pending"):
        parts.append(f"queue: {media['pending']}")
    if snap["ollama_models_loaded"]:
        parts.append(f"Ollama×{snap['ollama_models_loaded']}")
    return " · ".join(parts) if parts else ""
