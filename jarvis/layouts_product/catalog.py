"""Built-in Layout catalog — full frozen starter snapshots (honest)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from jarvis.layouts_product.schema import make_snapshot

# Full frozen defaults — applying a builtin replaces chrome fields, not a partial overlay.
_BUILTINS: list[dict[str, Any]] = [
    {
        "id": "coding",
        "label": "Coding",
        "kind": "starter",
        "description": "Chat + Projects + Memory + Documents + Mission Control.",
        "aliases": ["dev", "code"],
        "recommended_project": True,
        "snapshot": make_snapshot(
            {
                "view": "chat",
                "favorites": ["chat", "projects", "memory", "documents", "workstation"],
                "module": "coding",
                "role": "developer",
                "density": "comfortable",
                "dockHidden": False,
                "statusBarHidden": False,
                "miniChatHidden": False,
                "split": {"enabled": False, "primary": None, "secondary": None, "ratio": 0.55},
            },
            label="Coding",
            kind="starter",
        ),
    },
    {
        "id": "writing",
        "label": "Writing",
        "kind": "starter",
        "description": "Chat + Journal + Documents + Memory + Planner.",
        "aliases": ["write", "docs"],
        "snapshot": make_snapshot(
            {
                "view": "chat",
                "favorites": ["chat", "journal", "documents", "memory", "planner"],
                "module": "general",
                "role": "default",
            },
            label="Writing",
            kind="starter",
        ),
    },
    {
        "id": "research",
        "label": "Research",
        "kind": "starter",
        "description": "Browser + Documents + Memory + Chat + Home.",
        "aliases": ["browse", "web"],
        "snapshot": make_snapshot(
            {
                "view": "browser",
                "favorites": ["browser", "documents", "memory", "chat", "dashboard"],
                "module": "general",
                "role": "research",
            },
            label="Research",
            kind="starter",
        ),
    },
    {
        "id": "flytying",
        "label": "Fly Tying",
        "kind": "starter",
        "description": "Fly Tying + Gallery + Chat + Maker + Journal.",
        "aliases": ["fly", "tying"],
        "snapshot": make_snapshot(
            {
                "view": "flytying",
                "favorites": ["flytying", "gallery", "chat", "maker", "journal"],
                "role": "maker",
            },
            label="Fly Tying",
            kind="starter",
        ),
    },
    {
        "id": "maker",
        "label": "Maker",
        "kind": "starter",
        "description": "Maker Lab + Gallery + Projects + Chat + Documents.",
        "aliases": ["lab"],
        "snapshot": make_snapshot(
            {
                "view": "maker",
                "favorites": ["maker", "gallery", "projects", "chat", "documents"],
                "role": "maker",
            },
            label="Maker",
            kind="starter",
        ),
    },
    {
        "id": "media",
        "label": "Media",
        "kind": "starter",
        "description": "Gallery + Video + Meme + Audio + Chat.",
        "aliases": ["gallery", "images"],
        "snapshot": make_snapshot(
            {
                "view": "gallery",
                "favorites": ["gallery", "video", "meme", "audio", "chat"],
                "module": "image",
                "role": "media",
            },
            label="Media",
            kind="starter",
        ),
    },
    {
        "id": "planning",
        "label": "Planning",
        "kind": "starter",
        "description": "Planner + Calendar + Journal + Home + Chat.",
        "aliases": ["planner", "plan"],
        "snapshot": make_snapshot(
            {
                "view": "planner",
                "favorites": ["planner", "calendar", "journal", "dashboard", "chat"],
                "role": "default",
            },
            label="Planning",
            kind="starter",
        ),
    },
    {
        "id": "home",
        "label": "Home",
        "kind": "starter",
        "description": "Home + Mission Control + Planner + Chat + Memory.",
        "aliases": ["dashboard"],
        "snapshot": make_snapshot(
            {
                "view": "dashboard",
                "favorites": ["dashboard", "workstation", "planner", "chat", "memory"],
                "role": "default",
            },
            label="Home",
            kind="starter",
        ),
    },
    # Role packs (nice-to-have)
    {
        "id": "role-operations",
        "label": "Operations",
        "kind": "role",
        "description": "Mission Control–forward shell for ops days.",
        "aliases": ["ops"],
        "snapshot": make_snapshot(
            {
                "view": "workstation",
                "favorites": ["workstation", "dashboard", "automation", "models", "chat"],
                "role": "operations",
                "density": "compact",
            },
            label="Operations",
            kind="role",
        ),
    },
]


def list_builtins() -> list[dict[str, Any]]:
    return [deepcopy(x) for x in _BUILTINS]


def get_builtin(layout_id: str) -> dict[str, Any] | None:
    lid = (layout_id or "").strip().lower()
    # compat alias
    if lid == "dashboard":
        lid = "home"
    for item in _BUILTINS:
        if item["id"] == lid:
            return deepcopy(item)
        aliases = item.get("aliases") or []
        if lid in aliases:
            return deepcopy(item)
    return None


def search_builtins(query: str, *, limit: int = 24) -> list[dict[str, Any]]:
    q = (query or "").strip().lower()
    items = list_builtins()
    if not q:
        return items[:limit]
    scored: list[tuple[int, dict[str, Any]]] = []
    for it in items:
        blob = " ".join(
            [
                it.get("id", ""),
                it.get("label", ""),
                it.get("description", ""),
                it.get("kind", ""),
                " ".join(it.get("aliases") or []),
            ]
        ).lower()
        score = 0
        if q in blob:
            score += 10
        for tok in q.split():
            if tok in blob:
                score += 3
        if score:
            scored.append((score, it))
    scored.sort(key=lambda x: (-x[0], x[1].get("label") or ""))
    return [x for _, x in scored[:limit]]
