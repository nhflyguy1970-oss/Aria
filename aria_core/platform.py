"""Aria Core — Platform (delegates to aiplatform.workstation when present)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aria_core._delegate import soft_import
from aria_core.ownership import module_ownership

OWNER = module_ownership("platform")


def workstation_available() -> bool:
    return soft_import("aiplatform.workstation") is not None


def platform_root_hint() -> str | None:
    try:
        from aiplatform.workstation.paths import platform_root

        return str(platform_root())
    except Exception:
        root = Path(__file__).resolve().parents[1].parent / "AI-Platform"
        return str(root) if root.is_dir() else None


def platform_snapshot() -> dict[str, Any]:
    return {
        "available": workstation_available(),
        "root": platform_root_hint(),
        "owner": OWNER["owner"],
        "implementation": OWNER["implementation"],
    }
