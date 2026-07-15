"""Trust layer: failure/strategy memory, test-artifact filtering, memory correction."""

from __future__ import annotations

import re

from jarvis import llm
from jarvis.memory_context import should_inject_resume_context

TRUST_MEMORY_TYPES = ("failure", "strategy")

# Known pytest / dev scratch content — never inject into general chat or system prompt.
_TEST_ARTIFACT_RE = re.compile(
    r"broken_calc\.py|"
    r"\bbuy milk\b|"
    r"pytest journal scratch|"
    r"\btest unique xyz\b|"
    r"\blive test codename is Falcon\b|"
    r"\bmy test codename is Phoenix\b",
    re.I,
)

_CHECKPOINT_TEST_TASK = re.compile(
    r"debug until tests pass for data/scripts/broken_calc",
    re.I,
)

_TEST_PATH_RE = re.compile(r"broken_calc\.py|pytest_journal_scratch", re.I)

_DATA_LAYOUT_HINT = (
    "Data layout: `jarvis/` = app code; `data/` = your live files (memory, journal, chat, uploads); "
    "`tests/` and pytest must never write to `data/`."
)

_STRATEGY_PREFIX = re.compile(
    r"^(?:remember\s+)?(?:strategy|rule|behavior)\s*:\s*",
    re.I,
)

_CORRECT_PATTERNS = (
    re.compile(
        r"^(?:please\s+)?(?:correct|update|fix)\s+(?:that|the fact|memory|my memory)\s*(?:to\s+)?(?:that\s+)?(.+)$",
        re.I,
    ),
    re.compile(
        r"^(?:please\s+)?(?:actually,?\s+)(.+)$",
        re.I,
    ),
    re.compile(
        r"^(?:the\s+)?correct(?:ion)?\s+is\s*(?:that\s+)?(.+)$",
        re.I,
    ),
)


def is_test_artifact(content: str) -> bool:
    text = (content or "").strip()
    if not text:
        return False
    return bool(_TEST_ARTIFACT_RE.search(text))


def should_skip_checkpoint_in_prompt(content: str) -> bool:
    """Drop auto-saved checkpoints that only reference old test tasks."""
    text = (content or "").strip()
    if not text or "Auto-saved on exit" not in text:
        return False
    return bool(_CHECKPOINT_TEST_TASK.search(text))


def filter_trusted_content(content: str) -> str | None:
    """Return content for prompts, or None if it should not be injected."""
    text = (content or "").strip()
    if not text:
        return None
    if is_test_artifact(text):
        return None
    if should_skip_checkpoint_in_prompt(text):
        return None
    return text


def parse_memory_correct(message: str) -> tuple[str, str] | None:
    """Parse 'correct that X is Y' style messages → (search_hint, new_fact)."""
    text = (message or "").strip()
    if not text:
        return None
    for pat in _CORRECT_PATTERNS:
        m = pat.match(text)
        if m:
            new_fact = m.group(1).strip().rstrip(".")
            if len(new_fact) >= 4:
                return ("", new_fact)
    m = re.search(
        r"\b(?:correct|update|fix)\s+(?:memory\s+about\s+|that\s+)?(.+?)\s+"
        r"(?:to|is now|should be)\s+(.+)$",
        text,
        re.I,
    )
    if m:
        return (m.group(1).strip(), m.group(2).strip().rstrip("."))
    return None


def parse_strategy_remember(text: str) -> str | None:
    t = (text or "").strip()
    if not _STRATEGY_PREFIX.search(t):
        return None
    cleaned = _STRATEGY_PREFIX.sub("", t, count=1).strip()
    return cleaned if len(cleaned) >= 8 else None


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
    parts = []
    if task:
        parts.append(f"Task: {task[:160]}")
    if path:
        parts.append(f"File: `{path}`")
    parts.append(f"Failed: {excerpt or 'unknown error'}")
    content = " | ".join(parts)
    ns = namespace or "jarvis"
    try:
        from aria_core import acm_bridge

        if acm_bridge.acm_is_authoritative():
            return acm_bridge.primary_remember(
                content, entry_type="failure", tags=["coding"], namespace=ns
            )
    except Exception:
        pass
    if store.similar_exists(content):
        return None
    return store.add("failure", content, tags=["coding"], namespace=ns)


def record_fix_success(
    store,
    *,
    paths: list[str],
    note: str = "",
    namespace: str | None = None,
) -> dict | None:
    if not paths:
        return None
    rel = ", ".join(f"`{p}`" for p in paths[:4])
    content = f"Fix verified for {rel}."
    if note:
        content += f" {note[:200]}"
    ns = namespace or "jarvis"
    try:
        from aria_core import acm_bridge

        if acm_bridge.acm_is_authoritative():
            return acm_bridge.primary_remember(
                content, entry_type="fact", tags=["coding", "fix-verified"], namespace=ns
            )
    except Exception:
        pass
    if store.similar_exists(content):
        return None
    return store.add("fact", content, tags=["coding", "fix-verified"], namespace=ns)


def record_strategy(
    store,
    rule: str,
    *,
    namespace: str = "jarvis",
    source: str = "user",
) -> dict:
    content = rule.strip()
    if not content:
        raise ValueError("Empty strategy rule")
    tags = ["trust", source]
    try:
        from aria_core import acm_bridge

        if acm_bridge.acm_is_authoritative():
            return acm_bridge.primary_remember(
                content, entry_type="strategy", tags=tags, namespace=namespace
            )
    except Exception:
        pass
    for e in store.list_entries(entry_type="strategy", namespace=namespace):
        if e["content"].lower() == content.lower():
            return e
    return store.add("strategy", content, tags=tags, namespace=namespace)


def correct_memory(store, new_fact: str, *, search_hint: str = "") -> tuple[int, dict | None, bool]:
    """Replace matching memories with a corrected fact. Returns (removed_count, new_entry)."""
    from jarvis.modules.memory_common import derive_topic_hint, select_forget_targets

    new_fact = new_fact.strip()
    if not new_fact:
        return 0, None

    hint = (search_hint or "").strip() or derive_topic_hint(new_fact)
    removed = 0
    superseded_ids: list[str] = []
    if hint:
        targets = select_forget_targets(store.list_entries(), hint, limit=5)
        for e in targets:
            tags = list(e.get("tags") or [])
            if "superseded" not in tags:
                tags.append("superseded")
            updated = False
            try:
                if hasattr(store, "update"):
                    updated = bool(store.update(e["id"], tags=tags))
            except Exception:
                updated = False
            if updated:
                superseded_ids.append(e["id"])
                removed += 1
            elif store.delete_id(e["id"]):
                superseded_ids.append(e["id"])
                removed += 1
    else:
        key = _topic_key(new_fact)
        if key:
            for e in select_forget_targets(store.list_entries(), key, limit=5):
                if store.delete_id(e["id"]):
                    removed += 1
                    superseded_ids.append(e["id"])

    entry_type = (
        "preference" if re.search(r"\b(prefer|favorite|favourite)\b", new_fact, re.I) else "fact"
    )
    if parse_strategy_remember(new_fact):
        entry_type = "strategy"
        new_fact = parse_strategy_remember(new_fact) or new_fact

    new_entry = store.add(
        entry_type,
        new_fact,
        tags=["active", f"topic:{hint}"] if hint else ["active"],
    )

    try:
        from aria_core import memory_manager as mm

        mm.record_update_supersede(
            new_id=(new_entry or {}).get("id"),
            superseded_ids=superseded_ids,
            topic=hint,
            removed=removed,
        )
    except Exception:
        pass

    lower = new_fact.lower()
    style_preference = bool(
        re.search(
            r"\b(prefer|always|never|shorter|brief|concise|tone|format|communication|documentation)\b",
            lower,
            re.I,
        )
    ) and not re.search(r"\bfavorite\b", lower, re.I)

    strategy_created = False
    if style_preference:
        strategy_rule = f"When answering, remember: {new_fact.rstrip('.')}"
        if not _similar_strategy_exists(store, strategy_rule):
            store.add("strategy", strategy_rule, tags=["trust", "auto-correction"])
            strategy_created = True
            try:
                from jarvis.events import emit_memory_updated

                emit_memory_updated(action="strategy_created", entry_id=new_entry.get("id"))
            except Exception:
                pass

    return removed, new_entry, strategy_created


def _similar_strategy_exists(store, content: str, threshold: float = 0.88) -> bool:
    """Duplicate check scoped to strategy entries (preference facts must not block)."""
    norm = content.lower().strip()
    if not norm:
        return True
    for e in store.list_entries(entry_type="strategy"):
        if e.get("content", "").lower().strip() == norm:
            return True
        emb = llm.embed_text(content)
        e_emb = e.get("embedding") or []
        if emb and e_emb and llm.cosine_similarity(emb, e_emb) >= threshold:
            return True
    return False


def _topic_key(fact: str) -> str | None:
    from jarvis.modules.memory_common import derive_topic_hint

    hinted = derive_topic_hint(fact)
    if hinted:
        return hinted
    lower = fact.lower()
    for key in ("birthday", "broken_calc", "mom", "mother", "coffee", "color", "zeus"):
        if key in lower:
            return key
    return None


def record_tool_outcome(
    store,
    *,
    action: str,
    detail: str = "",
    ok: bool = True,
    namespace: str = "jarvis",
) -> dict | None:
    """Remember which tools worked for similar future routing."""
    if not ok or not action:
        return None
    snippet = (detail or action)[:120]
    content = f"Tool `{action}` worked for: {snippet}"
    if store.similar_exists(content):
        return None
    return store.add("strategy", content, tags=["tool-outcome", action], namespace=namespace)


def trust_context_for_chat(store, message: str, session=None) -> str:
    """Strategy rules + relevant failures for the current message."""
    lines: list[str] = []

    strategies = store.list_entries(entry_type="strategy")[:6]
    strategy_lines = [e["content"] for e in strategies if filter_trusted_content(e["content"])]
    if strategy_lines:
        lines.append(
            "Behavior rules (always follow):\n" + "\n".join(f"- {s}" for s in strategy_lines)
        )

    coding = should_inject_resume_context(message, session)
    if coding:
        failures = [
            e
            for e in store.list_entries(entry_type="failure")
            if filter_trusted_content(e.get("content", ""))
        ][:4]
        if failures:
            lines.append(
                "Recent coding failures/fixes:\n" + "\n".join(f"- {e['content']}" for e in failures)
            )

    return "\n\n".join(lines)


def is_test_artifact_path(path: str) -> bool:
    return bool(_TEST_PATH_RE.search(path or ""))


def is_trusted_memory_content(content: str) -> bool:
    """True if content is safe to store in live memory."""
    return filter_trusted_content(content) is not None


def scrub_store(store) -> dict:
    """Remove test artifacts and stale checkpoints from memory."""
    removed = 0
    for e in store.list_entries(include_embedding=True):
        content = e.get("content", "")
        if is_test_artifact(content) or should_skip_checkpoint_in_prompt(content):
            if store.delete_id(e["id"]):
                removed += 1
    return {"removed": removed}


def trust_status(store) -> dict:
    strategies = store.list_entries(entry_type="strategy")
    failures = store.list_entries(entry_type="failure")
    artifacts = sum(
        1
        for e in store.list_entries(include_embedding=True)
        if is_test_artifact(e.get("content", ""))
    )
    return {
        "strategies": len(strategies),
        "failures": len(failures),
        "artifact_entries_remaining": artifacts,
        "data_layout": _DATA_LAYOUT_HINT,
    }


def filter_entry_list(entries: list[dict], *, user_facing_only: bool = False) -> list[dict]:
    """Drop test artifacts; optionally keep only everyday user memory classes."""
    from jarvis.modules.memory_common import filter_user_facing

    out = []
    for e in entries:
        if filter_trusted_content(e.get("content", "")):
            out.append(e)
    if user_facing_only:
        out = filter_user_facing(out)
    return out


def data_paths_hint() -> str:
    return _DATA_LAYOUT_HINT


def seed_default_strategies(store) -> int:
    """One-time defaults if none exist — lightweight trust guardrails."""
    defaults = [
        "Never inject stale test files (e.g. broken_calc.py) or pytest scratch data into general chat.",
        "Journal notes with 'today' are dated facts — do not treat past journal 'today' lines as current.",
        "Do not write to the user's live journal or memory during automated tests.",
        _DATA_LAYOUT_HINT,
    ]
    added = 0
    existing = {e["content"].lower() for e in store.list_entries(entry_type="strategy")}
    for rule in defaults:
        if rule.lower() not in existing:
            record_strategy(store, rule, source="default")
            added += 1
    return added
