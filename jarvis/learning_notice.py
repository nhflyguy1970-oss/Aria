"""User-visible notices when Aria learns or retrieves from memory."""

from __future__ import annotations

# Thread-local-ish last retrieval hint for the current response (set during context build).
_last_retrieval_hint: str = ""


def set_retrieval_hint(text: str) -> None:
    global _last_retrieval_hint
    _last_retrieval_hint = (text or "").strip()


def pop_retrieval_hint() -> str:
    global _last_retrieval_hint
    hint = _last_retrieval_hint
    _last_retrieval_hint = ""
    return hint


def learning_notice(kind: str, *, detail: str = "") -> str:
    """Short confirmation when something was stored."""
    notices = {
        "preference": "✓ Preference updated.",
        "long_term": "✓ Stored in long-term memory.",
        "project": "✓ Added to project memory.",
        "personalization": "✓ Updated personalization.",
        "conversation": "✓ Saved for future conversations.",
        "strategy": "✓ Stored correction for future replies.",
        "profile": "✓ Profile updated.",
    }
    base = notices.get(kind, "✓ Saved.")
    if detail:
        return f"{base} ({detail[:80]})"
    return base


def memory_retrieval_hint(citations: list[dict], *, project: bool = False) -> str:
    """Brief note when memory influenced context (not noisy)."""
    if not citations:
        return ""
    if project:
        return "I found relevant information from your project memory."
    kinds = {c.get("type") for c in citations if c.get("type")}
    if "strategy" in kinds:
        return "I applied a stored preference from memory."
    if len(citations) == 1:
        return "I found one relevant memory entry."
    return f"I found {len(citations)} relevant memory entries."


def append_learning_to_message(message: str, notice: str) -> str:
    """Prefix assistant message with a learning notice when present."""
    notice = (notice or "").strip()
    if not notice:
        return message
    if notice in message:
        return message
    return f"{notice}\n\n{message}"


def append_retrieval_to_message(message: str, hint: str) -> str:
    """Prefix with retrieval hint once, briefly."""
    hint = (hint or "").strip()
    if not hint or hint in message:
        return message
    return f"_{hint}_\n\n{message}"
