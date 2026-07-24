"""One-time profile questionnaire — answers stored in memory namespace `profile`."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TypedDict

from jarvis.config import _load_chat_settings, _write_chat_settings


class _Question(TypedDict, total=False):
    id: str
    label: str
    hint: str
    type: str
    required: bool
    memory_type: str
    format: str
    options: list[tuple[str, str]]


PROFILE_NAMESPACE = "profile"
PROFILE_TAGS = ["profile", "onboarding"]

QUESTIONS: list[_Question] = [
    {
        "id": "name",
        "label": "What should I call you?",
        "hint": "First name or nickname",
        "type": "text",
        "required": True,
        "memory_type": "fact",
        "format": "User's name is {value}.",
    },
    {
        "id": "role",
        "label": "What do you do?",
        "hint": "Job, student, hobbies — whatever fits",
        "type": "text",
        "required": False,
        "memory_type": "fact",
        "format": "User's role or background: {value}.",
    },
    {
        "id": "location",
        "label": "Where are you based?",
        "hint": "City or timezone (optional)",
        "type": "text",
        "required": False,
        "memory_type": "fact",
        "format": "User is based in {value}.",
    },
    {
        "id": "communication",
        "label": "How should I communicate?",
        "type": "select",
        "required": True,
        "options": [
            ("brief", "Brief — bullets, no fluff"),
            ("balanced", "Balanced — clear and friendly"),
            ("detailed", "Detailed — thorough explanations"),
            ("tutor", "Tutor — step-by-step teaching"),
        ],
        "memory_type": "preference",
        "format": "User prefers {value} communication style.",
    },
    {
        "id": "primary_use",
        "label": "What will you use Jarvis for most?",
        "type": "select",
        "required": True,
        "options": [
            ("coding", "Coding & debugging"),
            ("writing", "Writing & documents"),
            ("research", "Research & learning"),
            ("creative", "Creative & images"),
            ("data", "Data & spreadsheets"),
            ("general", "General assistant"),
        ],
        "memory_type": "preference",
        "format": "User primarily uses Jarvis for {value}.",
    },
    {
        "id": "tech_stack",
        "label": "Favorite tools & tech?",
        "hint": "Editor, OS, languages you use daily",
        "type": "text",
        "required": False,
        "memory_type": "preference",
        "format": "User's tech stack and tools: {value}.",
    },
    {
        "id": "interests",
        "label": "Topics you work on often?",
        "hint": "Projects, domains, passions",
        "type": "text",
        "required": False,
        "memory_type": "fact",
        "format": "User often works on: {value}.",
    },
    {
        "id": "notes",
        "label": "Anything else I should always remember?",
        "hint": "Pet peeves, must-dos, accessibility needs…",
        "type": "textarea",
        "required": False,
        "memory_type": "preference",
        "format": "User notes for Jarvis: {value}.",
    },
]

_OPTION_LABELS: dict[str, dict[str, str]] = {
    q["id"]: dict(q.get("options") or []) for q in QUESTIONS if q.get("options")
}


def _profile_state() -> dict:
    return _load_chat_settings().get("profile_questionnaire") or {}


def is_completed() -> bool:
    return bool(_profile_state().get("completed"))


def get_status() -> dict:
    state = _profile_state()
    return {
        "completed": bool(state.get("completed")),
        "completed_at": state.get("completed_at"),
        "skipped": bool(state.get("skipped")),
    }


def get_questions() -> list[dict]:
    """Public question defs for the GUI (no format strings)."""
    out = []
    for q in QUESTIONS:
        item = {
            "id": q["id"],
            "label": q["label"],
            "type": q["type"],
            "required": q.get("required", False),
        }
        if q.get("hint"):
            item["hint"] = q["hint"]
        if q.get("options"):
            item["options"] = [{"value": v, "label": lbl} for v, lbl in q["options"]]
        out.append(item)
    return out


def _mark_completed(*, skipped: bool = False) -> None:
    data = _load_chat_settings()
    data["profile_questionnaire"] = {
        "completed": True,
        "skipped": skipped,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    _write_chat_settings(data)


def _display_value(question_id: str, raw: str) -> str:
    raw = (raw or "").strip()
    labels = _OPTION_LABELS.get(question_id, {})
    return labels.get(raw, raw.replace("_", " "))


def clear_profile_entries(memory_store) -> int:
    """Remove all profile namespace memories (ACM PRIMARY: cool/forget each id)."""
    entries = memory_store.list_entries(namespace=PROFILE_NAMESPACE)
    before = len(entries)
    try:
        from aria_core.acm_bridge import acm_is_authoritative

        if acm_is_authoritative():
            for e in entries:
                eid = e.get("id")
                if eid:
                    memory_store.delete_id(eid)
            return before
    except ImportError:
        pass
    memory_store._data["entries"] = [
        e for e in memory_store._data["entries"] if e.get("namespace") != PROFILE_NAMESPACE
    ]
    if before:
        memory_store._save()
    return before


def reset_profile(memory_store) -> None:
    """Clear profile memories and allow questionnaire again."""
    clear_profile_entries(memory_store)
    data = _load_chat_settings()
    data.pop("profile_questionnaire", None)
    _write_chat_settings(data)


def save_answers(memory_store, answers: dict, *, replace: bool = False) -> list[str]:
    """Persist questionnaire answers to memory. Returns stored memory lines."""
    if replace or is_completed():
        clear_profile_entries(memory_store)
    stored: list[str] = []
    summary_parts: list[str] = []

    for q in QUESTIONS:
        qid = q["id"]
        raw = (answers.get(qid) or "").strip()
        if not raw:
            continue
        display = _display_value(qid, raw)
        content = q["format"].format(value=display)
        memory_store.add(
            q.get("memory_type", "fact"),
            content,
            tags=PROFILE_TAGS + [qid],
            namespace=PROFILE_NAMESPACE,
        )
        stored.append(content)
        if qid == "name":
            summary_parts.insert(0, display)
        else:
            summary_parts.append(display)

    if summary_parts:
        summary = "User profile (onboarding): " + "; ".join(summary_parts) + "."
        memory_store.add(
            "fact",
            summary,
            tags=PROFILE_TAGS + ["summary"],
            namespace=PROFILE_NAMESPACE,
        )
        stored.append(summary)

    _mark_completed(skipped=False)
    return stored


def skip(memory_store) -> None:
    """Mark questionnaire complete without storing answers."""
    _mark_completed(skipped=True)
