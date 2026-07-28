"""Compatibility shim: jarvis.knowledge_graph → Connections / intelligence KG.

Memory & Journal associative surfaces call `search()`. Prefer
`jarvis.connections_services` for new code.
"""

from __future__ import annotations

from typing import Any

from jarvis.intelligence.knowledge_graph import (  # noqa: F401
    extract_entities,
    extract_relationships,
    get_store,
    neighbors,
    search_graph,
)
from jarvis.connections_services import search_connections


def search(query: str, *, limit: int = 8) -> list[dict[str, Any]]:
    """Return entity-shaped hits for associative UI (never silent)."""
    result = search_connections(query, limit=limit, mode="entities")
    if not result.get("ok"):
        return []
    out = []
    for n in result.get("nodes") or []:
        out.append(
            {
                "id": n.get("id") or n.get("name"),
                "name": n.get("name"),
                "label": n.get("name"),
                "kind": n.get("kind"),
                "namespace": n.get("namespace"),
                "source": "connections",
                "why": "Connections link — not autobiographical until adopted in Memory.",
            }
        )
    return out
