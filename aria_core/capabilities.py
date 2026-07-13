"""Aria Core — Capabilities catalog (pointers; no new logic)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aria_core.ownership import module_ownership

OWNER = module_ownership("capabilities")

_CONTRACT = Path(__file__).resolve().parents[1] / "docs" / "aria_core" / "BEHAVIORAL_CONTRACT.json"


def list_capability_ids() -> list[str]:
    if not _CONTRACT.is_file():
        return []
    data = json.loads(_CONTRACT.read_text(encoding="utf-8"))
    return [c["id"] for c in data.get("capabilities") or []]


def describe(capability_id: str) -> dict[str, Any] | None:
    if not _CONTRACT.is_file():
        return None
    data = json.loads(_CONTRACT.read_text(encoding="utf-8"))
    for cap in data.get("capabilities") or []:
        if cap.get("id") == capability_id:
            return dict(cap)
    return None


def list_registered_actions() -> list[str]:
    try:
        from jarvis.handlers.registry import list_actions

        return list(list_actions())
    except Exception:
        try:
            from jarvis.handlers import registry

            actions = getattr(registry, "ACTIONS", None) or getattr(registry, "_ACTIONS", {})
            return sorted(str(k) for k in actions.keys())
        except Exception:
            return []
