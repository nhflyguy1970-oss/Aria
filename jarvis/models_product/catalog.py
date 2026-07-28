"""Model catalog + rich model cards."""

from __future__ import annotations

import re
from typing import Any

# Curated metadata for known tags — used when live discovery lacks details.
_CATALOG_META: dict[str, dict[str, Any]] = {
    "qwen2.5:7b": {
        "friendly_name": "Qwen 2.5 7B",
        "capabilities": ["chat", "tools", "coding_assist"],
        "estimated_vram_gb": 5.0,
        "recommended_ram_gb": 16,
        "context_window": 32768,
        "quantization": "Q4_K_M (typical)",
        "license": "Apache-2.0",
        "recommended_uses": ["Great for chat", "Balanced quality", "Fits 8GB with headroom"],
        "tags": ["fast", "chat", "general"],
    },
    "qwen2.5:14b": {
        "friendly_name": "Qwen 2.5 14B",
        "capabilities": ["chat", "tools", "reasoning"],
        "estimated_vram_gb": 9.0,
        "recommended_ram_gb": 32,
        "context_window": 32768,
        "quantization": "Q4_K_M (typical)",
        "license": "Apache-2.0",
        "recommended_uses": ["Higher quality chat", "May offload on 8GB"],
        "tags": ["quality", "chat"],
    },
    "qwen2.5-coder:7b": {
        "friendly_name": "Qwen 2.5 Coder 7B",
        "capabilities": ["coding", "tools"],
        "estimated_vram_gb": 5.0,
        "recommended_ram_gb": 16,
        "context_window": 32768,
        "license": "Apache-2.0",
        "recommended_uses": ["Great for coding", "Fast responses"],
        "tags": ["coding", "fast"],
    },
    "qwen2.5-coder:1.5b-base": {
        "friendly_name": "Qwen 2.5 Coder 1.5B",
        "capabilities": ["coding", "routing", "tools"],
        "estimated_vram_gb": 1.5,
        "recommended_ram_gb": 8,
        "context_window": 32768,
        "license": "Apache-2.0",
        "recommended_uses": ["Low VRAM", "Router / NLU", "Fast responses"],
        "tags": ["low-vram", "router", "fast"],
    },
    "qwen3:1.7b": {
        "friendly_name": "Qwen 3 1.7B",
        "capabilities": ["chat", "fast"],
        "estimated_vram_gb": 1.8,
        "recommended_ram_gb": 8,
        "context_window": 32768,
        "license": "Apache-2.0",
        "recommended_uses": ["Low VRAM", "Fast responses"],
        "tags": ["low-vram", "fast"],
    },
    "deepseek-coder:latest": {
        "friendly_name": "DeepSeek Coder",
        "capabilities": ["coding", "tools"],
        "estimated_vram_gb": 5.5,
        "recommended_ram_gb": 16,
        "context_window": 16384,
        "license": "Custom",
        "recommended_uses": ["Great for coding", "Best coding default"],
        "tags": ["coding"],
    },
    "deepseek-r1:7b": {
        "friendly_name": "DeepSeek R1 7B",
        "capabilities": ["reasoning", "chat"],
        "estimated_vram_gb": 5.5,
        "recommended_ram_gb": 16,
        "context_window": 32768,
        "license": "MIT",
        "recommended_uses": ["Best reasoning", "Code review"],
        "tags": ["reasoning"],
    },
    "moondream:latest": {
        "friendly_name": "Moondream",
        "capabilities": ["vision"],
        "estimated_vram_gb": 2.0,
        "recommended_ram_gb": 8,
        "context_window": 2048,
        "license": "Apache-2.0",
        "recommended_uses": ["Supports vision", "Low VRAM"],
        "tags": ["vision", "low-vram"],
    },
    "llava:13b": {
        "friendly_name": "LLaVA 13B",
        "capabilities": ["vision", "chat"],
        "estimated_vram_gb": 10.0,
        "recommended_ram_gb": 32,
        "context_window": 4096,
        "license": "Apache-2.0",
        "recommended_uses": ["Supports vision", "Quality vision"],
        "tags": ["vision", "quality"],
    },
    "nomic-embed-text": {
        "friendly_name": "Nomic Embed Text",
        "capabilities": ["embedding"],
        "estimated_vram_gb": 0.5,
        "recommended_ram_gb": 4,
        "context_window": 8192,
        "license": "Apache-2.0",
        "recommended_uses": ["Embeddings", "Memory / RAG"],
        "tags": ["embedding", "low-vram"],
    },
    "nomic-embed-text:latest": {
        "friendly_name": "Nomic Embed Text",
        "capabilities": ["embedding"],
        "estimated_vram_gb": 0.5,
        "recommended_ram_gb": 4,
        "context_window": 8192,
        "license": "Apache-2.0",
        "recommended_uses": ["Embeddings", "Memory / RAG"],
        "tags": ["embedding", "low-vram"],
    },
    "dolphin-mistral:latest": {
        "friendly_name": "Dolphin Mistral",
        "capabilities": ["chat", "uncensored"],
        "estimated_vram_gb": 5.0,
        "recommended_ram_gb": 16,
        "context_window": 32768,
        "license": "Apache-2.0",
        "recommended_uses": ["Uncensored profile chat"],
        "tags": ["uncensored", "chat"],
    },
    "comfyui": {
        "friendly_name": "ComfyUI (image)",
        "capabilities": ["image"],
        "estimated_vram_gb": 4.0,
        "recommended_ram_gb": 16,
        "provider": "comfyui",
        "license": "GPL-3.0",
        "recommended_uses": ["Image generation"],
        "tags": ["image"],
        "pullable": False,
    },
}


def _parse_size_hint(tag: str) -> float | None:
    m = re.search(r":?(\d+(?:\.\d+)?)[bB]\b", tag)
    if not m:
        m = re.search(r"(\d+(?:\.\d+)?)[bB]", tag)
    if not m:
        return None
    try:
        params = float(m.group(1))
        # Rough Q4 estimate: ~0.6–0.7 GB per B
        return round(params * 0.65, 1)
    except ValueError:
        return None


def _free_vram_gb() -> float | None:
    try:
        from jarvis.gpu import free_vram_mb

        mb = free_vram_mb()
        if mb is None:
            return None
        return round(float(mb) / 1024.0, 2)
    except Exception:
        return None


def _loaded_names() -> set[str]:
    try:
        from jarvis.resource_router import ollama_loaded_models

        names = set()
        for m in ollama_loaded_models() or []:
            n = m.get("name") or m.get("model") or ""
            if n:
                names.add(n)
                names.add(n.split(":")[0])
        return names
    except Exception:
        return set()


def build_model_card(tag: str, *, installed: list[str] | None = None, free_vram_gb: float | None = None) -> dict[str, Any]:
    tag = (tag or "").strip()
    installed = installed if installed is not None else []
    installed_set = {x.lower() for x in installed}
    meta = dict(_CATALOG_META.get(tag) or _CATALOG_META.get(tag.split(":")[0]) or {})
    friendly = meta.get("friendly_name") or tag.replace(":", " · ")
    vram = meta.get("estimated_vram_gb")
    if vram is None:
        vram = _parse_size_hint(tag)
    if free_vram_gb is None:
        free_vram_gb = _free_vram_gb()
    fits = None
    confidence = "medium"
    if vram is not None and free_vram_gb is not None:
        fits = free_vram_gb >= float(vram) * 0.9
        confidence = "high" if tag in _CATALOG_META else "medium"
    elif vram is not None:
        confidence = "low"
    loaded = _loaded_names()
    running = tag in loaded or tag.split(":")[0] in loaded or any(tag.lower() == n.lower() for n in loaded)
    is_installed = tag.lower() in installed_set or any(
        x.lower() == tag.lower() or x.lower().startswith(tag.lower().split(":")[0]) for x in installed
    )
    provider = meta.get("provider") or ("comfyui" if tag.lower() == "comfyui" else "ollama")
    caps = list(meta.get("capabilities") or [])
    if "vision" in tag.lower() or "llava" in tag.lower() or "moondream" in tag.lower():
        if "vision" not in caps:
            caps.append("vision")
    if "embed" in tag.lower():
        if "embedding" not in caps:
            caps.append("embedding")
    if "coder" in tag.lower() or "code" in tag.lower():
        if "coding" not in caps:
            caps.append("coding")

    conflicts = []
    if fits is False:
        conflicts.append("May exceed free VRAM — unload models or pick a smaller tag")
    if provider == "comfyui":
        conflicts.append("Competes with Ollama for GPU — Free VRAM before heavy image jobs")

    return {
        "id": tag,
        "tag": tag,
        "friendly_name": friendly,
        "provider": provider,
        "capabilities": caps,
        "estimated_vram_gb": vram,
        "recommended_ram_gb": meta.get("recommended_ram_gb"),
        "context_window": meta.get("context_window"),
        "quantization": meta.get("quantization"),
        "license": meta.get("license") or "Unknown",
        "installed": is_installed or tag.lower() == "comfyui",
        "running": running,
        "warm": running,
        "recommended_uses": list(meta.get("recommended_uses") or []),
        "tags": list(meta.get("tags") or []),
        "confidence": confidence,
        "fits_current_hardware": fits,
        "free_vram_gb": free_vram_gb,
        "potential_conflicts": conflicts,
        "pullable": meta.get("pullable", provider == "ollama"),
        "homepage": meta.get("homepage"),
    }


def build_catalog(
    *,
    q: str = "",
    capability: str = "",
    provider: str = "",
    installed_only: bool = False,
    sort: str = "name",
) -> dict[str, Any]:
    from jarvis.model_store import get_all_settings

    settings = get_all_settings()
    installed = list(settings.get("installed") or [])
    # Seed catalog with installed + curated + active role models
    tags: set[str] = set(installed)
    tags.update(_CATALOG_META.keys())
    active = settings.get("active") or {}
    tags.update(str(v) for v in active.values() if v)
    free = _free_vram_gb()
    cards = [build_model_card(t, installed=installed, free_vram_gb=free) for t in tags if t]

    ql = (q or "").strip().lower()
    if ql:
        cards = [
            c
            for c in cards
            if ql in c["tag"].lower()
            or ql in c["friendly_name"].lower()
            or any(ql in u.lower() for u in c["recommended_uses"])
            or any(ql in t.lower() for t in c["tags"])
            or any(ql in cap.lower() for cap in c["capabilities"])
        ]
    if capability:
        cap = capability.lower()
        cards = [c for c in cards if cap in [x.lower() for x in c["capabilities"]] or cap in c["tags"]]
    if provider:
        cards = [c for c in cards if c["provider"].lower() == provider.lower()]
    if installed_only:
        cards = [c for c in cards if c["installed"]]

    if sort == "vram":
        cards.sort(key=lambda c: (c.get("estimated_vram_gb") is None, c.get("estimated_vram_gb") or 0))
    elif sort == "installed":
        cards.sort(key=lambda c: (not c["installed"], c["friendly_name"].lower()))
    else:
        cards.sort(key=lambda c: c["friendly_name"].lower())

    loaded = []
    try:
        from jarvis.resource_router import ollama_loaded_models

        loaded = ollama_loaded_models()
    except Exception:
        loaded = []

    return {
        "ok": True,
        "count": len(cards),
        "cards": cards,
        "loaded_models": loaded,
        "free_vram_gb": free,
        "filters": {"q": q, "capability": capability, "provider": provider, "installed_only": installed_only, "sort": sort},
        "product": "models",
    }
