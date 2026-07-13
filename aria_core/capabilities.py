"""Aria Core — Capabilities catalog + Capability Bus surface (Phase 3)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aria_core.capability_bus import (  # noqa: F401
    BUS_VERSION,
    backup,
    diagnose,
    execute_tool,
    health,
    infer,
    invoke,
    latest_backup_hint,
    learn,
    list_tools,
    mission_control_panel,
    notify,
    observe,
    plan,
    reason,
    recall,
    recover,
    reference,
    remember,
    repair,
    schedule,
    search,
)
from aria_core.capability_contracts import get_contract, list_contracts, validate_contracts
from aria_core.capability_registry import (
    REGISTRY,
    dependency_graph,
    get_capability,
    list_capabilities,
    validate_registry,
)
from aria_core.capability_registry import (
    all_capability_ids as bus_capability_ids,
)
from aria_core.ownership import module_ownership

OWNER = module_ownership("capabilities")

_CONTRACT = Path(__file__).resolve().parents[1] / "docs" / "aria_core" / "BEHAVIORAL_CONTRACT.json"


def list_capability_ids() -> list[str]:
    """Behavioral contract inventory ids (Phase 1 SSOT)."""
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
        from jarvis.handlers.registry import all_actions

        return [str(a.get("action")) for a in all_actions() if a.get("action")]
    except Exception:
        return []


def list_bus_verbs() -> list[str]:
    return bus_capability_ids()


def capability_interface() -> dict[str, Any]:
    """Future application consumption surface (no app migration in Phase 3)."""
    return {
        "owner": OWNER["owner"],
        "bus": "aria_core.capability_bus",
        "verbs": list_bus_verbs(),
        "registry": "aria_core.capability_registry",
        "contracts": "aria_core.capability_contracts",
        "version": BUS_VERSION,
        "note": "Applications should eventually depend on these verbs; organs stay put.",
    }


__all__ = [
    "BUS_VERSION",
    "OWNER",
    "REGISTRY",
    "backup",
    "capability_interface",
    "dependency_graph",
    "describe",
    "diagnose",
    "execute_tool",
    "get_capability",
    "get_contract",
    "health",
    "infer",
    "invoke",
    "latest_backup_hint",
    "learn",
    "list_bus_verbs",
    "list_capabilities",
    "list_capability_ids",
    "list_contracts",
    "list_registered_actions",
    "list_tools",
    "mission_control_panel",
    "notify",
    "observe",
    "plan",
    "reason",
    "recall",
    "recover",
    "reference",
    "remember",
    "repair",
    "schedule",
    "search",
    "validate_contracts",
    "validate_registry",
]
