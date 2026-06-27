"""Local vs cloud brain / voice mode indicator."""

from __future__ import annotations

import os
from typing import Any


def brain_mode_status() -> dict[str, Any]:
    from jarvis.ollama_health import check_ollama
    from jarvis.p4_flags import cloud_live_voice_enabled

    ollama = check_ollama()
    local_ok = bool(ollama.get("running"))
    cloud_bits: list[str] = []
    if os.getenv("OPENAI_API_KEY", "").strip():
        cloud_bits.append("OpenAI")
    if os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip():
        cloud_bits.append("Gemini")
    if os.getenv("JARVIS_MESHY_API_KEY", "").strip() or os.getenv("MESHY_API_KEY", "").strip():
        cloud_bits.append("Meshy")

    if local_ok and cloud_bits:
        mode = "hybrid"
    elif local_ok:
        mode = "local"
    elif cloud_bits:
        mode = "cloud"
    else:
        mode = "offline"

    return {
        "mode": mode,
        "local": local_ok,
        "ollama_models": len(ollama.get("models") or []),
        "cloud_providers": cloud_bits,
        "cloud_live_voice": cloud_live_voice_enabled(),
        "label": {
            "local": "Local brain (Ollama)",
            "cloud": "Cloud APIs",
            "hybrid": "Local + cloud",
            "offline": "Offline — check Ollama",
        }.get(mode, mode),
    }
