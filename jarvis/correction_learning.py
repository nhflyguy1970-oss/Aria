"""Correction learning — remember when the user fixes ARIA's mistakes."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any

from jarvis import llm
from jarvis.config import DATA_DIR

log = logging.getLogger("jarvis.correction_learning")

CORRECTION_NAMESPACE = "corrections"
CORRECTION_TAG = "correction-learn"
REGISTRY_FILE = DATA_DIR / "correction_learning.json"

_CORRECTION_MARKERS = re.compile(
    r"\b("
    r"that'?s wrong|you'?re wrong|you are wrong|that is wrong|that is incorrect|"
    r"that'?s incorrect|you'?re mistaken|not what i (?:asked|meant|wanted)|"
    r"don'?t say that|you made a mistake|you got (?:it|that) wrong|"
    r"no,?\s+that'?s not|actually,?\s+no\b"
    r")\b",
    re.I,
)
_CORRECTION_RECALL = re.compile(
    r"\b(what (?:did i|have i) correct(?:ed)?|what corrections? did i make|"
    r"correction recall|what did i fix (?:that )?you (?:said|got wrong))\b",
    re.I,
)
_CORRECTION_RECALL_QUERY = re.compile(
    r"(?:what (?:did i|have i) correct(?:ed)?(?: about)?|what corrections? did i make(?: about)?|"
    r"correction recall(?: about)?|what did i fix (?:that )?you (?:said|got wrong)(?: about)?)\s+(.+)$",
    re.I,
)
_WRONG_ABOUT = re.compile(
    r"^(?:no,?\s+)?(?:you'?re|you are)\s+wrong\s+about\s+(.+?)[:\s—-]+(.+)$",
    re.I | re.S,
)
_NOT_BUT = re.compile(
    r"^(?:no,?\s+)?(?:not|it'?s not)\s+(.+?)\s*,?\s*(?:it'?s|but)\s+(.+)$",
    re.I | re.S,
)
_ACTUALLY = re.compile(
    r"^(?:no,?\s+)?actually,?\s+(.+)$",
    re.I | re.S,
)


@dataclass
class CorrectionIntent:
    correction: str
    wrong_hint: str = ""
    kind: str = "fact"
    raw: str = ""


@dataclass
class CorrectionResult:
    ok: bool
    correction: str
    wrong_claim: str = ""
    kind: str = "fact"
    entry: dict | None = None
    mirrors: list[str] = field(default_factory=list)
    removed: int = 0
    message: str = ""
    source_id: str = ""


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def _load_registry() -> dict[str, Any]:
    if not REGISTRY_FILE.is_file():
        return {"corrections": []}
    try:
        data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("corrections"), list):
            return data
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("Corrupt correction registry: %s", exc)
    return {"corrections": []}


def _save_registry(data: dict[str, Any]) -> None:
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    from jarvis.live_data_guard import assert_live_write_allowed

    assert_live_write_allowed(REGISTRY_FILE)
    REGISTRY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _register_correction(
    *,
    correction: str,
    wrong_claim: str,
    kind: str,
    module: str = "",
) -> str:
    sid = hashlib.sha256(f"{correction}|{wrong_claim}|{time.time()}".encode()).hexdigest()[:12]
    data = _load_registry()
    data["corrections"] = [{
        "id": sid,
        "correction": correction,
        "wrong_claim": wrong_claim,
        "kind": kind,
        "module": module,
        "corrected_at": _utc_now(),
    }, *data.get("corrections", [])][:300]
    _save_registry(data)
    return sid


def correction_stats() -> dict[str, Any]:
    items = _load_registry().get("corrections", [])
    by_kind: dict[str, int] = {}
    for item in items:
        k = item.get("kind") or "fact"
        by_kind[k] = by_kind.get(k, 0) + 1
    return {
        "total": len(items),
        "namespace": CORRECTION_NAMESPACE,
        "by_kind": by_kind,
    }


def is_correction_message(message: str) -> bool:
    text = (message or "").strip()
    if not text:
        return False
    if parse_correction(text):
        return True
    return bool(_CORRECTION_MARKERS.search(text))


def is_correction_recall(message: str) -> bool:
    return bool(_CORRECTION_RECALL.search((message or "").strip()))


def parse_correction_recall_query(message: str) -> str:
    m = _CORRECTION_RECALL_QUERY.search((message or "").strip())
    return (m.group(1).strip() if m else "").rstrip("?.!")


def infer_correction_kind(correction: str) -> str:
    lower = (correction or "").lower()
    if re.search(r"\b(always|never|don'?t|do not|prefer|instead|use |route to|when i ask)\b", lower):
        return "behavior"
    if re.search(r"\b(wrong (?:about|date|name|path|file)|not |is actually|should be)\b", lower):
        return "fact"
    return "fact"


def parse_correction(message: str) -> CorrectionIntent | None:
    """Parse user correction into structured intent."""
    from jarvis.trust_memory import parse_memory_correct

    raw = (message or "").strip()
    if not raw:
        return None

    parsed = parse_memory_correct(raw)
    if parsed:
        hint, new_fact = parsed
        return CorrectionIntent(correction=new_fact, wrong_hint=hint, kind=infer_correction_kind(new_fact), raw=raw)

    m = _WRONG_ABOUT.match(raw)
    if m:
        return CorrectionIntent(
            correction=m.group(2).strip().rstrip("."),
            wrong_hint=m.group(1).strip(),
            kind=infer_correction_kind(m.group(2)),
            raw=raw,
        )

    m = _NOT_BUT.match(raw)
    if m:
        return CorrectionIntent(
            correction=m.group(2).strip().rstrip("."),
            wrong_hint=m.group(1).strip(),
            kind="fact",
            raw=raw,
        )

    if _CORRECTION_MARKERS.search(raw):
        m = _ACTUALLY.match(raw)
        if m:
            body = m.group(1).strip().rstrip(".")
            if len(body) >= 4:
                return CorrectionIntent(correction=body, kind=infer_correction_kind(body), raw=raw)
        m = re.search(
            r"(?:that'?s wrong|you'?re wrong|you are wrong|that is wrong|that is incorrect|"
            r"you got (?:it|that) wrong)[:\s—-]*(.+)$",
            raw,
            re.I | re.S,
        )
        if m:
            body = m.group(1).strip().rstrip(".")
            if len(body) >= 4:
                return CorrectionIntent(correction=body, kind=infer_correction_kind(body), raw=raw)
        if len(raw) >= 12:
            return CorrectionIntent(correction=raw, kind=infer_correction_kind(raw), raw=raw)

    return None


def _summarize_wrong_claim(assistant_msg: str, correction: str) -> str:
    assistant = (assistant_msg or "").strip()
    if not assistant:
        return ""
    if len(assistant) <= 280:
        return assistant
    excerpt = assistant[:1200]
    prompt = (
        "The user is correcting the assistant. From the assistant reply below, "
        "write ONE short sentence stating what the assistant got wrong. "
        "If unclear, summarize the disputed claim.\n\n"
        f"User correction: {correction[:400]}\n\n"
        f"Assistant reply:\n{excerpt}"
    )
    try:
        summary = llm.ask(llm.general_model(), [{"role": "user", "content": prompt}]).strip()
        return summary[:400] if summary else excerpt[:280]
    except Exception:
        return excerpt[:280]


def _format_correction(wrong_claim: str, correction: str) -> str:
    wrong = (wrong_claim or "").strip()
    right = (correction or "").strip()
    if wrong and right:
        return f"[Correction] Wrong: {wrong} → Right: {right}"
    if right.lower().startswith("[correction]"):
        return right
    return f"[Correction] {right}"


def apply_correction(
    memory,
    intent: CorrectionIntent,
    *,
    assistant_msg: str = "",
    module: str = "",
) -> CorrectionResult:
    """Store a user correction and update memory/strategy layers."""
    correction = intent.correction.strip()
    if not correction:
        return CorrectionResult(False, "", message="Empty correction.")

    kind = intent.kind if intent.kind in ("fact", "behavior") else infer_correction_kind(correction)
    wrong_claim = (intent.wrong_hint or "").strip()
    if not wrong_claim and assistant_msg:
        wrong_claim = _summarize_wrong_claim(assistant_msg, correction)

    removed = 0
    strategy_created = False
    mirrors: list[str] = []
    from jarvis.trust_memory import correct_memory, record_strategy

    if kind == "fact" or intent.wrong_hint:
        removed, _fact_entry, strategy_created = correct_memory(
            memory,
            correction,
            search_hint=intent.wrong_hint,
        )
        if removed:
            mirrors.append(f"replaced {removed} fact(s)")
        elif _fact_entry:
            mirrors.append("updated fact")
    elif kind == "behavior":
        rule = correction if correction.lower().startswith("when ") else f"When answering: {correction.rstrip('.')}"
        try:
            record_strategy(memory, rule, namespace=CORRECTION_NAMESPACE, source="correction-learn")
            mirrors.append("behavior strategy")
            strategy_created = True
        except ValueError as exc:
            log.debug("Strategy from correction skipped: %s", exc)

    lesson = _format_correction(wrong_claim, correction)

    entry = memory.add(
        "teaching",
        lesson,
        tags=[CORRECTION_TAG, f"correction-{kind}", "user-corrected"],
        namespace=CORRECTION_NAMESPACE,
    )
    mirrors.append("correction teaching")

    try:
        memory.add(
            "note",
            lesson,
            tags=[CORRECTION_TAG, f"correction-{kind}"],
            namespace=CORRECTION_NAMESPACE,
        )
        mirrors.append("correction note")
    except ValueError:
        pass

    if strategy_created and "behavior strategy" not in mirrors:
        mirrors.append("behavior strategy")

    sid = _register_correction(
        correction=correction,
        wrong_claim=wrong_claim,
        kind=kind,
        module=module,
    )
    return CorrectionResult(
        True,
        correction,
        wrong_claim=wrong_claim,
        kind=kind,
        entry=entry,
        mirrors=mirrors,
        removed=removed,
        message=f"Remembered your correction ({kind}).",
        source_id=sid,
    )


def list_corrections(memory, *, query: str = "", limit: int = 25) -> list[dict]:
    entries = memory.list_entries(entry_type="teaching", namespace=CORRECTION_NAMESPACE)
    entries = [e for e in entries if CORRECTION_TAG in (e.get("tags") or [])]
    if query:
        q = query.lower()
        entries = [e for e in entries if q in e.get("content", "").lower()]
        if not entries and llm.embed_available():
            hits = memory.search(query, limit=limit, namespace=CORRECTION_NAMESPACE)
            seen: set[str] = set()
            for h in hits:
                if CORRECTION_TAG in (h.get("tags") or []) and h["id"] not in seen:
                    entries.append(h)
                    seen.add(h["id"])
    entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return entries[:limit]


def correction_context_for_chat(memory, message: str, *, limit: int = 4) -> str:
    from jarvis.trust_memory import filter_trusted_content

    q = (message or "").strip()
    if len(q) < 6:
        return ""
    hits = list_corrections(memory, query=q, limit=limit)
    if not hits:
        words = [w for w in re.findall(r"[a-z]{4,}", q.lower())]
        stop = {"what", "when", "where", "should", "would", "could", "about", "there", "this", "that", "with", "from"}
        words = [w for w in words if w not in stop][:6]
        if words:
            pool = list_corrections(memory, limit=40)
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
    return "Past corrections (do not repeat these mistakes):\n" + "\n".join(lines)


def corrections_system_block(memory, *, max_items: int = 6) -> str:
    from jarvis.trust_memory import filter_trusted_content

    entries = list_corrections(memory, limit=max_items)
    lines: list[str] = []
    for e in entries:
        line = filter_trusted_content(e.get("content", ""))
        if line:
            lines.append(f"- {line}")
    if not lines:
        return ""
    return "User corrections (highest priority — avoid repeating these errors):\n" + "\n".join(lines)


def format_corrections_markdown(entries: list[dict]) -> str:
    if not entries:
        return "_No corrections stored yet._"
    return "\n".join(f"• {e.get('content', '')}" for e in entries)


def should_auto_learn_correction(user_msg: str, mode: str) -> bool:
    if mode == "off":
        return False
    if mode == "explicit":
        return bool(re.search(r"\b(remember (?:this )?correction|correct(?:ion)? learn)\b", user_msg, re.I))
    return is_correction_message(user_msg)
