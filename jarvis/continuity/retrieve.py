"""Continuity retrieval — "where did we leave off?" answered from the record.

Recognises continuity questions without trigger words, resolves them against
the continuity index (time windows, topic terms, recency, open work), and
returns a typed result:

  HITS         records were found; every item cites its source episode
  NO_RECORD    the history was searched and holds nothing relevant
  UNAVAILABLE  the history could not be searched — not the same as no record
  PARTIAL      found something, but part of the search failed

The result renders to one bounded, redacted context block. The same block is
what any model backend receives — local or, in future, cloud — so continuity
does not depend on which model answers, and no backend ever receives more
than the retrieved, relevant items.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from jarvis.continuity import store
from jarvis.continuity.classify import key_terms

log = logging.getLogger("jarvis.continuity")

HITS = "HITS"
NO_RECORD = "NO_RECORD"
UNAVAILABLE = "UNAVAILABLE"
PARTIAL = "PARTIAL"

SESSION_GAP_S = 2 * 3600  # a pause this long starts a new conversation session
MAX_ITEMS_PER_SECTION = 6
MAX_EXCERPT_TURNS = 6
DEFAULT_MAX_CHARS = 3500

_CONTINUITY_RE = re.compile(
    r"\b(?:"
    r"where\s+(?:did|were|had)\s+(?:we|i)\s+(?:leave|left|stop|stopped|get|got)(?:\s+off|\s+to)?|"
    r"where\s+were\s+we\b|"
    r"pick\s+up\s+where|"
    r"what\s+(?:were|was)\s+(?:we|i)\s+(?:talking|discussing|chatting|working)\s*(?:about|on)?|"
    r"what\s+did\s+(?:we|i)\s+(?:talk|discuss|chat)\s+about|"
    r"what\s+did\s+(?:we|i)\s+(?:decide|agree|settle|choose|conclude|land\s+on)|"
    r"did\s+(?:we|i)\s+(?:decide|agree|settle)|"
    r"(?:our|the)\s+(?:earlier|previous|last)\s+(?:decision|conversation|discussion|chat|session)|"
    r"last\s+time\s+(?:we|i)\s+(?:talked|spoke|chatted|discussed|worked)|"
    r"(?:remember|recall)\s+(?:that|the|our|when)\b.*\b(?:idea|project|plan|discussion|"
    r"conversation|decision|suggestion|app|application)\b|"
    r"(?:continue|resume|carry\s+on\s+with|get\s+back\s+to)\s+(?:the|our|that|this)\s+"
    r"(?:\w+\s+){0,3}(?:project|discussion|conversation|work|idea|plan)|"
    r"(?:project|idea|plan|thing)\s+(?:we|i)\s+(?:were|was)\s+(?:discussing|talking\s+about|"
    r"working\s+on)|"
    r"catch\s+me\s+up\b|"
    r"remind\s+me\s+what\s+we\b|"
    r"what\s+(?:was|were)\s+(?:that|the|our)\s+(?:\w+\s+){0,3}(?:idea|plan|decision)s?\b"
    r")",
    re.I,
)

# Words that make a sentence a continuity question but say nothing about topic.
_QUERY_STOP = frozenset(
    """where did were we leave left off stop stopped talking talk discussing discuss
    discussed chatting chat working work decide decided agree agreed settle settled choose
    chose conclude concluded remember recall that the our earlier previous last time
    yesterday today week tonight morning afternoon evening continue continuing resume carry
    get back project projects idea ideas plan plans decision decisions discussion
    conversation session thing things about what was again catch remind pick up had
    were land landed suggestion suggestions spoke whatever something""".split()
)

_SECRET_RE = re.compile(
    r"(?:"
    r"\b(?:sk|pk|rk|ghp|gho|github_pat|xox[abp]|AIza)[-_A-Za-z0-9]{16,}|"
    r"\b(?:api[_ -]?key|token|secret|password|passwd|pwd)\s*[:=]\s*\S+|"
    r"\b(?:\d[ -]?){13,16}\b"
    r")",
    re.I,
)


def is_continuity_query(text: str) -> bool:
    return bool(_CONTINUITY_RE.search(text or ""))


_CONTINUE_RE = re.compile(
    r"^\s*(?:(?:ok(?:ay)?|so|alright|now|please)[,\s]+)*(?:let'?s\s+)?"
    r"(?:continue|resume|carry\s+on|get\s+back\s+to|keep\s+going|pick\s+up)\b",
    re.I,
)


def is_recall_question(text: str) -> bool:
    """A question about the past, answered from the record.

    "Continue the project we were discussing" is a continuity turn too, but it
    asks ARIA to carry on working, so it goes to the conversation with the
    retrieved context rather than to a recall answer.
    """
    return is_continuity_query(text) and not _CONTINUE_RE.search(text or "")


def redact(text: str) -> str:
    return _SECRET_RE.sub("[redacted]", text or "")


def topic_terms(text: str) -> set[str]:
    return {t for t in key_terms(text) if t not in _QUERY_STOP}


def time_window(text: str, now: float) -> tuple[float | None, float | None, str]:
    """Resolve "yesterday", "today", "last week", "this morning" against local time."""
    lower = (text or "").lower()
    current = datetime.fromtimestamp(now)
    midnight = current.replace(hour=0, minute=0, second=0, microsecond=0)
    if "yesterday" in lower:
        start = midnight - timedelta(days=1)
        return start.timestamp(), midnight.timestamp(), "yesterday"
    if re.search(r"\b(?:this\s+morning|today|earlier\s+today)\b", lower):
        return midnight.timestamp(), now, "today"
    if re.search(r"\blast\s+week\b", lower):
        return (midnight - timedelta(days=7)).timestamp(), now, "the last week"
    return None, None, ""


@dataclass
class Item:
    section: str
    text: str
    ts: float
    actor: str
    status: str = ""
    ref: str = ""  # record id or episode id
    episode_ids: list[str] = field(default_factory=list)
    branch: str = ""
    note: str = ""

    def citation(self) -> dict[str, Any]:
        return {
            "id": self.ref,
            "type": f"conversation:{self.section}",
            "date": datetime.fromtimestamp(self.ts).strftime("%Y-%m-%d %H:%M") if self.ts else "",
            "content": self.text[:160],
            "episodes": list(self.episode_ids),
            "branch": self.branch,
            "actor": self.actor,
        }


@dataclass
class ContinuityResult:
    status: str
    query: str
    window_label: str = ""
    topic: list[str] = field(default_factory=list)
    sections: dict[str, list[Item]] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    session_span: tuple[float, float] | None = None
    withheld: int = 0  # sensitive items left out because the question was not about them

    @property
    def items(self) -> list[Item]:
        return [i for items in self.sections.values() for i in items]

    def citations(self) -> list[dict[str, Any]]:
        return [i.citation() for i in self.items]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "query": self.query,
            "window": self.window_label,
            "topic": list(self.topic),
            "errors": list(self.errors),
            "withheld_sensitive": self.withheld,
            "sections": {
                name: [
                    {
                        "text": redact(i.text),
                        "actor": i.actor,
                        "status": i.status,
                        "ref": i.ref,
                        "episodes": i.episode_ids,
                        "ts": i.ts,
                        "branch": i.branch,
                        "note": i.note,
                    }
                    for i in items
                ]
                for name, items in self.sections.items()
            },
        }

    def to_prompt(self, max_chars: int = DEFAULT_MAX_CHARS) -> str:
        """The single context block any model backend receives for this turn."""
        return render_context(self, max_chars=max_chars)


SECTION_TITLES = (
    ("decisions", "Decisions the user made"),
    ("rejected", "Rejected or dropped options"),
    ("corrections", "Corrections (these override what they correct)"),
    ("superseded", "Superseded — no longer current"),
    ("ideas", "Ideas discussed"),
    ("open_work", "Unfinished work"),
    ("completed", "Completed work (as recorded by missions/tools)"),
    ("suggestions", "ARIA suggestions the user has not acted on"),
    ("checkpoint", "Saved project checkpoint"),
    ("excerpt", "Conversation excerpt"),
)


def _stamp(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%a %b %d %H:%M") if ts else "undated"


def render_context(result: ContinuityResult, *, max_chars: int = DEFAULT_MAX_CHARS) -> str:
    if result.status == UNAVAILABLE:
        return (
            "Conversation history: UNAVAILABLE — the history search failed this turn. "
            "Do not say there is no record; say the history could not be checked."
        )
    if result.status == NO_RECORD:
        scope = f" about {' '.join(result.topic)}" if result.topic else ""
        when = f" from {result.window_label}" if result.window_label else ""
        return (
            f"Conversation history: NO_RECORD — nothing{scope}{when} was found in the "
            "archived conversations. Say so plainly. Do not reconstruct or guess what "
            "was discussed."
        )
    lines = [
        f"Conversation history ({result.status}) — retrieved from ARIA's archived "
        "conversations. Use only what is listed; cite [ref] ids when relying on an item. "
        "'user' items are what the user said; 'assistant' items are ARIA's own past "
        "suggestions, not decisions; tool/mission items are reported outcomes."
    ]
    for key, title in SECTION_TITLES:
        items = result.sections.get(key) or []
        if not items:
            continue
        lines.append(f"{title}:")
        for item in items:
            status = f" [{item.status}]" if item.status and key != "excerpt" else ""
            note = f" ({item.note})" if item.note else ""
            text = redact(" ".join(item.text.split()))[:300]
            lines.append(f"- {_stamp(item.ts)} {item.actor}{status}: {text}{note} [{item.ref}]")
    if result.errors:
        lines.append("Partial: " + "; ".join(result.errors))
    block = "\n".join(lines)
    if len(block) > max_chars:
        block = block[: max_chars - 20].rsplit("\n", 1)[0] + "\n- (truncated)"
    return block


# ------------------------------------------------------------------ retrieval


def _fts_query(terms: set[str]) -> str:
    safe = [re.sub(r"[^a-z0-9]", "", t) for t in sorted(terms)]
    return " OR ".join(f"{t}*" for t in safe if t)


_IMPORTED_NOTE = "imported from a backup; date approximate"
_SEEDED_NOTE = "from history before the archive existed; original time unknown"


def _record_item(section: str, rec: dict[str, Any], note: str = "") -> Item:
    extra = ""
    if (rec.get("branch") or "").startswith("import:"):
        extra = _IMPORTED_NOTE
    elif (rec.get("detail") or {}).get("episode_kind") == "seed":
        extra = _SEEDED_NOTE
    if extra:
        note = f"{note}; {extra}" if note else extra
    return Item(
        section=section,
        text=rec["text"],
        ts=float(rec["ts"]),
        actor=rec["actor"],
        status=rec["status"],
        ref=rec["id"],
        episode_ids=list(rec.get("episode_ids") or []),
        branch=rec.get("branch") or "",
        note=note,
    )


def _episode_item(ep: dict[str, Any]) -> Item:
    return Item(
        section="excerpt",
        text=ep["content"],
        ts=float(ep["ts"]),
        actor=ep["role"],
        ref=ep["id"],
        episode_ids=[ep["id"]],
        branch=ep["branch"],
        note=(
            _IMPORTED_NOTE
            if ep["kind"] == "import"
            else _SEEDED_NOTE if ep["kind"] == "seed" else ""
        ),
    )


def _latest_session(
    now: float, exclude_text: str, *, branch: str | None = None
) -> tuple[float, float] | None:
    """The most recent stretch of conversation, ignoring the question being asked."""
    recent = store.episodes_between(end=now + 1, branch=branch, limit=400)
    recent = [
        e
        for e in recent
        if not (e["role"] == "user" and e["content"].strip() == exclude_text.strip())
    ]
    if not recent:
        return None
    end = recent[0]["ts"]
    start = end
    for ep in recent[1:]:
        if start - ep["ts"] > SESSION_GAP_S:
            break
        start = ep["ts"]
    return start, end


def _supersession_note(rec: dict[str, Any]) -> str:
    if rec["status"] == store.SUPERSEDED and rec.get("superseded_by"):
        newer = store.get_record(rec["superseded_by"])
        if newer:
            return f"superseded by: {' '.join(newer['text'].split())[:120]}"
    return ""


def _is_sensitive(text: str) -> bool:
    """Categories that never ride along unless the question is about them."""
    try:
        from jarvis.health_product.context import is_health_chat

        return is_health_chat(text)
    except Exception:  # noqa: BLE001 - if unsure, treat as sensitive
        return True


def retrieve(
    query: str,
    *,
    now: float | None = None,
    branch: str | None = None,
    sync: bool = True,
    include_checkpoint: bool = True,
) -> ContinuityResult:
    """Retrieve continuity for one question.

    ``branch`` scopes "where did we leave off?"-style questions to the
    conversation the user is in — branches are how they keep work, personal
    and other threads apart. A question naming a topic searches every branch,
    because the user asked about that topic specifically.
    """
    now = time.time() if now is None else now
    topic = topic_terms(query)
    start, end, label = time_window(query, now)
    ordered = [w for w in dict.fromkeys(re.findall(r"[a-z0-9][a-z0-9+#.-]*", query.lower()))]
    result = ContinuityResult(
        status=NO_RECORD,
        query=query,
        window_label=label,
        topic=[w.strip(".") for w in ordered if w.strip(".") in topic],
    )

    try:
        if sync:
            from jarvis.continuity.ingest import sync_archives

            sync_archives()
        records = _select_records(query, topic, start, end, now, result, branch=branch)
    except Exception as exc:  # noqa: BLE001 - surfaced as UNAVAILABLE, never as "nothing"
        log.warning("Continuity retrieval failed: %s", exc, exc_info=True)
        result.status = UNAVAILABLE
        result.errors.append(f"{type(exc).__name__}: {exc}")
        return result

    if not _is_sensitive(query):
        withheld = [r for r in records["records"] if _is_sensitive(r["text"])]
        withheld += [e for e in records["excerpt"] if _is_sensitive(e["content"])]
        if withheld:
            records["records"] = [r for r in records["records"] if not _is_sensitive(r["text"])]
            records["excerpt"] = [e for e in records["excerpt"] if not _is_sensitive(e["content"])]
            result.withheld = len(withheld)
    _fill_sections(result, records)

    if include_checkpoint and not topic:
        try:
            from aria_core import acm_bridge

            checkpoint = acm_bridge.project_latest_checkpoint()
            if checkpoint and checkpoint.get("content"):
                ts = _parse_ts(checkpoint.get("timestamp"))
                if start is None or (ts and start <= ts < (end or now + 1)):
                    result.sections["checkpoint"] = [
                        Item(
                            section="checkpoint",
                            text=str(checkpoint["content"]),
                            ts=ts or 0.0,
                            actor="user",
                            ref=str(checkpoint.get("id") or "acm-checkpoint"),
                            note="saved checkpoint in ACM",
                        )
                    ]
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"checkpoint lookup failed: {type(exc).__name__}")

    if result.items:
        result.status = PARTIAL if result.errors else HITS
    elif result.errors:
        result.status = UNAVAILABLE
    return result


def _parse_ts(raw: Any) -> float:
    if raw in (None, ""):
        return 0.0
    try:
        return float(raw)
    except (TypeError, ValueError):
        try:
            return datetime.fromisoformat(str(raw)).timestamp()
        except ValueError:
            return 0.0


def _select_records(
    query: str,
    topic: set[str],
    start: float | None,
    end: float | None,
    now: float,
    result: ContinuityResult,
    *,
    branch: str | None = None,
) -> dict[str, Any]:
    """Pick the records and excerpt that answer this question."""
    out: dict[str, Any] = {"records": [], "excerpt": []}
    if topic:
        match = _fts_query(topic)
        records = store.search_records(match, limit=40) if match else []
        if start is not None:
            records = [r for r in records if start <= r["ts"] < (end or now + 1)]
        # Precision over recall: an item must mention most of what was asked
        # about (both words of "fishing application"). Falling back to items
        # that share one word returned unrelated turns as if they answered.
        floor = len(topic) if len(topic) <= 2 else -(-2 * len(topic) // 3)
        out["records"] = [r for r in records if len(topic & key_terms(r["text"])) >= floor]
        episodes = store.search_episodes(match, start=start, end=end, limit=20) if match else []
        episodes = [e for e in episodes if e["content"].strip() != query.strip()]
        episodes = [e for e in episodes if len(topic & key_terms(e["content"])) >= floor]
        out["excerpt"] = sorted(episodes, key=lambda e: e["ts"])[-MAX_EXCERPT_TURNS:]
        return out

    if start is not None:
        span = (start, end or now)
    else:
        span = _latest_session(now, query, branch=branch)
    if span is None:
        return out
    result.session_span = span
    lo, hi = span[0], span[1] + 1
    out["records"] = store.list_records(start=lo, end=hi, branch=branch, limit=60)
    if start is None:
        # "Where did we leave off" also means work still open from before this
        # session; an explicit window ("yesterday") means only that window.
        open_work = store.list_records(
            kinds=[store.TASK],
            statuses=[store.OPEN],
            start=lo - 30 * 86400,
            limit=20,
        )
        # Missions are not tied to a chat branch; user tasks are.
        open_work = [
            r for r in open_work if not branch or r["actor"] == store.MISSION or r["branch"] == branch
        ]
        seen = {r["id"] for r in out["records"]}
        out["records"].extend(r for r in open_work if r["id"] not in seen)
    episodes = store.episodes_between(lo, hi, branch=branch, limit=200, newest_first=False)
    episodes = [e for e in episodes if e["content"].strip() != query.strip()]
    out["excerpt"] = episodes[-MAX_EXCERPT_TURNS:]
    return out


def _fill_sections(result: ContinuityResult, selected: dict[str, Any]) -> None:
    sections: dict[str, list[Item]] = {}

    def add(section: str, item: Item) -> None:
        bucket = sections.setdefault(section, [])
        if len(bucket) < MAX_ITEMS_PER_SECTION and item.ref not in {i.ref for i in bucket}:
            bucket.append(item)

    for rec in sorted(selected["records"], key=lambda r: r["ts"], reverse=True):
        kind, status, actor = rec["kind"], rec["status"], rec["actor"]
        if status == store.SUPERSEDED and actor == store.USER:
            if kind == store.IDEA:
                # A corrected detail does not retire the idea itself.
                note = _supersession_note(rec).replace("superseded by", "later corrected")
                add("ideas", _record_item("ideas", rec, note))
            else:
                add("superseded", _record_item("superseded", rec, _supersession_note(rec)))
            continue
        if kind == store.DECISION:
            add("decisions", _record_item("decisions", rec))
        elif kind == store.REJECTION:
            add("rejected", _record_item("rejected", rec))
        elif kind == store.SUGGESTION:
            if status == store.REJECTED:
                add("rejected", _record_item("rejected", rec, "ARIA suggestion, rejected"))
            elif status == store.ACCEPTED:
                # The user's own decision is the record of what was chosen; a
                # suggestion may have offered several options.
                continue
            else:
                add("suggestions", _record_item("suggestions", rec))
        elif kind == store.CORRECTION:
            add("corrections", _record_item("corrections", rec))
        elif kind == store.IDEA:
            add("ideas", _record_item("ideas", rec))
        elif kind == store.TASK:
            if status == store.OPEN:
                add("open_work", _record_item("open_work", rec))
            elif actor in (store.USER,):
                add("completed", _record_item("completed", rec, "user said finished"))
            else:
                add("completed", _record_item("completed", rec))
        elif kind == store.OUTCOME:
            add("completed", _record_item("completed", rec))
    excerpt = [_episode_item(e) for e in selected["excerpt"]]
    if excerpt:
        sections["excerpt"] = excerpt
    # Chronological inside each section reads more naturally.
    for name, items in sections.items():
        items.sort(key=lambda i: i.ts)
    result.sections = sections


# ------------------------------------------------------------------ answers


def answer(result: ContinuityResult) -> str:
    """A grounded, deterministic reply for direct continuity questions."""
    if result.status == UNAVAILABLE:
        return (
            "I couldn't search our conversation history just now, so I can't tell you "
            "what we discussed. That's a retrieval problem, not an empty history — "
            "please ask again in a moment."
        )
    if result.status == NO_RECORD:
        about = f" about **{' '.join(result.topic)}**" if result.topic else ""
        when = f" from {result.window_label}" if result.window_label else ""
        return (
            f"I don't have any record of a conversation{about}{when} in my history. "
            "I'd rather say that than guess — if you remind me, I'll keep it this time."
        )
    lines: list[str] = []
    if result.window_label and not result.topic:
        lines.append(f"Here's what we covered {result.window_label}:")
    elif result.session_span and not result.topic:
        lines.append(
            f"Last time we talked ({_stamp(result.session_span[1])}), here's where things stood:"
        )
    elif result.topic:
        lines.append(f"Here's what I have on **{' '.join(result.topic)}**:")
    titles = {
        "decisions": "**Decided**",
        "rejected": "**Rejected / dropped**",
        "corrections": "**Corrected**",
        "superseded": "**No longer current**",
        "ideas": "**Ideas**",
        "open_work": "**Still open**",
        "completed": "**Done**",
        "suggestions": "**My suggestions you haven't acted on**",
        "checkpoint": "**Saved checkpoint**",
    }
    for key, title in titles.items():
        items = result.sections.get(key) or []
        if not items:
            continue
        lines.append("")
        lines.append(title)
        for item in items:
            who = "you" if item.actor == "user" else item.actor
            note = f" — {item.note}" if item.note else ""
            lines.append(f"- {redact(' '.join(item.text.split()))[:220]} _({who}, {_stamp(item.ts)})_{note}")
    if not any(result.sections.get(k) for k in titles):
        excerpt = result.sections.get("excerpt") or []
        lines.append("")
        lines.append("**What we were saying**")
        for item in excerpt[-4:]:
            who = "You" if item.actor == "user" else "I"
            lines.append(f"- {who}: {redact(' '.join(item.text.split()))[:200]}")
    refs = [i.ref for i in result.items][:8]
    lines.append("")
    lines.append("Sources: " + ", ".join(f"`{r}`" for r in refs))
    if result.status == PARTIAL:
        lines.append("_Part of the history search failed: " + "; ".join(result.errors) + "_")
    return "\n".join(lines)
