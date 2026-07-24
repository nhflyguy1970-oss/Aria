"""When to auto-start heavy services (ComfyUI, HA, model warmup) vs on-demand only."""

from __future__ import annotations

import os


def _env_on(name: str, *, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() not in ("0", "false", "no", "off")


def lazy_startup_enabled() -> bool:
    """True: only Ollama at ARIA open; Comfy/HA/vision warmup start when used."""
    return _env_on("JARVIS_LAZY_STARTUP", default="1")


def autostart_comfyui() -> bool:
    return _env_on("JARVIS_AUTOSTART_COMFYUI", default="0")


def autostart_ha() -> bool:
    return _env_on("JARVIS_HA_AUTOSTART", default="0")


def autostart_memgraph() -> bool:
    backend = os.getenv("JARVIS_GRAPH_BACKEND", "").strip().lower()
    default = "1" if backend == "memgraph" else "0"
    return _env_on("JARVIS_MEMGRAPH_AUTOSTART", default=default)


def model_warmup_enabled() -> bool:
    return _env_on("JARVIS_MODEL_WARMUP", default="0")


def router_warmup_enabled() -> bool:
    return _env_on("JARVIS_WARM_ROUTER", default="0")


def auto_pull_models_enabled() -> bool:
    return _env_on("JARVIS_AUTO_PULL_MODELS", default="0")


def manage_ollama_enabled() -> bool:
    """Jarvis may start ollama serve if not already running."""
    return _env_on("JARVIS_MANAGE_OLLAMA", default="1")
