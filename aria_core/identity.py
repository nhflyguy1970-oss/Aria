"""Aria Core — Identity (delegates to jarvis.config)."""

from __future__ import annotations

from typing import Any

from aria_core.ownership import module_ownership

OWNER = module_ownership("identity")


def profile_name() -> str:
    from jarvis import config as jarvis_config

    return str(getattr(jarvis_config, "PROFILE_NAME", None) or "Aria")


def is_uncensored() -> bool:
    from jarvis import config as jarvis_config

    return bool(getattr(jarvis_config, "UNCENSORED", False))


def system_prompt() -> str:
    from jarvis import config as jarvis_config

    if is_uncensored():
        return str(getattr(jarvis_config, "SYSTEM_PROMPT_UNCENSORED", "") or "")
    return str(getattr(jarvis_config, "SYSTEM_PROMPT", "") or "")


def identity_snapshot() -> dict[str, Any]:
    return {
        "profile_name": profile_name(),
        "uncensored": is_uncensored(),
        "owner": OWNER["owner"],
        "implementation": OWNER["implementation"],
    }
