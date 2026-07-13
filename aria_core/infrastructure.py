"""Aria Core — Infrastructure (delegates to jarvis GPU/VRAM helpers)."""

from __future__ import annotations

from typing import Any

from aria_core.ownership import module_ownership

OWNER = module_ownership("infrastructure")


def vram_guard_available() -> bool:
    try:
        import jarvis.vram_guard  # noqa: F401

        return True
    except ImportError:
        return False


def gpu_module() -> Any:
    from jarvis import gpu

    return gpu


def infrastructure_snapshot() -> dict[str, Any]:
    return {
        "vram_guard": vram_guard_available(),
        "owner": OWNER["owner"],
        "implementation": OWNER["implementation"],
    }
