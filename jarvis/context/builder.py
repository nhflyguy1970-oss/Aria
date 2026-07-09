"""Unified context builder — assemble all context for conversation automatically."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.context")


def build_unified_context(assistant: Any, message: str, *, general: bool = False) -> dict[str, Any]:
    """Assemble context from memory, knowledge, workspace, projects, git, planner, journal."""
    parts: list[str] = []
    citations: list[dict] = []
    warnings: list[str] = []
    meta: dict[str, Any] = {}

    from jarvis.router import is_general_knowledge_question, is_meta_self_question
    from jarvis.runtime_introspection import is_runtime_introspection_question

    skip_project = (
        general
        or is_general_knowledge_question(message, assistant.session)
        or is_meta_self_question(message)
        or is_runtime_introspection_question(message)
    )

    from jarvis.behaviors.conversation import ConversationEngine

    engine = ConversationEngine(assistant)
    prefix, ctx_warnings, ctx_citations = engine.build_context_prefix(
        message, skip_unified_extras=True
    )
    if prefix:
        parts.append(prefix)
    warnings.extend(ctx_warnings)
    citations.extend(ctx_citations)

    if not skip_project:
        append_context_extras(parts, assistant, message, meta)

    return {
        "ok": True,
        "context": "\n\n".join(p for p in parts if p),
        "parts": parts,
        "warnings": warnings,
        "citations": citations,
        "meta": meta,
    }


def append_context_extras(
    parts: list[str], assistant: Any, message: str, meta: dict[str, Any]
) -> None:
    _append_workspace(parts, meta)
    _append_git_state(parts, meta)
    _append_journal(parts, message)
    _append_tool_history(parts, assistant)
    _append_personalization(parts, meta)


def _append_workspace(parts: list[str], meta: dict[str, Any]) -> None:
    try:
        from jarvis.environment import briefing_line

        line = briefing_line()
        if line:
            parts.append(f"Workstation:\n{line}")
            meta["workstation"] = line
    except Exception as exc:
        logger.debug("workspace context: %s", exc)


def _append_git_state(parts: list[str], meta: dict[str, Any]) -> None:
    try:
        from jarvis.knowledge.git_sync import list_repo_states

        states = list_repo_states()
        active = [s for s in states if s.dirty or s.open_prs][:3]
        if not active:
            return
        lines = []
        for st in active:
            pr = f", {len(st.open_prs)} open PR(s)" if st.open_prs else ""
            lines.append(f"- {st.label}: branch `{st.branch}`{' (dirty)' if st.dirty else ''}{pr}")
        parts.append("Git repositories:\n" + "\n".join(lines))
        meta["git_repos"] = [s.to_dict() for s in active]
    except Exception as exc:
        logger.debug("git context: %s", exc)


def _append_journal(parts: list[str], message: str) -> None:
    if "journal" not in message.lower():
        return
    try:
        from jarvis.modules.journal import _today

        day = _today()
        if day and day.get("bullets"):
            bullets = day["bullets"][:5]
            parts.append(
                "Recent journal:\n" + "\n".join(f"- {b.get('text', '')[:120]}" for b in bullets)
            )
    except Exception as exc:
        logger.debug("journal context: %s", exc)


def _append_tool_history(parts: list[str], assistant: Any) -> None:
    try:
        hits = (
            assistant.memory.search("", limit=3, namespace="tools")
            if hasattr(assistant.memory, "search")
            else []
        )
        if not hits:
            return
        lines = [f"- {(h.get('content') or '')[:160]}" for h in hits]
        parts.append("Recent tool results:\n" + "\n".join(lines))
    except Exception as exc:
        logger.debug("tool history: %s", exc)


def _append_personalization(parts: list[str], meta: dict[str, Any]) -> None:
    try:
        from jarvis.personalization.store import preferred_model, preferred_project, preferred_tool

        hints = []
        tool = preferred_tool()
        if tool:
            hints.append(f"preferred coding tool: {tool}")
        proj = preferred_project()
        if proj:
            hints.append(f"preferred project: {proj}")
        chat_model = preferred_model("general")
        if chat_model:
            hints.append(f"preferred chat model: {chat_model}")
        if hints:
            parts.append("Learned preferences:\n" + "\n".join(f"- {h}" for h in hints))
            meta["preferences"] = hints
    except Exception as exc:
        logger.debug("personalization context: %s", exc)
