"""Brain mode — autonomy bundle for proactive memory learning."""

from __future__ import annotations

import os
from typing import Any

BRAIN_ENV = "JARVIS_BRAIN_MODE"
_BRAIN_BUNDLE_FLAGS = (
    "JARVIS_MEMORY_CONSOLIDATION",
    "JARVIS_GRAPH_LLM_EXTRACT",
    "JARVIS_AUTO_OBSERVE_COMMAND",
    "JARVIS_AUTO_JOURNAL_LEARN",
    "JARVIS_AUTO_DOCUMENT_LEARN",
    "JARVIS_AUTO_AUDIO_LEARN",
    "JARVIS_AUTO_WORKFLOW_REMEMBER",
    "JARVIS_PROJECT_JOURNAL_AUTO_LEARN",
)


def brain_mode_enabled() -> bool:
    from jarvis.config import load_brain_mode

    return load_brain_mode()


def _env_truthy(val: str) -> bool:
    return val.strip().lower() in ("1", "true", "yes", "on", "smart")


def _env_falsy(val: str) -> bool:
    return val.strip().lower() in ("0", "false", "off", "no")


def brain_or_env(key: str, *, default_when_brain: bool = True) -> bool:
    """True when env is on, or brain mode enables unless env explicitly off."""
    val = os.getenv(key, "").strip()
    if val and _env_falsy(val):
        return False
    if val and _env_truthy(val):
        return True
    if brain_mode_enabled():
        return default_when_brain
    return default_when_brain


def consolidation_enabled() -> bool:
    return brain_or_env("JARVIS_MEMORY_CONSOLIDATION")


def graph_llm_extract_enabled() -> bool:
    return brain_or_env("JARVIS_GRAPH_LLM_EXTRACT")


def auto_observe_command_enabled() -> bool:
    return brain_or_env("JARVIS_AUTO_OBSERVE_COMMAND")


def auto_journal_learn_enabled() -> bool:
    from jarvis.config import load_auto_journal_learn

    return load_auto_journal_learn()


def auto_document_learn_enabled() -> bool:
    from jarvis.config import load_auto_document_learn

    return load_auto_document_learn()


def auto_audio_learn_enabled() -> bool:
    return brain_or_env("JARVIS_AUTO_AUDIO_LEARN")


def auto_workflow_remember_enabled() -> bool:
    val = os.getenv("JARVIS_AUTO_WORKFLOW_REMEMBER", "").strip()
    if val and _env_falsy(val):
        return False
    if val and _env_truthy(val):
        return True
    return brain_mode_enabled()


def project_journal_auto_learn_enabled() -> bool:
    return brain_or_env("JARVIS_PROJECT_JOURNAL_AUTO_LEARN")


def brain_mode_status() -> dict[str, Any]:
    enabled = brain_mode_enabled()
    status: dict[str, Any] = {
        "enabled": enabled,
        "env": os.getenv(BRAIN_ENV, ""),
        "consolidation": consolidation_enabled(),
        "graph_llm_extract": graph_llm_extract_enabled(),
        "auto_observe_command": auto_observe_command_enabled(),
        "auto_journal_learn": auto_journal_learn_enabled(),
        "auto_document_learn": auto_document_learn_enabled(),
        "auto_audio_learn": auto_audio_learn_enabled(),
        "auto_workflow_remember": auto_workflow_remember_enabled(),
        "project_journal_auto_learn": project_journal_auto_learn_enabled(),
        "bundle_flags": list(_BRAIN_BUNDLE_FLAGS),
    }
    try:
        from jarvis.reflection_loop import reflection_status

        status["reflection"] = reflection_status()
    except Exception:
        pass
    return status
