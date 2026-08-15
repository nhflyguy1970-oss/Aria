"""Dependency chains — always repair from the lowest dependency first."""

from __future__ import annotations

from typing import Any

# Lower in the chain = more foundational (repair first)
DEPENDENCY_EDGES: dict[str, list[str]] = {
    # child depends on parents
    "search": ["documents", "system"],
    "documents": ["system"],
    "ocr": ["documents", "system"],
    "gallery": ["system"],
    "providers": ["docker", "system"],
    "coding": ["providers", "system"],
    "voice": ["providers", "system"],
    "mission_control": ["system"],
    "health": ["system"],
    "acm": ["system"],
    "smarthome": ["system"],
    "browser": ["system"],
    "jobs": ["system"],
    "docker": ["system"],
    "planner": ["system"],
    "calendar": ["system"],
    "flytying": ["system"],
    "aria": ["system"],
}


def chain_for(subsystem: str) -> list[str]:
    """Return foundational → leaf order for a subsystem."""
    seen: set[str] = set()
    order: list[str] = []

    def walk(node: str) -> None:
        if node in seen:
            return
        seen.add(node)
        for parent in DEPENDENCY_EDGES.get(node) or []:
            walk(parent)
        order.append(node)

    walk(subsystem or "system")
    return order


def analyze(subsystem: str, *, related: list[str] | None = None) -> dict[str, Any]:
    chain = chain_for(subsystem)
    related = related or []
    for r in related:
        for n in chain_for(r):
            if n not in chain:
                # merge foundational nodes earlier
                chain = list(dict.fromkeys([*chain_for(r), *chain]))
    # Display top→bottom as foundation→symptom for UI (storage→documents→search)
    return {
        "subsystem": subsystem,
        "chain": chain,
        "repair_order": chain,  # lowest dependency first
        "display": " → ".join(chain),
        "display_vertical": chain,
        "note": "Always repair from the lowest dependency first.",
    }


def order_issues_by_dependency(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Stable sort: more foundational subsystems first within same priority."""

    def depth(iss: dict[str, Any]) -> int:
        sub = iss.get("subsystem") or ""
        return len(chain_for(sub))

    return sorted(issues, key=lambda i: depth(i))
