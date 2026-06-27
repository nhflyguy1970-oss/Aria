"""Memory context: system prompt block, conflicts, project namespace, smart auto-memory."""

from __future__ import annotations

import re
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path

from jarvis.config import PROJECT_ROOT

_JOURNAL_MEMORY = re.compile(
    r"^From bullet journal \(([^)]+)\):\s*(.+)$",
    re.I | re.S,
)
_JOURNAL_DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")
_RESUME_HINTS = re.compile(
    r"\b(resume|continue|checkpoint|left off|where we|coding task|debug until|"
    r"pick up|unfinished|still working on)\b",
    re.I,
)
_CODING_FILE_HINTS = re.compile(
    r"\b(fix|debug|implement|patch|refactor|run tests|pytest)\b.*\.py\b|"
    r"\.py\b.*\b(fix|debug|implement|patch|refactor|tests?)\b",
    re.I,
)

AUTO_MEMORY_MODES = ("off", "explicit", "smart")
GENERIC_AUTO_PATTERNS = (
    r"user asked",
    r"user wanted",
    r"the user is",
    r"assistant (said|replied|explained)",
    r"conversation about",
    r"discussed (the|a) topic",
)


def detect_project_namespace(root: Path | None = None) -> str:
    """Slug from git repo name or project folder."""
    base = (root or PROJECT_ROOT).resolve()
    try:
        r = subprocess.run(
            ["git", "-C", str(base), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if r.returncode == 0:
            base = Path(r.stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        pass
    name = re.sub(r"[^\w-]+", "-", base.name.lower()).strip("-")
    return name or "default"


def system_prompt_block(memory_store, *, max_chars: int = 2200) -> str:
    """Stable user context for the system prompt."""
    from jarvis.trust_memory import filter_trusted_content, seed_default_strategies

    seed_default_strategies(memory_store)

    lines = ["Persistent user context (trust this over guesses):"]

    profile = memory_store.list_entries(namespace="profile")
    summary = next((p for p in profile if "summary" in (p.get("tags") or [])), None)
    if summary:
        lines.append(f"- {summary['content']}")
    else:
        for p in profile[:4]:
            lines.append(f"- {p['content']}")

    for e in memory_store.list_entries(entry_type="strategy")[:4]:
        line = filter_trusted_content(e["content"])
        if line:
            lines.append(f"- Rule: {line}")

    stable = [
        e for e in memory_store.list_entries()
        if e.get("type") in ("fact", "preference", "project")
        and e.get("namespace") not in ("profile",)
        and "checkpoint" not in (e.get("tags") or [])
        and e.get("type") not in ("auto", "failure", "strategy")
    ]
    for e in stable:
        line = filter_trusted_content(e["content"])
        if line:
            lines.append(f"- {line}")
        if len(lines) >= 10:
            break

    block = "\n".join(lines)
    if len(block) > max_chars:
        block = block[: max_chars - 3] + "..."
    return block if len(lines) > 1 else ""


def find_conflicts(memory_store, *, threshold: float = 0.82) -> list[dict]:
    """Find likely contradictory or duplicate memory pairs."""
    from jarvis import llm
    from jarvis.cheatsheets import is_cheatsheet_entry

    entries = [
        e for e in memory_store.list_entries(include_embedding=True)
        if not is_cheatsheet_entry(e)
    ]
    conflicts: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for i, a in enumerate(entries):
        for b in entries[i + 1 :]:
            if a.get("id") == b.get("id"):
                continue
            key = tuple(sorted([a.get("id", ""), b.get("id", "")]))
            if key in seen:
                continue

            ca, cb = a["content"].lower(), b["content"].lower()
            if ca == cb or ca in cb or cb in ca:
                conflicts.append({
                    "kind": "duplicate",
                    "a": memory_store.to_public(a),
                    "b": memory_store.to_public(b),
                    "score": 1.0,
                })
                seen.add(key)
                continue

            emb_a, emb_b = a.get("embedding") or [], b.get("embedding") or []
            sim = llm.cosine_similarity(emb_a, emb_b) if emb_a and emb_b else 0.0
            if sim < threshold:
                continue

            if _looks_contradictory(a["content"], b["content"]):
                conflicts.append({
                    "kind": "contradiction",
                    "a": memory_store.to_public(a),
                    "b": memory_store.to_public(b),
                    "score": round(sim, 3),
                })
                seen.add(key)
            elif sim >= 0.92 and a.get("namespace") == b.get("namespace"):
                conflicts.append({
                    "kind": "similar",
                    "a": memory_store.to_public(a),
                    "b": memory_store.to_public(b),
                    "score": round(sim, 3),
                })
                seen.add(key)

    return conflicts[:20]


def _looks_contradictory(a: str, b: str) -> bool:
    la, lb = a.lower(), b.lower()
    neg = ("don't", "do not", "never", "not ", "no longer", "avoid")
    prefs = ("prefer", "likes", "uses", "wants", "enjoy")
    if any(p in la for p in prefs) and any(p in lb for p in prefs):
        if any(n in la for n in neg) != any(n in lb for n in neg):
            return True
    opposites = [
        ("dark mode", "light mode"),
        ("tabs", "spaces"),
        ("vim", "emacs"),
        ("brief", "detailed"),
        ("linux", "windows"),
        ("morning", "evening"),
    ]
    for x, y in opposites:
        if (x in la and y in lb) or (y in la and x in lb):
            return True
    return False


def should_extract_auto_memory(user_msg: str, assistant_msg: str, mode: str) -> bool:
    if mode == "off":
        return False
    if mode == "explicit":
        return bool(re.search(r"\b(remember|don't forget|note that|keep in mind)\b", user_msg, re.I))
    # smart
    if re.search(r"\b(remember|don't forget|note that|keep in mind)\b", user_msg, re.I):
        return True
    if re.search(r"\?\s*$", user_msg.strip()) and not re.search(
        r"\b(i (?:am|'m)|my name|i prefer|i like|i use|i live|call me)\b", user_msg, re.I
    ):
        return False
    if len(user_msg.strip()) < 12:
        return False
    return bool(re.search(
        r"\b(i (?:am|'m)|my name|call me|i prefer|i like|i love|i hate|i use|i work|i live)\b",
        user_msg,
        re.I,
    ))


def filter_extracted_facts(facts: list[str], user_msg: str) -> list[str]:
    """Drop low-value auto-extracted facts."""
    out = []
    for fact in facts:
        f = fact.strip()
        if len(f) < 12:
            continue
        lower = f.lower()
        if any(re.search(p, lower) for p in GENERIC_AUTO_PATTERNS):
            continue
        if "jarvis" in lower and "user" not in lower:
            continue
        out.append(f)
    return out[:2]


def should_inject_resume_context(message: str, session=None) -> bool:
    """Only surface coding resume/checkpoint hints when the user is continuing that work."""
    from jarvis.router import is_meta_self_question

    text = (message or "").strip()
    if not text or is_meta_self_question(text):
        return False
    if session is not None and getattr(session, "last_module", "") == "coding":
        return True
    if _RESUME_HINTS.search(text):
        return True
    if _CODING_FILE_HINTS.search(text):
        return True
    return False


def _journal_date_from_location(location: str) -> date | None:
    m = _JOURNAL_DATE.search(location or "")
    if not m:
        return None
    try:
        return date.fromisoformat(m.group(1))
    except ValueError:
        return None


def _format_journal_date(d: date) -> str:
    return d.strftime("%B ") + str(d.day)


def normalize_journal_memory_text(content: str, *, journal_date: date | None = None) -> str:
    """Store journal bullets as stable facts, not relative 'today' phrasing."""
    m = _JOURNAL_MEMORY.match((content or "").strip())
    if not m:
        return (content or "").strip()

    location, body = m.group(1).strip(), m.group(2).strip()
    body = re.sub(r"^[\s—\-–]+", "", body).strip()
    d = journal_date or _journal_date_from_location(location)
    if d is None:
        return f"From bullet journal ({location}): {body}"

    birthday = re.match(
        r"today is (.+?)'s birthday\.?$",
        body,
        re.I,
    )
    if birthday:
        who = birthday.group(1).strip()
        who_title = who[:1].upper() + who[1:] if who else "Their"
        return f"{who_title}'s birthday is {_format_journal_date(d)}."

    if re.search(r"\btoday\b", body, re.I):
        body = re.sub(
            r"^Today is ",
            f"On {_format_journal_date(d)}, ",
            body,
            count=1,
            flags=re.I,
        )
        body = re.sub(r"\btoday\b", _format_journal_date(d), body, flags=re.I)

    return f"From bullet journal ({location}): {body}"


def contextualize_memory_for_chat(content: str, *, today: date | None = None) -> str | None:
    """Rewrite or drop dated journal memories so past 'today' notes do not confuse chat."""
    text = (content or "").strip()
    if not text:
        return None

    m = _JOURNAL_MEMORY.match(text)
    if not m:
        return text

    location, body = m.group(1).strip(), m.group(2).strip()
    journal_day = _journal_date_from_location(location)
    now = today or datetime.now(timezone.utc).date()
    if journal_day is None or journal_day >= now:
        return normalize_journal_memory_text(text, journal_date=journal_day)

    normalized = normalize_journal_memory_text(text, journal_date=journal_day)
    if re.search(r"\bbirthday\b", normalized, re.I):
        birthday_only = re.match(r"^(.+'s birthday is .+\.)$", normalized, re.I)
        if birthday_only:
            return birthday_only.group(1)
        return normalized
    if re.search(r"\btoday\b", body, re.I):
        return None
    return f"{normalized} (journal note from {journal_day.isoformat()}, not today)"


def build_conversation_extraction_text(
    messages: list[dict],
    *,
    max_messages: int = 12,
    max_chars: int = 350,
) -> str:
    """Format recent dialogue for periodic conversation memory extraction."""
    recent = [
        m for m in messages[-max_messages:]
        if m.get("role") in ("user", "assistant") and (m.get("content") or "").strip()
    ]
    return "\n".join(
        f"{m['role']}: {(m.get('content') or '').strip()[:max_chars]}" for m in recent
    )


def branch_memory_namespace(branch_id: str) -> str:
    """Per-chat-branch namespace for conversation memory."""
    bid = (branch_id or "main").strip() or "main"
    return f"branch:{bid}"


def branch_summary_text(messages: list[dict], *, max_messages: int = 16, max_chars: int = 400) -> str:
    """Compact branch conversation summary for upsert_branch_summary."""
    recent = [
        m for m in messages[-max_messages:]
        if m.get("role") in ("user", "assistant") and (m.get("content") or "").strip()
    ]
    lines = [
        f"{m['role']}: {(m.get('content') or '').strip()[:max_chars]}"
        for m in recent
    ]
    return "Conversation summary:\n" + "\n".join(lines) if lines else ""


def build_quick_checkpoint(session, messages: list[dict], task_manager=None) -> str | None:
    """Template checkpoint for shutdown — no LLM call."""
    from jarvis.trust_memory import filter_trusted_content, is_test_artifact_path

    user_msgs = [m["content"][:120] for m in messages if m.get("role") == "user"][-3:]
    if not user_msgs and not session.last_file:
        return None

    parts = []
    if session.last_file and not is_test_artifact_path(session.last_file):
        parts.append(f"last file `{session.last_file}`")
    if session.last_module and session.last_module != "general":
        parts.append(f"module {session.last_module}")
    if session.last_coding_mode:
        parts.append(f"coding mode {session.last_coding_mode}")
    if task_manager:
        t = task_manager.active()
        if t:
            parts.append(f"task `{t.title}` ({t.status})")
    if user_msgs:
        clean = [m for m in user_msgs if filter_trusted_content(m)]
        if clean:
            parts.append("recent asks: " + " | ".join(clean))

    if len(parts) < 2 and not session.last_file:
        return None
    return "Auto-saved on exit — " + "; ".join(parts) + "."
