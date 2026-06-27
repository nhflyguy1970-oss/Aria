"""Explicit teaching — deliberate lessons the user teaches ARIA."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from jarvis import llm

TEACHING_NAMESPACE = "teaching"
EXPLICIT_TEACH_TAG = "explicit-teach"
TEACHING_KINDS = ("fact", "rule", "preference", "procedure", "relationship", "skill")

_TEACH_TYPED = re.compile(
    r"^(?:please\s+)?teach\s+(?:aria|jarvis)?\s*"
    r"(fact|rule|preference|procedure|relationship|skill)\s*:\s*(.+)$",
    re.I | re.S,
)
_TEACH_THAT = re.compile(
    r"^(?:please\s+)?teach\s+(?:aria|jarvis)\s+(?:that\s+)?(.+)$",
    re.I | re.S,
)
_TEACH_BARE = re.compile(
    r"^(?:please\s+)?teach\s+(?:aria|jarvis)?\s+(.+)$",
    re.I | re.S,
)
_RECALL = re.compile(
    r"\b(?:what did i teach|what have i taught|recall (?:my )?teaching|taught you about)\b",
    re.I,
)
_RECALL_QUERY = re.compile(
    r"(?:what did i teach(?: you)?(?: about)?|what have i taught(?: you)?(?: about)?|"
    r"recall (?:my )?teaching(?: about)?|taught you about)\s+(.+)$",
    re.I,
)

_RULE_MARKERS = re.compile(
    r"\b(always|never|must|should not|don't|do not|when answering|when i ask)\b",
    re.I,
)
_PROCEDURE_MARKERS = re.compile(
    r"\b(first|then|step\s*\d|steps?:|to deploy|to fix|to run|how to)\b",
    re.I,
)


@dataclass
class TeachIntent:
    kind: str
    content: str
    raw: str = ""


@dataclass
class TeachResult:
    kind: str
    content: str
    entry: dict | None = None
    mirrors: list[str] | None = None
    namespace: str = TEACHING_NAMESPACE


def _kind_tag(kind: str) -> str:
    k = (kind or "fact").lower()
    return f"teach-{k}" if k in TEACHING_KINDS else "teach-fact"


def _format_lesson(kind: str, content: str) -> str:
    label = kind.capitalize()
    body = (content or "").strip()
    if body.lower().startswith(f"[{kind}]"):
        return body
    return f"[{label}] {body}"


def infer_teaching_kind(content: str) -> str:
    text = (content or "").strip()
    lower = text.lower()
    if _PROCEDURE_MARKERS.search(lower):
        return "procedure"
    if _RULE_MARKERS.search(lower):
        return "rule"
    if re.search(r"\b(prefer|preference|likes? to)\b", lower):
        return "preference"
    if re.search(r"\b(works on|uses|knows|related to|connected to)\b", lower):
        return "relationship"
    if re.search(r"\b(when i|use tool|call action|route to)\b", lower):
        return "skill"
    return "fact"


def parse_teach_message(message: str) -> TeachIntent | None:
    raw = (message or "").strip()
    if not raw:
        return None
    m = _TEACH_TYPED.match(raw)
    if m:
        kind = m.group(1).lower()
        content = m.group(2).strip()
        if content:
            return TeachIntent(kind=kind, content=content, raw=raw)
    m = _TEACH_THAT.match(raw)
    if m:
        content = m.group(1).strip()
        if content:
            return TeachIntent(kind=infer_teaching_kind(content), content=content, raw=raw)
    m = _TEACH_BARE.match(raw)
    if m:
        content = m.group(1).strip()
        if content and not _RECALL.search(content):
            return TeachIntent(kind=infer_teaching_kind(content), content=content, raw=raw)
    return None


def is_teach_recall(message: str) -> bool:
    return bool(_RECALL.search((message or "").strip()))


def parse_teach_recall_query(message: str) -> str:
    m = _RECALL_QUERY.search((message or "").strip())
    return (m.group(1).strip() if m else "").rstrip("?.!")


def _teaching_tags(kind: str) -> list[str]:
    return [EXPLICIT_TEACH_TAG, _kind_tag(kind), "user-taught"]


def apply_explicit_teaching(
    memory,
    intent: TeachIntent,
    *,
    namespace: str | None = None,
) -> TeachResult:
    """Store an explicit lesson and mirror into specialized memory layers."""
    kind = intent.kind if intent.kind in TEACHING_KINDS else "fact"
    content = intent.content.strip()
    ns = (namespace or TEACHING_NAMESPACE).strip() or TEACHING_NAMESPACE
    lesson = _format_lesson(kind, content)
    mirrors: list[str] = []

    entry = memory.add(
        "teaching",
        lesson,
        tags=_teaching_tags(kind),
        namespace=ns,
    )

    if kind == "rule":
        from jarvis.trust_memory import record_strategy

        strat = record_strategy(memory, content, namespace=ns, source="explicit-teach")
        if strat:
            mirrors.append("strategy rule")
    elif kind == "preference":
        memory.add(
            "preference",
            content,
            tags=[EXPLICIT_TEACH_TAG, "teach-preference"],
            namespace=ns,
        )
        mirrors.append("preference")
    elif kind == "fact":
        memory.add(
            "fact",
            content,
            tags=[EXPLICIT_TEACH_TAG, "teach-fact"],
            namespace=ns,
        )
        mirrors.append("fact")
    elif kind == "procedure":
        memory.add(
            "note",
            lesson,
            tags=[EXPLICIT_TEACH_TAG, "teach-procedure"],
            namespace=ns,
        )
        mirrors.append("procedure note")
    elif kind == "relationship":
        from jarvis.relationship_memory import (
            RELATIONSHIP_NAMESPACE,
            parse_relationship_link,
            record_links,
        )

        links = parse_relationship_link(content) or parse_relationship_link(f"link {content}")
        if not links:
            links = parse_relationship_link(f"remember {content}")
        if links:
            record_links(links, namespace=RELATIONSHIP_NAMESPACE)
            mirrors.append("relationship graph")
    elif kind == "skill":
        from jarvis.trust_memory import record_strategy

        rule = content if content.lower().startswith("when ") else f"When relevant: {content}"
        record_strategy(memory, rule, namespace=ns, source="explicit-teach-skill")
        mirrors.append("skill rule")

    return TeachResult(kind=kind, content=lesson, entry=entry, mirrors=mirrors, namespace=ns)


def list_teachings(
    memory,
    *,
    query: str = "",
    kind: str | None = None,
    limit: int = 25,
) -> list[dict]:
    entries = memory.list_entries(entry_type="teaching", namespace=TEACHING_NAMESPACE)
    if not entries:
        entries = [
            e for e in memory.list_entries(entry_type="teaching")
            if EXPLICIT_TEACH_TAG in (e.get("tags") or [])
        ]
    if kind and kind in TEACHING_KINDS:
        tag = _kind_tag(kind)
        entries = [e for e in entries if tag in (e.get("tags") or [])]
    if query:
        q = query.lower()
        entries = [
            e for e in entries
            if q in e.get("content", "").lower()
            or any(q in t.lower() for t in e.get("tags") or [])
        ]
        if llm.embed_available():
            hits = memory.search(query, limit=limit, namespace=TEACHING_NAMESPACE)
            seen = {e["id"] for e in entries}
            for h in hits:
                if h.get("type") == "teaching" and h["id"] not in seen:
                    entries.append(h)
                    seen.add(h["id"])
    entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return entries[:limit]


def teaching_stats(memory) -> dict[str, Any]:
    entries = list_teachings(memory, limit=500)
    by_kind: dict[str, int] = {}
    for e in entries:
        tags = e.get("tags") or []
        kind = next((t.replace("teach-", "") for t in tags if t.startswith("teach-")), "fact")
        by_kind[kind] = by_kind.get(kind, 0) + 1
    return {
        "total": len(entries),
        "namespace": TEACHING_NAMESPACE,
        "by_kind": by_kind,
    }


def explicit_teaching_system_block(memory, *, max_items: int = 8) -> str:
    from jarvis.trust_memory import filter_trusted_content

    entries = list_teachings(memory, limit=max_items)
    lines: list[str] = []
    for e in entries:
        line = filter_trusted_content(e.get("content", ""))
        if line:
            lines.append(f"- {line}")
    if not lines:
        return ""
    return "Explicit teachings (user-taught — follow these):\n" + "\n".join(lines)


def explicit_teaching_context_for_chat(memory, message: str, *, limit: int = 5) -> str:
    from jarvis.trust_memory import filter_trusted_content

    q = (message or "").strip()
    if len(q) < 6:
        return ""
    hits = list_teachings(memory, query=q, limit=limit)
    if not hits:
        return ""
    lines: list[str] = []
    for e in hits:
        line = filter_trusted_content(e.get("content", ""))
        if line:
            lines.append(f"- {line}")
    if not lines:
        return ""
    return "Relevant teachings for this message:\n" + "\n".join(lines)


def format_teachings_markdown(entries: list[dict]) -> str:
    if not entries:
        return "_No explicit teachings stored yet._"
    lines: list[str] = []
    for e in entries:
        tags = e.get("tags") or []
        kind = next((t.replace("teach-", "") for t in tags if t.startswith("teach-")), "fact")
        lines.append(f"• **[{kind}]** {e.get('content', '')}")
    return "\n".join(lines)
