"""Stop GPU-heavy Jarvis services so the machine is ready for gaming."""

from __future__ import annotations

import logging
import os
import shutil
import signal
import subprocess
import time

from jarvis.ml_memory import release_torch_memory, unload_ollama_models

log = logging.getLogger("jarvis.gaming_shutdown")


def _kill_ollama_serve() -> bool:
    """Stop Ollama serve when JARVIS_GAMING_KILL_OLLAMA allows it."""
    if os.getenv("JARVIS_GAMING_KILL_OLLAMA", "1").strip().lower() in ("0", "false", "no", "off"):
        return False
    try:
        from jarvis.services import stop_managed_services

        stop_managed_services()
    except Exception as exc:
        log.debug("stop_managed_services: %s", exc)
    if not shutil.which("ollama"):
        return False
    try:
        out = subprocess.run(
            ["pgrep", "-x", "ollama"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        for line in (out.stdout or "").splitlines():
            pid = int(line.strip())
            if pid <= 1:
                continue
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                continue
        time.sleep(0.5)
        return True
    except Exception as exc:
        log.debug("Ollama kill skipped: %s", exc)
        return False


def stop_all_for_gaming() -> dict[str, object]:
    """Unload models, stop ComfyUI, clear PyTorch cache — best effort."""
    result: dict[str, object] = {"ok": True}

    try:
        from jarvis.services import stop_comfyui

        stop_comfyui()
        result["comfyui_stopped"] = True
    except Exception as exc:
        log.warning("ComfyUI stop failed: %s", exc)
        result["comfyui_stopped"] = False

    unloaded = unload_ollama_models()
    release_torch_memory()
    result["unloaded_ollama"] = unloaded
    result["released_torch"] = True

    result["ollama_stopped"] = _kill_ollama_serve()

    try:
        from jarvis.gpu import detect_gpu

        gpu = detect_gpu()
        result["vram_mb"] = gpu.get("vram_mb")
        result["free_vram_mb"] = gpu.get("free_vram_mb")
    except Exception:
        pass

    log.info(
        "Gaming shutdown: comfy=%s ollama_models=%d ollama_kill=%s",
        result.get("comfyui_stopped"),
        len(unloaded),
        result.get("ollama_stopped"),
    )
    return result
