"""User-facing assistant name — acronym branding (default: ARIA)."""

from __future__ import annotations

import os

DEFAULT_NAME = "ARIA"
DEFAULT_FULL_NAME = "Adaptive Reasoning Intelligence Assistant"


def assistant_name() -> str:
    return os.getenv("JARVIS_ASSISTANT_NAME", DEFAULT_NAME).strip() or DEFAULT_NAME


def assistant_full_name() -> str:
    return os.getenv("JARVIS_ASSISTANT_FULL_NAME", DEFAULT_FULL_NAME).strip() or DEFAULT_FULL_NAME


def assistant_intro() -> str:
    """e.g. ARIA (Adaptive Reasoning Intelligence Assistant)"""
    return f"{assistant_name()} ({assistant_full_name()})"


def assistant_window_title(*, uncensored: bool = False) -> str:
    name = assistant_name()
    return f"{name} (Uncensored)" if uncensored else name


def branding_dict() -> dict[str, str]:
    return {
        "assistant_name": assistant_name(),
        "assistant_full_name": assistant_full_name(),
        "assistant_intro": assistant_intro(),
    }
