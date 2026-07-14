"""Shared memory store helpers (search, scoring, parsing)."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from datetime import UTC, datetime

from jarvis import llm

MEMORY_TYPES = (
    "fact",
    "auto",
    "note",
    "preference",
    "project",
    "failure",
    "success",
    "strategy",
    "teaching",
)
DEFAULT_NAMESPACE = "default"

# User-facing classes for normal recall/search/summary. Diagnostic types stay out
# of everyday answers (strategies/telemetry only in diagnostics paths).
USER_FACING_TYPES = frozenset({"fact", "preference", "note", "project", "teaching"})
DIAGNOSTIC_TYPES = frozenset({"strategy", "failure", "success", "auto"})
_DIAGNOSTIC_TAGS = frozenset(
    {
        "tool-outcome",
        "telemetry",
        "trust",
        "coding",
        "conversation-summary",
        "checkpoint",
        "fix-verified",
        "auto-correction",
        "superseded",
    }
)
_JOURNAL_TAGS = frozenset(
    {
        "journal",
        "journal-learn",
        "bullet-journal",
        "journal-learned",
    }
)
_JOURNAL_CONTENT = re.compile(r"^from bullet journal\b|^from journal\b", re.I)
_TOPIC_HINT = re.compile(
    r"\b("
    r"favorite\s+(?:coffee|colou?r|tea|food|movie|book|song|drink)|"
    r"(?:coffee|colou?r|tea)\s+preference|"
    r"dog'?s?\s+name|my\s+dog|"
    r"preferred?\s+\w+|communication\s+style|documentation\s+preference|"
    r"decision\s+style"
    r")\b",
    re.I,
)
_QUERY_FILLER = re.compile(
    r"^(?:please\s+)?"
    r"(?:what\s+is\s+my|what'?s\s+my|do\s+you\s+remember\s+my|"
    r"what\s+do\s+you\s+know\s+about|"
    r"search\s+(?:my\s+)?memory(?:\s+for)?|find\s+in\s+memory|"
    r"memory\s+search(?:\s+for)?|tell\s+me\s+(?:about\s+)?my)\s+",
    re.I,
)
_FORGET_STOPWORDS = frozenset(
    {
        "my",
        "the",
        "a",
        "an",
        "please",
        "forget",
        "delete",
        "remove",
        "that",
        "about",
        "memory",
        "memories",
        "preference",
        "preferences",
        "fact",
        "facts",
        "note",
        "notes",
        "entry",
        "entries",
        "info",
        "information",
        "favorite",
        "favourite",
        "update",
        "change",
        "correct",
        "fix",
    }
)


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def parse_ts(ts: str) -> datetime:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return datetime.now(UTC)


def to_public(entry: dict) -> dict:
    return {k: v for k, v in entry.items() if k != "embedding"}


def is_user_facing_entry(entry: dict) -> bool:
    """True for facts/preferences/notes meant for everyday recall."""
    etype = str(entry.get("type") or "")
    if etype in DIAGNOSTIC_TYPES:
        return False
    if etype not in USER_FACING_TYPES:
        return False
    tags = {str(t).lower() for t in (entry.get("tags") or [])}
    if tags & _DIAGNOSTIC_TAGS:
        return False
    if "superseded" in tags:
        return False
    ns = str(entry.get("namespace") or "").lower()
    if ns in ("tools", "jarvis") and etype == "strategy":
        return False
    return True


def is_journal_entry(entry: dict) -> bool:
    tags = {str(t).lower() for t in (entry.get("tags") or [])}
    if tags & _JOURNAL_TAGS:
        return True
    ns = str(entry.get("namespace") or "").lower()
    if ns in ("journal", "journal-learned") or ns.startswith("journal"):
        return True
    return bool(_JOURNAL_CONTENT.search(entry.get("content") or ""))


def derive_topic_hint(text: str) -> str:
    """Extract a stable topic key so updates supersede prior facts on the same concept."""
    raw = (text or "").strip()
    if not raw:
        return ""
    m = _TOPIC_HINT.search(raw)
    if m:
        return m.group(1).lower().strip()
    # Fallback: distinctive tokens after stripping common verbs/stopwords.
    cleaned = re.sub(
        r"^(?:actually,?\s*)?(?:please\s+)?(?:update|change|correct|fix|remember(?:\s+that)?)\s+",
        "",
        raw,
        flags=re.I,
    )
    cleaned = re.sub(r"\b(?:is|now|to|the|a|an|my)\b", " ", cleaned, flags=re.I)
    tokens = [w for w in re.split(r"\W+", cleaned.lower()) if len(w) > 2 and w not in _FORGET_STOPWORDS]
    return " ".join(tokens[:3]).strip()


def filter_user_facing(entries: list[dict]) -> list[dict]:
    return [e for e in entries if is_user_facing_entry(e)]


def normalize_memory_query(query: str) -> str:
    """Strip interrogative / search wrappers so ranking keys on the topic."""
    text = (query or "").strip()
    text = _QUERY_FILLER.sub("", text, count=1).strip()
    text = re.sub(r"[?\s]+$", "", text).strip()
    return text or (query or "").strip()


def type_rank_boost(entry: dict) -> float:
    """Semantic priority: user facts/preferences first; journal/telemetry last."""
    if is_journal_entry(entry):
        return 0.45
    etype = str(entry.get("type") or "")
    if etype == "preference":
        return 1.25
    if etype == "fact":
        return 1.15
    if etype in ("note", "teaching", "project"):
        return 1.05
    if etype == "auto":
        return 0.35
    if etype in ("strategy", "failure", "success"):
        return 0.2
    return 1.0


def relevance_score(entry: dict) -> float:
    base = float(entry.get("relevance", 1.0))
    age_days = max(0, (datetime.now(UTC) - parse_ts(entry.get("timestamp", ""))).days)
    decay = max(0.25, 1.0 - age_days * 0.008)
    access_boost = min(0.4, int(entry.get("access_count", 0)) * 0.04)
    type_penalty = 0.85 if entry.get("type") == "auto" else 1.0
    return (base * decay + access_boost) * type_penalty * type_rank_boost(entry)


def keyword_score(entry: dict, query_lower: str) -> float:
    content = entry.get("content", "").lower()
    tags = " ".join(entry.get("tags") or []).lower()
    if query_lower in content:
        return 3.0 + content.count(query_lower) * 0.1
    words = [w for w in re.split(r"\W+", query_lower) if len(w) > 2]
    if words and all(w in content or w in tags for w in words):
        return 2.0
    if any(query_lower in t.lower() for t in entry.get("tags", [])):
        return 1.5
    return 0.0


def forget_match_score(entry: dict, query: str) -> float:
    """Precise topic match for delete — 'coffee' must not hit 'color'."""
    if not is_user_facing_entry(entry):
        return 0.0
    q = normalize_memory_query(query).lower().strip()
    if not q:
        return 0.0
    content = entry.get("content", "").lower()
    if q in content:
        return 10.0 + keyword_score(entry, q)
    tokens = [w for w in re.split(r"\W+", q) if len(w) > 2 and w not in _FORGET_STOPWORDS]
    if not tokens:
        # Vague query with only stopwords — require full-phrase keyword hit.
        return keyword_score(entry, q) if keyword_score(entry, q) >= 3.0 else 0.0
    hits = [t for t in tokens if t in content]
    if not hits:
        return 0.0
    # Require every distinctive token (coffee, not just "favorite").
    if len(hits) < len(tokens):
        return 0.0
    return 5.0 + len(hits) + keyword_score(entry, q)


def select_forget_targets(entries: list[dict], query: str, *, limit: int = 3) -> list[dict]:
    scored = [(forget_match_score(e, query), e) for e in entries]
    scored = [(s, e) for s, e in scored if s >= 5.0]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [e for _, e in scored[:limit]]


def format_recall_answer(entry: dict) -> str:
    """Turn a stored fact into a spoken answer (not a search dump)."""
    text = (entry.get("content") or "").strip()
    if not text:
        return ""
    rewritten = re.sub(r"^(?:remember(?:\s+that)?\s+)?", "", text, flags=re.I).strip()
    rewritten = re.sub(r"^(?:My|my)\b", "Your", rewritten)
    rewritten = re.sub(r"^(?:I|i)\b", "You", rewritten)
    if rewritten and rewritten[-1] not in ".!?":
        rewritten += "."
    return rewritten


_FACT_QUESTION = re.compile(
    r"\bwhat\s+is\s+my\b|\bwhat'?s\s+my\b|\bdo\s+you\s+remember\s+my\b|"
    r"\bwhat\s+do\s+you\s+know\s+about\s+(?!me\b)",
    re.I,
)
_PREFERENCE_SUMMARY = re.compile(
    r"\b(?:what\s+)?preferences?\b|\bwhat\s+do\s+you\s+know\s+about\s+my\s+preferences\b",
    re.I,
)


def is_fact_question(query: str) -> bool:
    return bool(_FACT_QUESTION.search(query or ""))


def is_preference_summary_query(query: str) -> bool:
    return bool(_PREFERENCE_SUMMARY.search(query or ""))


def normalize_entry(entry: dict, index: int = 0) -> dict:
    entry.setdefault("id", f"m{index}")
    entry.setdefault("namespace", DEFAULT_NAMESPACE)
    if isinstance(entry.get("tags"), str):
        try:
            entry["tags"] = json.loads(entry["tags"])
        except json.JSONDecodeError:
            entry["tags"] = []
    entry.setdefault("tags", [])
    entry.setdefault("access_count", 0)
    entry.setdefault("relevance", 1.0)
    entry.setdefault("timestamp", utc_now())
    if entry.get("type") not in MEMORY_TYPES:
        entry["type"] = "note"
    return entry


def search_pool(
    pool: list[dict],
    query: str,
    limit: int,
    *,
    namespace: str | None,
    get_embedding: Callable[[dict], list[float]],
    set_embedding: Callable[[dict, list[float]], None],
    touch: Callable[[str], None],
    flush_touches: Callable[[], None],
    user_facing_only: bool = False,
) -> list[dict]:
    query_lower = normalize_memory_query(query).lower().strip() or query.lower().strip()
    if namespace:
        pool = [e for e in pool if e.get("namespace") == namespace]
    if user_facing_only:
        pool = filter_user_facing(pool)

    keyword_matches = [e for e in pool if keyword_score(e, query_lower) > 0]
    if keyword_matches:
        ranked = sorted(
            keyword_matches,
            key=lambda e: (
                keyword_score(e, query_lower) * (0.4 if is_journal_entry(e) else 1.0),
                relevance_score(e) * (0.5 if is_journal_entry(e) else 1.0),
                -len(e.get("content") or ""),
            ),
            reverse=True,
        )
        results = ranked[:limit]
        for e in results:
            touch(e["id"])
        flush_touches()
        return [to_public(e) for e in results]

    if not llm.embed_available():
        return []

    query_emb = llm.embed_text(query_lower or query)
    if not query_emb:
        return []

    scored: list[tuple[float, dict]] = []
    for e in pool:
        emb = get_embedding(e)
        if not emb:
            emb = llm.embed_text(e["content"])
            set_embedding(e, emb)
        sim = llm.cosine_similarity(query_emb, emb)
        if sim > 0.3:
            scored.append((sim * relevance_score(e), e))
    scored.sort(key=lambda x: x[0], reverse=True)
    results = [e for _, e in scored[:limit]]
    for e in results:
        touch(e["id"])
    flush_touches()
    return [to_public(e) for e in results]


def parse_remember(text: str) -> tuple[str, str, str | None]:
    text = (text or "").replace("\r\n", "\n").strip()
    lower = text.lower()
    namespace = None
    if m := re.search(r"\b(?:in|for)\s+(?:namespace|project)\s+[`'\"]?(\w[\w-]*)[`'\"]?", lower):
        namespace = m.group(1)
        text = re.sub(
            r"\b(?:in|for)\s+(?:namespace|project)\s+[`'\"]?\w[\w-]*[`'\"]?\s*",
            "",
            text,
            flags=re.I,
        )
    for prefix in (
        r"^(please\s+)?(remember|don't forget|note that|keep in mind)\s*(that\s+)?",
        r"^(these|the following)\s+facts?\s*:?\s*",
        r"^facts?\s*:?\s*",
    ):
        text = re.sub(prefix, "", text, flags=re.I).strip()
    entry_type = "fact"
    if re.search(r"\b(preference|prefer|favorite|favourite)\b", lower):
        entry_type = "preference"
    elif re.search(r"\b(project|codename)\b", lower):
        entry_type = "project"
    return text.strip(), entry_type, namespace


def split_remember_facts(content: str) -> list[str]:
    text = (content or "").replace("\r\n", "\n").strip()
    if not text:
        return []
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    skip = re.compile(
        r"^(do not summarize|just reply|reply with|no summary|stored\.?)\b",
        re.I,
    )
    lines = [ln for ln in lines if not skip.search(ln)]
    if len(lines) >= 2:
        return lines
    return [text] if text else []
