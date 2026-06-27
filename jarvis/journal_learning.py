"""Learn durable facts from bullet and project journal pages."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from jarvis import llm
from jarvis.memory_context import normalize_journal_memory_text

log = logging.getLogger("jarvis.journal_learning")

JOURNAL_LEARN_NAMESPACE = "journal-learned"
JOURNAL_LEARN_TAG = "journal-learn"
_MAX_CHARS = int(os.getenv("JARVIS_JOURNAL_LEARN_CHARS", "10000"))
_MAX_FACTS = int(os.getenv("JARVIS_JOURNAL_LEARN_FACTS", "8"))

_LEARN_JOURNAL = re.compile(
    r"\b(learn from (?:today'?s? |my )?journal|remember (?:from )?(?:today'?s? )?journal|"
    r"journal learn|learn from project journal)\b",
    re.I,
)
_LEARN_PROJECT = re.compile(
    r"\blearn from\s+([\w-]+)\s+(?:project\s+)?journal\b",
    re.I,
)
_RECALL = re.compile(
    r"\b(what did (?:i|we) (?:log|write) in (?:the )?journal|journal (?:learning )?recall|"
    r"what did i learn from (?:the )?journal)\b",
    re.I,
)
_RECALL_QUERY = re.compile(
    r"(?:what did (?:i|we) (?:log|write) in (?:the )?journal(?: about)?|"
    r"journal (?:learning )?recall(?: about)?|what did i learn from (?:the )?journal(?: about)?)\s+(.+)$",
    re.I,
)


def is_journal_learn(message: str) -> bool:
    return bool(_LEARN_JOURNAL.search((message or "").strip()) or _LEARN_PROJECT.search((message or "").strip()))


def is_journal_learn_recall(message: str) -> bool:
    return bool(_RECALL.search((message or "").strip()))


def parse_journal_learn_recall_query(message: str) -> str:
    m = _RECALL_QUERY.search((message or "").strip())
    return (m.group(1).strip() if m else "").rstrip("?.!")


def extract_journal_learnings(
    text: str,
    *,
    project: str = "",
    day: str = "",
    max_facts: int | None = None,
) -> list[str]:
    excerpt = (text or "").strip()
    if not excerpt:
        return []
    if len(excerpt) > _MAX_CHARS:
        excerpt = excerpt[-_MAX_CHARS:]
    limit = max_facts if max_facts is not None else _MAX_FACTS
    label = f"{project} journal {day}".strip() or "journal"
    prompt = (
        f"Extract up to {limit} durable facts, decisions, or lessons from this project daily journal. "
        "Each item must be a complete sentence useful later (tasks done, blockers, decisions, specs). "
        "Skip weather, quotes, and empty platitudes. "
        'Return JSON only: {"facts": ["fact1"]}. Empty array if nothing substantive.\n\n'
        f"Source: {label}\n\n{excerpt}"
    )
    try:
        raw = llm.ask(llm.general_model(), [{"role": "user", "content": prompt}])
        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```\w*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        data = json.loads(raw)
        facts = [f.strip() for f in data.get("facts", []) if isinstance(f, str) and len(f.strip()) > 8]
        return facts[:limit]
    except Exception as exc:
        log.warning("Journal learning extract failed: %s", exc)
        return []


def _store_learnings(
    memory,
    facts: list[str],
    *,
    project: str,
    day: str,
    namespace: str | None = None,
) -> list[str]:
    ns = (namespace or project or JOURNAL_LEARN_NAMESPACE).strip() or JOURNAL_LEARN_NAMESPACE
    if ns == "default":
        ns = JOURNAL_LEARN_NAMESPACE
    location = f"project:{project}:daily:{day}" if project else f"daily:{day}"
    stored: list[str] = []
    proj_tag = f"project:{project[:32]}" if project else "project:main"
    for fact in facts:
        body = fact.strip()
        if not body:
            continue
        normalized = normalize_journal_memory_text(
            f"From bullet journal ({location}): {body}",
        )
        try:
            memory.add(
                "fact",
                normalized,
                tags=[JOURNAL_LEARN_TAG, proj_tag, f"journal-day:{day}"],
                namespace=ns,
            )
            memory.add(
                "note",
                normalized,
                tags=[JOURNAL_LEARN_TAG, proj_tag],
                namespace=ns,
            )
            stored.append(normalized)
        except ValueError as exc:
            log.debug("Skip journal learning: %s", exc)
    return stored


def learn_from_text(
    memory,
    text: str,
    *,
    project: str = "",
    day: str = "",
    namespace: str | None = None,
) -> dict[str, Any]:
    facts = extract_journal_learnings(text, project=project, day=day)
    if not facts:
        return {"ok": False, "message": "Nothing substantive to learn from that journal page.", "facts": []}
    stored = _store_learnings(memory, facts, project=project, day=day, namespace=namespace)
    return {
        "ok": True,
        "message": f"Learned **{len(stored)}** item(s) from journal.",
        "facts": stored,
        "project": project,
        "day": day,
    }


def learn_from_project_journal(
    memory,
    project: str,
    *,
    day: str | None = None,
    namespace: str | None = None,
) -> dict[str, Any]:
    from jarvis.project_journal import ProjectJournal

    store = ProjectJournal(project)
    d = day or __import__("jarvis.modules.journal", fromlist=["_today"])._today()
    text = store.page_text(d)
    if not text.strip() or text.count("\n") < 1:
        bullets = store.daily_get(d).get("bullets") or []
        if not bullets and not (store.daily_get(d).get("notes") or "").strip():
            return {"ok": False, "message": f"No journal entries for **{store.slug}** on {d}.", "facts": []}
    result = learn_from_text(memory, text, project=store.slug, day=d, namespace=namespace)
    if result.get("ok"):
        store.daily_mark_learned(d)
    return result


def learn_from_main_journal(memory, *, day: str | None = None, namespace: str | None = None) -> dict[str, Any]:
    from jarvis.modules.journal import BulletJournal, _format_bullet, _today

    journal = BulletJournal()
    d = day or _today()
    page = journal.daily_get(d, enrich=False)
    parts = [f"Main bullet journal — {d}"]
    for b in page.get("bullets") or []:
        parts.append(_format_bullet(b))
    for line in page.get("gratitude") or []:
        if line:
            parts.append(f"Gratitude: {line}")
    prompts = page.get("prompts") or {}
    if prompts.get("morning"):
        parts.append(f"Morning: {prompts['morning']}")
    if prompts.get("evening"):
        parts.append(f"Evening: {prompts['evening']}")
    text = "\n".join(parts)
    return learn_from_text(memory, text, project="main", day=d, namespace=namespace or JOURNAL_LEARN_NAMESPACE)


def list_journal_learnings(memory, *, query: str = "", project: str = "", limit: int = 25) -> list[dict]:
    entries = memory.list_entries(namespace=JOURNAL_LEARN_NAMESPACE)
    if project:
        tag = f"project:{project[:32]}"
        entries = [e for e in entries if tag in (e.get("tags") or [])]
    entries = [e for e in entries if JOURNAL_LEARN_TAG in (e.get("tags") or [])]
    if not entries:
        entries = [e for e in memory.list_entries() if JOURNAL_LEARN_TAG in (e.get("tags") or [])]
    if project:
        tag = f"project:{project[:32]}"
        entries = [e for e in entries if tag in (e.get("tags") or [])]
    if query:
        q = query.lower()
        entries = [e for e in entries if q in e.get("content", "").lower()]
    entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return entries[:limit]


def journal_learning_context_for_chat(memory, message: str, *, limit: int = 4) -> str:
    from jarvis.trust_memory import filter_trusted_content

    q = (message or "").strip()
    if len(q) < 6:
        return ""
    hits = list_journal_learnings(memory, query=q, limit=limit)
    if not hits:
        words = [w for w in re.findall(r"[a-z]{4,}", q.lower())]
        stop = {"what", "when", "where", "journal", "today", "about", "this", "that", "from"}
        words = [w for w in words if w not in stop][:6]
        if words:
            pool = list_journal_learnings(memory, limit=40)
            hits = [e for e in pool if any(w in e.get("content", "").lower() for w in words)][:limit]
    if not hits:
        return ""
    lines = []
    for e in hits:
        line = filter_trusted_content(e.get("content", ""))
        if line:
            lines.append(f"- {line}")
    if not lines:
        return ""
    return "Relevant journal learnings:\n" + "\n".join(lines)


def format_learnings_markdown(entries: list[dict]) -> str:
    if not entries:
        return "_No journal learnings stored yet._"
    return "\n".join(f"• {e.get('content', '')}" for e in entries)
