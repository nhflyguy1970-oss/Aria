"""Application behavior extraction — coherent units extracted from JarvisAssistant."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from jarvis.behaviors.lifecycle import ApplicationBehavior

if TYPE_CHECKING:
    from jarvis.assistant import JarvisAssistant

_BEHAVIORS: list[ApplicationBehavior] = []


def register_behavior(target: ApplicationBehavior | type[ApplicationBehavior]) -> Any:
    if isinstance(target, type):
        instance = target()
        _BEHAVIORS.append(instance)
        return target
    _BEHAVIORS.append(target)
    return target


def discover_behaviors() -> list[ApplicationBehavior]:
    _ensure_loaded()
    return list(_BEHAVIORS)


def register_behaviors(assistant: JarvisAssistant | None = None) -> list[ApplicationBehavior]:
    loaded = discover_behaviors()
    for behavior in loaded:
        behavior.attach()
        if assistant is not None:
            behavior.initialize(assistant)
    return loaded


def behavior_descriptors(application_id: str) -> list[dict[str, Any]]:
    return [behavior.descriptor(application_id) for behavior in discover_behaviors()]


def get_behavior(behavior_id: str) -> ApplicationBehavior | None:
    for behavior in discover_behaviors():
        if behavior.behavior_id == behavior_id:
            return behavior
    return None


_loaded = False


def _ensure_loaded() -> None:
    global _loaded
    if _loaded:
        return
    from jarvis.behaviors import conversation as _conversation  # noqa: F401
    from jarvis.behaviors import git as _git  # noqa: F401

    _loaded = True
