"""Conversation continuity — "where did we leave off?" from the actual record."""

from __future__ import annotations

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


@register_action(
    "continuity_recall",
    module="memory",
    description="Recall earlier conversations, decisions and unfinished work",
    info=True,
)
def continuity_recall(assistant, params: dict, message: str) -> dict:
    from jarvis import continuity

    query = str(params.get("query") or message or "").strip()
    branches = getattr(assistant, "branches", None)
    result = continuity.retrieve(query, branch=getattr(branches, "active_id", None))
    reply = continuity.answer(result)
    payload = {
        "continuity": result.to_dict(),
        "memory_citations": result.citations(),
    }
    if result.status == continuity.UNAVAILABLE:
        return err(reply, module="memory", error_kind="memory_unavailable", **payload)
    return ok(reply, module="memory", **payload)


@register_action(
    "continuity_status",
    module="memory",
    description="Show conversation-history indexing and ACM ingestion health",
    info=True,
)
def continuity_status(assistant, params: dict, message: str) -> dict:
    from jarvis.continuity import status

    snap = status()
    outbox = snap.get("outbox") or {}
    lines = [
        "**Conversation continuity**",
        f"- Archived turns indexed: {snap.get('episodes', 0)}",
        f"- Continuity records: {sum((snap.get('records') or {}).values())}"
        f" {dict(snap.get('records') or {})}",
        f"- ACM ingestion: {outbox.get('done', 0)} encoded, {outbox.get('pending', 0)} pending,"
        f" {outbox.get('failed', 0)} failed, {outbox.get('skipped', 0)} declined",
        f"- Background sync: {'running' if snap.get('worker_running') else 'not running'}",
    ]
    if snap.get("last_error"):
        lines.append(f"- Last error: {snap['last_error']}")
    return ok("\n".join(lines), module="memory", continuity=snap)
