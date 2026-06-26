"""Free GPU/RAM between heavy ML steps (MusicGen, Bark, Ollama)."""

from __future__ import annotations

import gc
import json
import os
import urllib.request


def system_ram_gb() -> float:
    try:
        with open("/proc/meminfo", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) / (1024 * 1024)
    except OSError:
        return 0.0
    return 0.0


def release_torch_memory() -> None:
    gc.collect()
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            if hasattr(torch.cuda, "ipc_collect"):
                torch.cuda.ipc_collect()
    except ImportError:
        pass


def unload_ollama_models(timeout: float = 8.0) -> list[str]:
    """Ask Ollama to drop loaded models so PyTorch can use the GPU."""
    host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    unloaded: list[str] = []
    try:
        with urllib.request.urlopen(f"{host}/api/ps", timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
        for entry in data.get("models", []):
            name = entry.get("name") or entry.get("model")
            if not name:
                continue
            body = json.dumps({"model": name, "prompt": ".", "stream": False, "keep_alive": 0}).encode()
            req = urllib.request.Request(
                f"{host}/api/generate",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                urllib.request.urlopen(req, timeout=timeout)
                unloaded.append(name)
            except Exception:
                pass
    except Exception:
        pass
    return unloaded


def resolve_song_mode(*, low_vram: bool, ram_gb: float) -> str:
    """Return safe | balanced | max."""
    mode_env = os.getenv("JARVIS_SONG_MODE", "").strip().lower()
    if mode_env in ("safe", "balanced", "max"):
        return mode_env

    safe_legacy = os.getenv("JARVIS_SONG_SAFE", "").strip().lower()
    if safe_legacy in ("1", "true", "yes"):
        return "safe"
    if safe_legacy in ("0", "false", "no"):
        return "max"

    if not low_vram:
        return "max"
    if ram_gb >= 32:
        return "balanced"
    return "safe"


def song_generation_plan(requested_duration: int) -> dict:
    """
    Plan resource use for song jobs.

    balanced (8GB GPU + lots of RAM): GPU music one-at-a-time, vocals on CPU.
    safe: instrumental only, short clips.
    max: prefer GPU for everything (may OOM on 8GB).
    """
    from jarvis.gpu import detect_gpu, is_low_vram

    gpu = detect_gpu()
    vram = int(gpu.get("vram_mb") or 0)
    ram_gb = round(system_ram_gb(), 1)
    low_vram = is_low_vram(10240)
    mode = resolve_song_mode(low_vram=low_vram, ram_gb=ram_gb)

    vocals_env = os.getenv("JARVIS_SONG_VOCALS", "").strip().lower()
    if vocals_env in ("0", "false", "no"):
        allow_vocals = False
    elif vocals_env in ("1", "true", "yes"):
        allow_vocals = True
    else:
        allow_vocals = mode != "safe"

    vocal_dev_env = os.getenv("JARVIS_SONG_VOCAL_DEVICE", "auto").strip().lower()
    if vocal_dev_env in ("cpu", "cuda"):
        vocal_device = vocal_dev_env
    elif mode == "balanced" or (low_vram and ram_gb >= 32):
        vocal_device = "cpu"
    else:
        vocal_device = "cuda"

    music_dev_env = os.getenv("JARVIS_SONG_MUSIC_DEVICE", "auto").strip().lower()
    if music_dev_env in ("cpu", "cuda"):
        music_device = music_dev_env
    elif mode == "safe":
        music_device = "cuda"
    elif mode == "balanced":
        music_device = "cuda"
    else:
        music_device = "cuda"

    mode_cap = {"safe": 15, "balanced": 30, "max": 30}[mode]
    env_max = int(os.getenv("JARVIS_SONG_MAX_DURATION", str(mode_cap)) or mode_cap)
    max_dur = min(max(1, env_max), 30, mode_cap)
    duration = min(max(5, int(requested_duration)), max_dur)

    warning = ""
    if mode == "safe" and not allow_vocals:
        warning = (
            f"Safe mode ({vram or '?'}MB VRAM): instrumental only, {duration}s. "
            "Set JARVIS_SONG_MODE=balanced for full songs on CPU vocals."
        )
    elif mode == "balanced" and allow_vocals:
        warning = (
            f"Balanced mode: GPU music ({duration}s max), AI vocals on CPU "
            f"({int(ram_gb)}GB RAM) — slower but avoids reboots."
        )
    elif mode == "max" and low_vram:
        warning = "Max mode on limited VRAM — may OOM/reboot if multiple GPU models overlap."

    return {
        "mode": mode,
        "safe_mode": mode == "safe",
        "allow_vocals": allow_vocals,
        "vocal_device": vocal_device,
        "music_device": music_device,
        "duration": duration,
        "unload_ollama_before_music": mode in ("safe", "balanced") or (0 < vram <= 12288),
        "sequential_unload": mode in ("safe", "balanced"),
        "warning": warning,
        "vram_mb": vram,
        "ram_gb": ram_gb,
    }
