"""Aria Core — Learning (delegates to jarvis.learning_governor)."""

from __future__ import annotations

from typing import Any

from aria_core.ownership import module_ownership

OWNER = module_ownership("learning")


def enabled() -> bool:
    from jarvis.learning_governor import enabled as _enabled

    return _enabled()


def propose(*, kind: str, payload: dict[str, Any] | None = None, source: str = ""):
    from jarvis.learning_governor import propose as _propose

    return _propose(kind=kind, payload=payload, source=source)


def commit(proposal, apply):
    from jarvis.learning_governor import commit as _commit

    return _commit(proposal, apply)


def Proposal(*args: Any, **kwargs: Any):
    from jarvis.learning_governor import Proposal as _Proposal

    return _Proposal(*args, **kwargs)


def recent_audit(*, limit: int = 50) -> list[dict[str, Any]]:
    from jarvis.learning_governor import recent_audit as _recent

    return _recent(limit=limit)
