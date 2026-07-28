"""AI stack recommender — suggest only, never auto-apply."""

from __future__ import annotations

from typing import Any


def recommend_stacks() -> dict[str, Any]:
    from jarvis.model_store import get_all_settings, PRESETS, _pick_for_role, OPTIMIZED_STANDARD, FAST_STANDARD

    settings = get_all_settings()
    installed = list(settings.get("installed") or [])
    hw = settings.get("hardware") or {}
    free_vram = None
    try:
        from jarvis.gpu import free_vram_mb

        free_vram = round(float(free_vram_mb() or 0) / 1024.0, 2)
    except Exception:
        pass

    def resolve(preset: dict[str, str]) -> dict[str, str]:
        return {role: _pick_for_role(role, preset, installed) for role in (
            "conversation", "coding", "reasoning", "vision", "embedding", "image", "fast_chat", "review"
        )}

    stacks = [
        {
            "id": "fast",
            "label": "Fast",
            "summary": "Prioritize latency and low VRAM",
            "roles": resolve(FAST_STANDARD),
            "why": "Uses smaller / faster tags when installed; good for interactive chat on 8GB GPUs.",
        },
        {
            "id": "balanced",
            "label": "Balanced",
            "summary": "Default quality preset tuned for this machine",
            "roles": resolve(OPTIMIZED_STANDARD),
            "why": "Matches Aria optimized defaults for chat, coding, vision, and embeddings.",
        },
        {
            "id": "quality",
            "label": "Quality",
            "summary": "Prefer higher-quality tags when available",
            "roles": resolve(PRESETS["quality"]["standard"]),
            "why": "Lean into 14B-class models when installed; may offload on 8GB VRAM.",
        },
        {
            "id": "coding",
            "label": "Coding focus",
            "summary": "Strengthen coding + review roles",
            "roles": {
                **resolve(OPTIMIZED_STANDARD),
                "coding": _pick_for_role("coding", {"coding": "deepseek-coder:latest"}, installed),
                "review": _pick_for_role("review", {"review": "deepseek-r1:7b"}, installed),
            },
            "why": "Best when Projects / coding jobs dominate.",
        },
        {
            "id": "vision",
            "label": "Vision focus",
            "summary": "Prefer capable vision tags",
            "roles": {
                **resolve(OPTIMIZED_STANDARD),
                "vision": _pick_for_role("vision", {"vision": "llava:13b"}, installed),
            },
            "why": "Use when Gallery / screenshot / document vision is primary.",
        },
        {
            "id": "reasoning",
            "label": "Reasoning focus",
            "summary": "Prefer reasoning models for chat + review",
            "roles": {
                **resolve(OPTIMIZED_STANDARD),
                "conversation": _pick_for_role("reasoning", {"reasoning": "deepseek-r1:7b"}, installed),
                "reasoning": _pick_for_role("reasoning", {"reasoning": "deepseek-r1:7b"}, installed),
            },
            "why": "Better for deep analysis; slower responses.",
        },
    ]

    missing = settings.get("missing_active") or []
    return {
        "ok": True,
        "auto_apply": False,
        "hardware": {**hw, "free_vram_gb": free_vram},
        "installed_count": len(installed),
        "missing_active": missing,
        "stacks": stacks,
        "guidance": "Review a stack, then Apply only after confirmation. Never auto-applied.",
        "product": "models",
    }
