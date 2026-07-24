"""Aria Core Reflex Engine — pre-cognition fast path (Phase 8).

Sits before Capability Bus, Cognitive Orchestrator, Learning, Memory,
Knowledge, Planning, and Reasoning. Deterministic feature matching via
grammar / morphology / syntax — not a growing ad-hoc regex list in the router.
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

REFLEX_VERSION = "2.0-phase8"
PUBLISHER = "aria_core.reflex"

# Tokens that do not carry intent for allow-set checks.
_FILLERS = frozenset(
    {
        "a",
        "an",
        "the",
        "my",
        "me",
        "you",
        "your",
        "to",
        "please",
        "just",
        "really",
        "very",
        "so",
        "oh",
        "um",
        "uh",
        "well",
    }
)
_ADDRESS = frozenset({"aria", "jarvis", "jarvi", "assistant", "friend", "there", "everyone", "all"})

# Stem vocabularies — catalog data, not router regex sprawl.
# Include both surface forms and morphology-stemmed forms (morning→morn, etc.).
_GREET_STEMS = frozenset(
    {
        "hi",
        "hello",
        "hey",
        "greetings",
        "yo",
        "howdy",
        "good",
        "morning",
        "morn",
        "afternoon",
        "evening",
        "day",
    }
)
_CHECKIN_STEMS = frozenset(
    {
        "how",
        "are",
        "you",
        "doing",
        "do",
        "it",
        "going",
        "go",
        "things",
        "thing",
        "what",
        "up",
        "sup",
    }
)
_FAREWELL_STEMS = frozenset(
    {"bye", "goodbye", "goodnight", "later", "see", "farewell", "cya", "ya"}
)
_ACK_STEMS = frozenset(
    {
        "ok",
        "okay",
        "k",
        "thanks",
        "thank",
        "thx",
        "got",
        "cool",
        "nice",
        "great",
        "awesome",
        "perfect",
        "alright",
    }
)
_CONFIRM_STEMS = frozenset(
    {"yes", "yeah", "yep", "yup", "sure", "affirmative", "do", "go", "ahead", "confirm", "agreed"}
)
_NEGATE_STEMS = frozenset(
    {"no", "nope", "nah", "negative", "don't", "dont", "cancel", "never", "mind"}
)
_STOP_STEMS = frozenset({"stop", "cancel", "abort", "halt", "quit", "enough", "nevermind"})
_CONTINUE_STEMS = frozenset({"continue", "proceed", "keep", "going", "go", "on"})
_REPEAT_STEMS = frozenset({"repeat", "again", "say", "that", "what"})
_HELP_STEMS = frozenset(
    {
        "help",
        "capacit",
        "capabilities",
        "capability",
        "feature",
        "features",
        "can",
        "do",
        "what",
        "able",
    }
)
_MODEL_STEMS = frozenset(
    {"model", "models", "ollama", "llm", "which", "what", "recommend", "recommended", "best"}
)
_CLEAR_STEMS = frozenset({"clear"})
_BRIEF_STEMS = frozenset({"briefing", "brief", "status", "news", "update", "report"})
_MC_STEMS = frozenset({"mission", "control", "dashboard", "cockpit"})
_UI_OPEN = frozenset({"open", "show", "launch", "start"})
_UI_CLOSE = frozenset({"close", "hide", "dismiss"})


@dataclass(frozen=True)
class ReflexPattern:
    """Structured reflex rule — matched against extracted linguistic features."""

    id: str
    category: str
    action: str
    priority: int
    max_tokens: int
    confidence: float
    allow_stems: frozenset[str] | None = None
    require_any: frozenset[str] | None = None
    require_all: frozenset[str] | None = None
    forbid_stems: frozenset[str] | None = None
    sentence_types: frozenset[str] | None = None
    question_types: frozenset[str] | None = None
    params: dict[str, Any] = field(default_factory=dict)
    thinking: str = "reflex"
    route_handler: str = "ReflexEngine"
    enabled: bool = True


@dataclass
class ReflexFeatures:
    text: str
    lower: str
    sentence_type: str
    question_type: str
    mood: str
    tokens: list[str]
    stems: list[str]
    content_stems: list[str]
    token_count: int
    subject: str
    verb: str
    object: str


_LOCK = threading.RLock()
_HISTORY: list[dict[str, Any]] = []
_HISTORY_LIMIT = 500
_STATS: dict[str, Any] = {
    "matched": 0,
    "escalated": 0,
    "failed": 0,
    "by_category": {},
    "latency_sum_ms": 0.0,
    "latency_count": 0,
    "false_positives": 0,
    "false_negatives": 0,
}
_FALSE_POS: list[dict[str, Any]] = []
_FALSE_NEG: list[dict[str, Any]] = []


def _catalog() -> list[ReflexPattern]:
    """Authoritative reflex pattern catalog (feature constraints, not router regexes)."""
    return [
        ReflexPattern(
            id="session.clear",
            category="session.clear",
            action="clear",
            priority=5,
            max_tokens=2,
            confidence=0.99,
            allow_stems=_CLEAR_STEMS,
            require_all=_CLEAR_STEMS,
        ),
        ReflexPattern(
            id="session.stop",
            category="session.interrupt",
            action="session_interrupt",
            priority=6,
            max_tokens=4,
            confidence=0.97,
            allow_stems=_STOP_STEMS | _NEGATE_STEMS | frozenset({"that", "this", "please", "it"}),
            require_any=_STOP_STEMS | frozenset({"nevermind"}),
            params={"reply": "Stopped."},
        ),
        ReflexPattern(
            id="session.continue",
            category="session.continue",
            action="session_continue",
            priority=7,
            max_tokens=4,
            confidence=0.95,
            allow_stems=_CONTINUE_STEMS | frozenset({"please"}),
            require_any=frozenset({"continue", "proceed"}) | frozenset({"keep"}),
            params={"reply": "Continuing."},
        ),
        ReflexPattern(
            id="session.repeat",
            category="session.repeat",
            action="session_repeat",
            priority=8,
            max_tokens=5,
            confidence=0.95,
            allow_stems=_REPEAT_STEMS | frozenset({"please", "again"}),
            require_any=frozenset({"repeat", "again"}),
        ),
        ReflexPattern(
            id="ui.mc_open",
            category="ui.mission_control",
            action="status_summary",
            priority=9,
            max_tokens=6,
            confidence=0.93,
            require_all=frozenset({"mission", "control"}),
            require_any=_UI_OPEN | frozenset({"mission"}),
            allow_stems=_MC_STEMS | _UI_OPEN | frozenset({"the", "please"}),
            thinking="mission control open",
        ),
        ReflexPattern(
            id="ui.mc_close",
            category="ui.mission_control",
            action="reflex_reply",
            priority=9,
            max_tokens=6,
            confidence=0.93,
            require_all=frozenset({"mission", "control"}),
            require_any=_UI_CLOSE,
            allow_stems=_MC_STEMS | _UI_CLOSE | frozenset({"the", "please"}),
            params={"reply": "Close Mission Control from the desktop tray or window controls."},
        ),
        ReflexPattern(
            id="briefing.morning",
            category="briefing.morning",
            action="morning_briefing",
            priority=10,
            max_tokens=8,
            confidence=0.96,
            require_any=frozenset({"morning", "morn"}),
            allow_stems=_GREET_STEMS | _BRIEF_STEMS | _ADDRESS,
            thinking="morning briefing",
            route_handler="SituationalBriefing",
        ),
        ReflexPattern(
            id="meta.help",
            category="meta.help",
            action="capabilities",
            priority=12,
            max_tokens=10,
            confidence=0.92,
            sentence_types=frozenset({"interrogative", "request", "imperative", "declarative"}),
            require_any=frozenset({"help", "capacit", "capabilities", "feature", "features"}),
            allow_stems=_HELP_STEMS | _ADDRESS | frozenset({"your", "me", "list", "show"}),
            thinking="capabilities",
        ),
        ReflexPattern(
            id="meta.help_what_can",
            category="meta.help",
            action="capabilities",
            priority=12,
            max_tokens=8,
            confidence=0.92,
            require_all=frozenset({"what", "can"}),
            require_any=frozenset({"do", "you"}),
            allow_stems=_HELP_STEMS | _ADDRESS | frozenset({"you"}),
        ),
        ReflexPattern(
            id="meta.models",
            category="meta.models",
            action="models_info",
            priority=13,
            max_tokens=8,
            confidence=0.92,
            require_any=frozenset({"model", "models", "ollama"}),
            allow_stems=_MODEL_STEMS
            | _ADDRESS
            | frozenset({"are", "available", "should", "i", "use", "list", "show"}),
            thinking="models question",
        ),
        ReflexPattern(
            id="social.greeting",
            category="social.greeting",
            action="greeting",
            priority=20,
            max_tokens=5,
            confidence=0.98,
            allow_stems=_GREET_STEMS | _ADDRESS,
            require_any=frozenset(
                {
                    "hi",
                    "hello",
                    "hey",
                    "greetings",
                    "yo",
                    "howdy",
                    "morning",
                    "morn",
                    "afternoon",
                    "evening",
                    "day",
                }
            ),
            forbid_stems=_BRIEF_STEMS | frozenset({"help", "model", "models"}),
            thinking="greeting",
            route_handler="greeting",
        ),
        ReflexPattern(
            id="social.checkin_how",
            category="social.checkin",
            action="greeting",
            priority=21,
            max_tokens=8,
            confidence=0.97,
            allow_stems=_CHECKIN_STEMS | _GREET_STEMS | _ADDRESS,
            require_all=frozenset({"how", "are"}),
            forbid_stems=_BRIEF_STEMS | frozenset({"model", "models", "help", "capacit"}),
            thinking="social checkin",
            route_handler="greeting",
        ),
        ReflexPattern(
            id="social.checkin_up",
            category="social.checkin",
            action="greeting",
            priority=21,
            max_tokens=6,
            confidence=0.97,
            allow_stems=_CHECKIN_STEMS | _GREET_STEMS | _ADDRESS,
            require_any=frozenset({"up", "sup"}),
            forbid_stems=_BRIEF_STEMS | frozenset({"model", "models", "help", "capacit"}),
            thinking="social checkin",
            route_handler="greeting",
        ),
        ReflexPattern(
            id="social.farewell",
            category="social.farewell",
            action="reflex_reply",
            priority=22,
            max_tokens=5,
            confidence=0.97,
            allow_stems=_FAREWELL_STEMS | _ADDRESS | frozenset({"you", "ya", "good"}),
            require_any=frozenset({"bye", "goodbye", "goodnight", "farewell", "later", "cya"}),
            params={"reply": "Goodbye! I'm here when you need me."},
        ),
        ReflexPattern(
            id="social.ack",
            category="social.ack",
            action="reflex_reply",
            priority=23,
            max_tokens=4,
            confidence=0.96,
            allow_stems=_ACK_STEMS | _ADDRESS | frozenset({"you", "lot"}),
            require_any=_ACK_STEMS - frozenset({"got"}),  # "got" alone weak; "got it" via require
            params={"reply": "You're welcome."},
        ),
        ReflexPattern(
            id="social.ack_got_it",
            category="social.ack",
            action="reflex_reply",
            priority=23,
            max_tokens=3,
            confidence=0.96,
            require_all=frozenset({"got", "it"}),
            allow_stems=frozenset({"got", "it"}) | _ADDRESS,
            params={"reply": "Understood."},
        ),
        ReflexPattern(
            id="social.confirm",
            category="social.confirm",
            action="reflex_reply",
            priority=24,
            max_tokens=4,
            confidence=0.95,
            allow_stems=_CONFIRM_STEMS | _ADDRESS | frozenset({"it", "that"}),
            require_any=frozenset(
                {"yes", "yeah", "yep", "yup", "sure", "affirmative", "agreed", "confirm"}
            ),
            params={"reply": "Confirmed."},
        ),
        ReflexPattern(
            id="social.confirm_go",
            category="social.confirm",
            action="reflex_reply",
            priority=24,
            max_tokens=4,
            confidence=0.95,
            require_any=frozenset({"ahead", "do"}),
            allow_stems=_CONFIRM_STEMS | frozenset({"it", "that", "please"}),
            params={"reply": "On it."},
        ),
        ReflexPattern(
            id="social.negate",
            category="social.negate",
            action="reflex_reply",
            priority=25,
            max_tokens=4,
            confidence=0.95,
            allow_stems=_NEGATE_STEMS | _ADDRESS | frozenset({"that", "this", "please"}),
            require_any=frozenset({"no", "nope", "nah", "negative"}),
            params={"reply": "Okay — cancelled."},
        ),
    ]


def extract_features(message: str) -> ReflexFeatures:
    from jarvis.nlu.grammar import analyze_grammar
    from jarvis.nlu.morphology import analyze_morphology
    from jarvis.nlu.syntax import analyze_syntax

    text = (message or "").strip()
    grammar = analyze_grammar(text)
    morph = analyze_morphology(text)
    syntax = analyze_syntax(text, grammar)
    tokens = list(morph.tokens)

    def _clean(word: str) -> str:
        n = (word or "").lower()
        if n.endswith("'s"):
            n = n[:-2]
        return n.replace("'", "").strip()

    # Light normalization for catalog matching (avoid over-stemming names/greetings).
    norm = [c for t in tokens if (c := _clean(t))]
    stems = [c for s in morph.stems if (c := _clean(s))]
    lexicon = sorted(set(norm) | set(stems))
    content = [s for s in lexicon if s not in _FILLERS and s not in _ADDRESS]
    return ReflexFeatures(
        text=text,
        lower=text.lower(),
        sentence_type=grammar.sentence_type,
        question_type=grammar.question_type,
        mood=grammar.mood,
        tokens=tokens,
        stems=lexicon,
        content_stems=content,
        token_count=len(tokens),
        subject=syntax.subject,
        verb=syntax.verb,
        object=syntax.object,
    )


def _match_pattern(feat: ReflexFeatures, pat: ReflexPattern) -> bool:
    if not pat.enabled or not feat.text:
        return False
    if feat.token_count > pat.max_tokens:
        return False
    if pat.sentence_types and feat.sentence_type not in pat.sentence_types:
        return False
    if pat.question_types and feat.question_type not in pat.question_types:
        return False

    stems = set(feat.stems)
    content = set(feat.content_stems) or stems

    # Special-case morning briefing: greeting morning + briefing stem
    if pat.id == "briefing.morning":
        if not (stems & frozenset({"morning", "morn"})):
            return False
        if not (stems & _BRIEF_STEMS):
            return False
        if os_briefing_disabled():
            return False
        return True

    # Bare "models" is a runtime command — reflex only for question/recommend forms.
    if pat.id == "meta.models":
        if not (stems & frozenset({"model", "models", "ollama"})):
            return False
        if not (
            stems & frozenset({"what", "which", "recommend", "recommended", "best", "list", "show"})
        ):
            return False
        if pat.allow_stems is not None and not content.issubset(
            pat.allow_stems | _FILLERS | _ADDRESS
        ):
            return False
        return True

    if pat.require_all and not pat.require_all.issubset(stems):
        return False
    if pat.require_any and not (stems & pat.require_any):
        return False
    if pat.forbid_stems and (stems & pat.forbid_stems):
        return False
    if pat.allow_stems is not None:
        # every content stem must be permitted
        if not content.issubset(pat.allow_stems | _FILLERS | _ADDRESS):
            return False
    return True


def os_briefing_disabled() -> bool:
    import os

    return os.getenv("JARVIS_BRIEFING", "1") == "0"


def _emit(name: str, **payload: Any) -> None:
    try:
        from aria_core.event_bus import safe_publish

        safe_publish(name, source=PUBLISHER, **payload)
    except Exception:
        pass


def _record(kind: str, **fields: Any) -> dict[str, Any]:
    rec = {
        "id": str(uuid.uuid4()),
        "kind": kind,
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
        **fields,
    }
    with _LOCK:
        _HISTORY.append(rec)
        if len(_HISTORY) > _HISTORY_LIMIT:
            del _HISTORY[: len(_HISTORY) - _HISTORY_LIMIT]
    return rec


def _bump_category(category: str) -> None:
    with _LOCK:
        by = _STATS["by_category"]
        by[category] = int(by.get(category, 0)) + 1


def evaluate(message: str) -> dict[str, Any] | None:
    """Return reflex match metadata or None (escalate). Does not publish events."""
    feat = extract_features(message)
    for pat in sorted(_catalog(), key=lambda p: p.priority):
        if _match_pattern(feat, pat):
            return {
                "matched": True,
                "pattern_id": pat.id,
                "category": pat.category,
                "action": pat.action,
                "params": dict(pat.params),
                "confidence": pat.confidence,
                "thinking": pat.thinking,
                "route_handler": pat.route_handler,
                "features": {
                    "sentence_type": feat.sentence_type,
                    "question_type": feat.question_type,
                    "token_count": feat.token_count,
                    "stems": feat.stems[:12],
                    "content_stems": feat.content_stems[:12],
                },
            }
    return None


def try_reflex(
    message: str, session: Any = None, *, attachment: Any = None
) -> dict[str, Any] | None:
    """Attempt reflex match. On hit, return router intent; else escalate."""
    t0 = time.perf_counter()
    if attachment:
        duration_ms = round((time.perf_counter() - t0) * 1000, 3)
        with _LOCK:
            _STATS["escalated"] = int(_STATS["escalated"]) + 1
        _emit("ReflexEscalated", reason="attachment", duration_ms=duration_ms)
        _emit("ReflexLatency", duration_ms=duration_ms, matched=False)
        _record("escalated", reason="attachment", duration_ms=duration_ms)
        return None

    try:
        hit = evaluate(message)
    except Exception as exc:
        duration_ms = round((time.perf_counter() - t0) * 1000, 3)
        with _LOCK:
            _STATS["failed"] = int(_STATS["failed"]) + 1
        _emit("ReflexFailed", error=type(exc).__name__, duration_ms=duration_ms)
        _emit("ReflexLatency", duration_ms=duration_ms, matched=False, failed=True)
        _record("failed", error=type(exc).__name__, duration_ms=duration_ms)
        return None

    duration_ms = round((time.perf_counter() - t0) * 1000, 3)
    with _LOCK:
        _STATS["latency_sum_ms"] = float(_STATS["latency_sum_ms"]) + duration_ms
        _STATS["latency_count"] = int(_STATS["latency_count"]) + 1

    if not hit:
        with _LOCK:
            _STATS["escalated"] = int(_STATS["escalated"]) + 1
        _emit("ReflexEscalated", reason="no_match", duration_ms=duration_ms)
        _emit("ReflexLatency", duration_ms=duration_ms, matched=False)
        _record(
            "escalated", reason="no_match", duration_ms=duration_ms, message_len=len(message or "")
        )
        return None

    with _LOCK:
        _STATS["matched"] = int(_STATS["matched"]) + 1
    _bump_category(hit["category"])
    _emit(
        "ReflexMatched",
        category=hit["category"],
        pattern_id=hit["pattern_id"],
        action=hit["action"],
        confidence=hit["confidence"],
        duration_ms=duration_ms,
    )
    _emit(
        "ReflexLatency",
        duration_ms=duration_ms,
        matched=True,
        category=hit["category"],
    )
    _record(
        "matched",
        category=hit["category"],
        pattern_id=hit["pattern_id"],
        action=hit["action"],
        confidence=hit["confidence"],
        duration_ms=duration_ms,
        features=hit.get("features"),
    )
    return {
        "action": hit["action"],
        "params": hit["params"],
        "thinking": hit["thinking"],
        "route_handler": hit["route_handler"],
        "router": "reflex",
        "router_stage": "pre_nlu_reflex",
        "reflex_category": hit["category"],
        "reflex_pattern": hit["pattern_id"],
        "reflex_confidence": hit["confidence"],
        "route_confidence": hit["confidence"],
        "route_reason": "reflex",
    }


def is_reflex(message: str, *, attachment: Any = None) -> bool:
    if attachment:
        return False
    try:
        return evaluate(message) is not None
    except Exception:
        return False


def mark_false_positive(*, pattern_id: str = "", category: str = "", note: str = "") -> None:
    with _LOCK:
        _STATS["false_positives"] = int(_STATS["false_positives"]) + 1
        _FALSE_POS.append(
            {"pattern_id": pattern_id, "category": category, "note": note, "ts": time.time()}
        )
        if len(_FALSE_POS) > 100:
            del _FALSE_POS[: len(_FALSE_POS) - 100]


def mark_false_negative(
    *, message_len: int = 0, expected_category: str = "", note: str = ""
) -> None:
    with _LOCK:
        _STATS["false_negatives"] = int(_STATS["false_negatives"]) + 1
        _FALSE_NEG.append(
            {
                "message_len": message_len,
                "expected_category": expected_category,
                "note": note,
                "ts": time.time(),
            }
        )
        if len(_FALSE_NEG) > 100:
            del _FALSE_NEG[: len(_FALSE_NEG) - 100]


def reflex_history(*, limit: int = 100) -> list[dict[str, Any]]:
    with _LOCK:
        return list(_HISTORY[-limit:])


def reflex_statistics() -> dict[str, Any]:
    with _LOCK:
        matched = int(_STATS["matched"])
        escalated = int(_STATS["escalated"])
        failed = int(_STATS["failed"])
        lat_n = int(_STATS["latency_count"]) or 1
        avg = round(float(_STATS["latency_sum_ms"]) / lat_n, 3)
        by_category = dict(_STATS["by_category"])
        false_pos = int(_STATS["false_positives"])
        false_neg = int(_STATS["false_negatives"])
    total = matched + escalated + failed
    return {
        "owner": "aria_core.reflex",
        "version": REFLEX_VERSION,
        "matched": matched,
        "escalated": escalated,
        "failed": failed,
        "total": total,
        "hit_rate": round(100.0 * matched / total, 2) if total else 0.0,
        "avg_latency_ms": avg,
        "by_category": by_category,
        "false_positives": false_pos,
        "false_negatives": false_neg,
        "pattern_count": len(_catalog()),
    }


def reset_for_tests() -> None:
    with _LOCK:
        _HISTORY.clear()
        _FALSE_POS.clear()
        _FALSE_NEG.clear()
        _STATS["matched"] = 0
        _STATS["escalated"] = 0
        _STATS["failed"] = 0
        _STATS["by_category"] = {}
        _STATS["latency_sum_ms"] = 0.0
        _STATS["latency_count"] = 0
        _STATS["false_positives"] = 0
        _STATS["false_negatives"] = 0


def mission_control_panel(*, limit: int = 100) -> dict[str, Any]:
    stats = reflex_statistics()
    hist = reflex_history(limit=limit)
    top = sorted((stats.get("by_category") or {}).items(), key=lambda kv: kv[1], reverse=True)
    with _LOCK:
        false_pos = list(_FALSE_POS[-20:])
        false_neg = list(_FALSE_NEG[-20:])
    return {
        "ok": True,
        "title": "Aria Core Reflex Layer",
        "owner": "aria_core.reflex",
        "version": REFLEX_VERSION,
        "implementation": "aria_core.reflex_engine (grammar/morphology/syntax features)",
        "statistics": stats,
        "hit_rate": stats["hit_rate"],
        "avg_latency_ms": stats["avg_latency_ms"],
        "matched": stats["matched"],
        "escalated": stats["escalated"],
        "failed": stats["failed"],
        "bypassed": stats["matched"],
        "top_categories": [{"category": k, "count": v} for k, v in top[:12]],
        "false_positives": false_pos,
        "false_negatives": false_neg,
        "history": hist,
        "note": (
            "Pre-cognition reflexes. Matched requests bypass Cap Bus, Cognitive "
            "Orchestrator, Learning, Memory, Knowledge, Planning, and Reasoning."
        ),
    }
