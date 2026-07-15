"""Memory hierarchy — layers, promotion, retention, consolidation, retrieval priority."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from jarvis.modules.memory_common import parse_ts, relevance_score

logger = logging.getLogger("jarvis.memory.hierarchy")

LAYER_TAG = "memory_layer"


class MemoryLayer(StrEnum):
    WORKING = "working"
    CONVERSATION = "conversation"
    PROJECT = "project"
    SEMANTIC = "semantic"
    KNOWLEDGE = "knowledge"
    EPISODIC = "episodic"
    PROCEDURAL = "procedural"
    LONG_TERM = "long_term"


# Higher number = higher retrieval priority in chat
RETRIEVAL_PRIORITY: dict[str, int] = {
    MemoryLayer.LONG_TERM.value: 100,
    MemoryLayer.PROCEDURAL.value: 90,
    MemoryLayer.PROJECT.value: 80,
    MemoryLayer.SEMANTIC.value: 75,
    MemoryLayer.KNOWLEDGE.value: 70,
    MemoryLayer.EPISODIC.value: 60,
    MemoryLayer.CONVERSATION.value: 50,
    MemoryLayer.WORKING.value: 40,
}

RETENTION_DAYS: dict[str, int | None] = {
    MemoryLayer.WORKING.value: 1,
    MemoryLayer.CONVERSATION.value: 30,
    MemoryLayer.PROJECT.value: 180,
    MemoryLayer.SEMANTIC.value: 365,
    MemoryLayer.KNOWLEDGE.value: None,
    MemoryLayer.EPISODIC.value: 90,
    MemoryLayer.PROCEDURAL.value: None,
    MemoryLayer.LONG_TERM.value: None,
}

TYPE_DEFAULT_LAYER: dict[str, str] = {
    "preference": MemoryLayer.LONG_TERM.value,
    "strategy": MemoryLayer.PROCEDURAL.value,
    "teaching": MemoryLayer.KNOWLEDGE.value,
    "project": MemoryLayer.PROJECT.value,
    "success": MemoryLayer.EPISODIC.value,
    "failure": MemoryLayer.EPISODIC.value,
    "fact": MemoryLayer.SEMANTIC.value,
    "note": MemoryLayer.CONVERSATION.value,
    "auto": MemoryLayer.CONVERSATION.value,
}


def infer_layer(entry: dict) -> str:
    tags = entry.get("tags") or []
    for tag in tags:
        if isinstance(tag, str) and tag.startswith("layer:"):
            return tag.split(":", 1)[-1]
    if LAYER_TAG in entry:
        return str(entry[LAYER_TAG])
    ns = str(entry.get("namespace") or "")
    if ns.startswith("project:"):
        return MemoryLayer.PROJECT.value
    if ns in ("profile", "aria:profile"):
        return MemoryLayer.LONG_TERM.value
    if ns == "tools":
        return MemoryLayer.PROCEDURAL.value
    return TYPE_DEFAULT_LAYER.get(str(entry.get("type") or "note"), MemoryLayer.CONVERSATION.value)


def tag_layer(entry: dict, layer: str | MemoryLayer) -> dict:
    layer_val = layer.value if isinstance(layer, MemoryLayer) else str(layer)
    entry = dict(entry)
    entry[LAYER_TAG] = layer_val
    tags = list(entry.get("tags") or [])
    tags = [t for t in tags if not (isinstance(t, str) and t.startswith("layer:"))]
    tags.append(f"layer:{layer_val}")
    entry["tags"] = tags
    return entry


def retrieval_score(entry: dict, *, base: float | None = None) -> float:
    layer = infer_layer(entry)
    priority = RETRIEVAL_PRIORITY.get(layer, 50)
    base_score = base if base is not None else relevance_score(entry)
    access = min(20, int(entry.get("access_count") or 0))
    return base_score + priority * 0.01 + access * 0.05


def hierarchical_search(
    memory: Any, query: str, *, limit: int = 10, namespace: str | None = None
) -> list[dict]:
    """Search memory with layer-aware ranking."""
    hits = memory.search(query, limit=max(limit * 3, 15), namespace=namespace)
    for h in hits:
        h["_layer"] = infer_layer(h)
        h["_rank"] = retrieval_score(h, base=float(h.get("score") or 0))
    hits.sort(key=lambda e: e.get("_rank", 0), reverse=True)
    return hits[:limit]


def should_promote(entry: dict) -> str | None:
    """Return target layer if entry should be promoted, else None."""
    layer = infer_layer(entry)
    access = int(entry.get("access_count") or 0)
    age_days = (datetime.now(UTC) - parse_ts(entry.get("timestamp", ""))).days

    if layer == MemoryLayer.CONVERSATION.value and access >= 3:
        ns = str(entry.get("namespace") or "")
        if ns.startswith("project:"):
            return MemoryLayer.PROJECT.value
        if entry.get("type") == "preference":
            return MemoryLayer.LONG_TERM.value
        return MemoryLayer.SEMANTIC.value

    if layer == MemoryLayer.PROJECT.value and access >= 5:
        return MemoryLayer.SEMANTIC.value

    if layer == MemoryLayer.EPISODIC.value and entry.get("type") == "success" and access >= 2:
        return MemoryLayer.PROCEDURAL.value

    if layer == MemoryLayer.PROCEDURAL.value and access >= 10 and age_days >= 7:
        return MemoryLayer.LONG_TERM.value

    if layer == MemoryLayer.SEMANTIC.value and access >= 15 and age_days >= 14:
        return MemoryLayer.LONG_TERM.value

    return None


def should_prune(entry: dict) -> bool:
    layer = infer_layer(entry)
    max_days = RETENTION_DAYS.get(layer)
    if max_days is None:
        return False
    if str(entry.get("type")) in ("preference", "strategy", "teaching"):
        return False
    if int(entry.get("access_count") or 0) >= 5:
        return False
    age_days = (datetime.now(UTC) - parse_ts(entry.get("timestamp", ""))).days
    return age_days > max_days


def consolidate(memory: Any, *, dry_run: bool = False) -> dict[str, Any]:
    """Promote/prune — M4d: no legacy SoT mutation when ACM is authoritative."""
    try:
        from aria_core import acm_bridge

        if acm_bridge.acm_is_authoritative():
            return {
                "ok": True,
                "promoted": 0,
                "layers_updated": 0,
                "pruned": 0,
                "dry_run": dry_run,
                "total": 0,
                "authoritative": "acm",
                "note": "M4d: hierarchy SoT consolidate disabled; ACM owns accessibility",
            }
    except Exception:
        pass

    promoted = 0
    pruned = 0
    layers_updated = 0

    entries = memory.list_entries() if hasattr(memory, "list_entries") else []
    for entry in entries:
        target = should_promote(entry)
        if target and target != infer_layer(entry):
            layers_updated += 1
            promoted += 1
            if not dry_run and hasattr(memory, "update"):
                tagged = tag_layer(entry, target)
                memory.update(entry["id"], tags=tagged.get("tags"))

    if hasattr(memory, "list_entries"):
        for entry in memory.list_entries():
            if should_prune(entry):
                pruned += 1
                if not dry_run and hasattr(memory, "delete_id"):
                    memory.delete_id(entry["id"])

    return {
        "ok": True,
        "promoted": promoted,
        "layers_updated": layers_updated,
        "pruned": pruned,
        "dry_run": dry_run,
        "total": len(entries),
    }


def layer_summary(memory: Any) -> dict[str, int]:
    counts: dict[str, int] = {layer.value: 0 for layer in MemoryLayer}
    if not hasattr(memory, "list_entries"):
        return counts
    for entry in memory.list_entries():
        layer = infer_layer(entry)
        counts[layer] = counts.get(layer, 0) + 1
    return counts


def format_hierarchy_markdown(memory: Any) -> str:
    summary = layer_summary(memory)
    lines = ["## Memory hierarchy", ""]
    for layer in MemoryLayer:
        count = summary.get(layer.value, 0)
        retain = RETENTION_DAYS.get(layer.value)
        retain_label = "permanent" if retain is None else f"{retain}d"
        lines.append(f"- **{layer.value}**: {count} entries · retain {retain_label}")
    return "\n".join(lines)
