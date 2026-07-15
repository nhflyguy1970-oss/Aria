"""Experience memory — durable successes and failures for learning from outcomes."""

from __future__ import annotations

import re

from jarvis import llm

EXPERIENCE_NAMESPACE = "experience"
EXPERIENCE_TYPES = ("success", "failure")

_TASK_HINTS = re.compile(
    r"\b(fix|debug|implement|refactor|test|pytest|error|failed|worked|approach|"
    r"image|comfy|generate|coding|script|module|tool)\b",
    re.I,
)

_SUCCESS_REMEMBER = re.compile(
    r"^(?:please\s+)?(?:remember\s+)?(?:that\s+)?(?:this|that)\s+worked\s*(?::|-)?\s*(.*)$",
    re.I | re.S,
)
_FAILURE_REMEMBER = re.compile(
    r"^(?:please\s+)?(?:remember\s+)?(?:that\s+)?(?:this|that)\s+failed\s*(?::|-)?\s*(.*)$",
    re.I | re.S,
)
_SUCCESS_PREFIX = re.compile(r"^(?:remember\s+)?success\s*:\s*", re.I)
_FAILURE_PREFIX = re.compile(r"^(?:remember\s+)?failure\s*:\s*", re.I)

_RECALL_QUERY = re.compile(
    r"^(?:please\s+)?(?:what|show|list|recall)\s+"
    r"(?:(?:past|previous)\s+)?"
    r"(?:(?:experiences?|outcomes?)\s+)?"
    r"(?:for|about|with|on)\s+(.+)$"
    r"|^(?:please\s+)?(?:what worked|what failed|past failures|past successes)\s*(?:for|with|on)?\s*(.*)$",
    re.I,
)


def _format_content(
    *,
    outcome: str,
    task: str = "",
    detail: str = "",
    module: str = "",
    context: str = "",
) -> str:
    label = "Succeeded" if outcome == "success" else "Failed"
    parts: list[str] = []
    if module:
        parts.append(f"[{module}]")
    if task:
        parts.append(task.strip()[:160])
    body = detail.strip()[:500] or task.strip()[:500] or "unspecified"
    if context:
        parts.append(f"({context.strip()[:120]})")
    head = " ".join(parts).strip()
    if head:
        return f"{label}: {head} — {body}"
    return f"{label}: {body}"


def record_experience(
    store,
    *,
    outcome: str,
    task: str = "",
    detail: str = "",
    module: str = "",
    context: str = "",
    namespace: str = EXPERIENCE_NAMESPACE,
    tags: list[str] | None = None,
) -> dict | None:
    """Store a success or failure experience (ACM client when PRIMARY — M4c)."""
    outcome = outcome if outcome in EXPERIENCE_TYPES else "failure"
    content = _format_content(
        outcome=outcome,
        task=task,
        detail=detail,
        module=module,
        context=context,
    )
    entry_tags = ["experience", f"outcome-{outcome}"]
    if module:
        entry_tags.append(module)
    if tags:
        entry_tags.extend(tags)
    try:
        from aria_core import acm_bridge

        if acm_bridge.acm_is_authoritative():
            return acm_bridge.primary_remember(
                content,
                entry_type=outcome if outcome in ("success", "failure") else "fact",
                tags=entry_tags,
                namespace=namespace,
            )
    except Exception:
        pass
    if hasattr(store, "similar_exists") and store.similar_exists(content):
        return None
    return store.add(outcome, content, tags=entry_tags, namespace=namespace)


def record_failure(
    store,
    *,
    path: str = "",
    error: str = "",
    task: str = "",
    namespace: str | None = None,
) -> dict | None:
    excerpt = (error or "").strip()[:500]
    if not excerpt and not path:
        return None
    return record_experience(
        store,
        outcome="failure",
        task=task,
        detail=excerpt or "unknown error",
        module="coding",
        context=path,
        namespace=namespace or EXPERIENCE_NAMESPACE,
        tags=["coding"],
    )


def record_success(
    store,
    *,
    paths: list[str] | None = None,
    task: str = "",
    detail: str = "",
    module: str = "coding",
    note: str = "",
    namespace: str | None = None,
) -> dict | None:
    context = ""
    if paths:
        context = ", ".join(f"`{p}`" for p in paths[:4])
    body = detail or note
    if not body and context:
        body = f"verified for {context}"
    if not body and not task:
        return None
    return record_experience(
        store,
        outcome="success",
        task=task,
        detail=body,
        module=module,
        context=context,
        namespace=namespace or EXPERIENCE_NAMESPACE,
        tags=["coding"] if module == "coding" else [],
    )


def record_tool_outcome(
    store,
    *,
    action: str,
    detail: str = "",
    ok: bool = True,
    namespace: str = EXPERIENCE_NAMESPACE,
) -> dict | None:
    if not ok or not action:
        return None
    snippet = (detail or action)[:120]
    return record_experience(
        store,
        outcome="success",
        task=action,
        detail=snippet,
        module="tool",
        namespace=namespace,
        tags=["tool-outcome", action],
    )


def parse_experience_remember(text: str) -> tuple[str, str] | None:
    """Parse user phrases → (outcome, detail)."""
    raw = (text or "").strip()
    if not raw:
        return None
    m = _SUCCESS_REMEMBER.match(raw)
    if m:
        return "success", (m.group(1) or "user noted this worked").strip()
    m = _FAILURE_REMEMBER.match(raw)
    if m:
        return "failure", (m.group(1) or "user noted this failed").strip()
    if _SUCCESS_PREFIX.match(raw):
        return "success", _SUCCESS_PREFIX.sub("", raw, count=1).strip()
    if _FAILURE_PREFIX.match(raw):
        return "failure", _FAILURE_PREFIX.sub("", raw, count=1).strip()
    return None


def parse_experience_recall_query(message: str) -> str:
    m = _RECALL_QUERY.match((message or "").strip())
    if not m:
        return ""
    return (m.group(1) or m.group(2) or "").strip()


def list_experiences(
    store,
    *,
    outcome: str | None = None,
    limit: int = 20,
) -> list[dict]:
    from jarvis.trust_memory import filter_entry_list

    types = [outcome] if outcome in EXPERIENCE_TYPES else list(EXPERIENCE_TYPES)
    entries: list[dict] = []
    seen: set[str] = set()
    for entry_type in types:
        for e in store.list_entries(entry_type=entry_type, namespace=EXPERIENCE_NAMESPACE):
            if e.get("id") not in seen:
                seen.add(e["id"])
                entries.append(e)
        for e in store.list_entries(entry_type=entry_type, namespace="jarvis"):
            if e.get("id") not in seen:
                seen.add(e["id"])
                entries.append(e)
    entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return filter_entry_list(entries[:limit])


def recall_experiences(store, query: str, *, limit: int = 8) -> list[dict]:
    from jarvis.trust_memory import filter_entry_list

    q = (query or "").strip()
    if not q:
        return list_experiences(store, limit=limit)
    hits: list[dict] = []
    seen: set[str] = set()
    if llm.embed_available():
        for ns in (EXPERIENCE_NAMESPACE, "jarvis", None):
            for e in store.search(q, limit=limit, namespace=ns):
                if e.get("type") not in EXPERIENCE_TYPES or e.get("id") in seen:
                    continue
                seen.add(e["id"])
                hits.append(e)
    if not hits:
        ql = q.lower()
        for e in list_experiences(store, limit=limit * 3):
            if ql in e.get("content", "").lower():
                hits.append(e)
    return filter_entry_list(hits[:limit])


def experience_stats(store) -> dict:
    successes = list_experiences(store, outcome="success", limit=500)
    failures = list_experiences(store, outcome="failure", limit=500)
    return {
        "successes": len(successes),
        "failures": len(failures),
        "namespace": EXPERIENCE_NAMESPACE,
    }


def experience_context_for_chat(store, message: str, *, limit: int = 4) -> str:
    """Inject relevant past successes/failures when the user is doing similar work."""
    from jarvis.trust_memory import filter_trusted_content

    text = (message or "").strip()
    if len(text) < 8 or not _TASK_HINTS.search(text):
        return ""

    hits = recall_experiences(store, text, limit=limit)
    if not hits:
        return ""

    lines: list[str] = []
    for e in hits:
        line = filter_trusted_content(e.get("content", ""))
        if line:
            lines.append(f"- [{e.get('type', 'experience')}] {line}")
    if not lines:
        return ""
    return "Past experiences (learn from these — do not repeat failures):\n" + "\n".join(lines)
