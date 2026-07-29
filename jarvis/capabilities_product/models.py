"""Capability record model and permission/trust helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


TRUST_LEVELS = (
    "built_in",
    "first_party",
    "trusted_local",
    "experimental",
    "untrusted",
    "disabled",
    "quarantined",
    "unknown",
)

TRUST_LABELS = {
    "built_in": "Built-in",
    "first_party": "First-party",
    "trusted_local": "Trusted Local",
    "experimental": "Experimental",
    "untrusted": "Untrusted",
    "disabled": "Disabled",
    "quarantined": "Quarantined",
    "unknown": "Unknown",
}

PERMISSION_LABELS = {
    "memory.read": "Read memory",
    "memory.write": "Write memory",
    "rag.search": "Search knowledge (RAG)",
    "graph.read": "Read knowledge graph",
    "graph.write": "Write knowledge graph",
    "automation.manage": "Manage automations",
    "workflow.run": "Run workflows",
    "http.egress": "Network (HTTP egress)",
    "fs.read": "Read filesystem",
    "fs.write": "Write filesystem",
    "tools.execute": "Execute tools",
    "voice.use": "Use Voice",
    "vision.use": "Use Vision",
    "browser.use": "Use Browser",
    "ha.control": "Control Home Assistant",
    "models.use": "Use models",
    "microphone": "Microphone",
    "camera": "Camera",
}


@dataclass
class CapabilityRecord:
    id: str
    name: str
    layer: str  # host | sdk | acm | platform
    category: str = "Utilities"
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    trust: str = "unknown"
    enabled: bool = True
    status: str = "discovered"  # discovered | loaded | enabled | disabled | failed | quarantined
    health: str = "unknown"  # healthy | degraded | failed | unknown
    permissions: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    path: str = ""
    tags: list[str] = field(default_factory=list)
    contributions: dict[str, Any] = field(default_factory=dict)
    isolation: str = "none"  # none | process | wasm | seccomp — honest
    sandbox_claimed: bool = False
    restart_required: bool = False
    lazy: bool = False
    error: str = ""
    risk_summary: str = ""
    source: str = ""
    experimental: bool = False
    update_available: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["trust_label"] = TRUST_LABELS.get(self.trust, self.trust)
        d["permission_labels"] = [PERMISSION_LABELS.get(p, p) for p in self.permissions]
        d["isolation_note"] = isolation_note(self.isolation, self.sandbox_claimed)
        return d


def isolation_note(isolation: str, sandbox_claimed: bool = False) -> str:
    if isolation in ("process", "wasm", "seccomp"):
        return f"Isolated via {isolation}."
    if sandbox_claimed:
        return (
            "Manifest requested sandbox, but Aria does not isolate capability code today. "
            "Code runs in-process with the Aria host."
        )
    return "No process isolation. Code runs in-process with the Aria host."


def risk_from_permissions(permissions: list[str], trust: str) -> str:
    if trust in ("built_in", "first_party"):
        base = "Shipped with Aria; treated as trusted first-party code."
    elif trust == "trusted_local":
        base = "Local capability you marked trusted; still runs in-process."
    elif trust == "experimental":
        base = "Experimental — may be unstable; review permissions carefully."
    elif trust == "untrusted":
        base = "Untrusted — keep disabled unless you accept full host access risk."
    else:
        base = "Review trust and permissions before enabling."
    sensitive = [p for p in permissions if p in ("fs.write", "tools.execute", "http.egress", "memory.write", "ha.control")]
    if sensitive:
        labels = ", ".join(PERMISSION_LABELS.get(p, p) for p in sensitive)
        return f"{base} Elevated: {labels}."
    if permissions:
        return f"{base} Declared permissions are listed for review."
    return f"{base} No special permissions declared."
