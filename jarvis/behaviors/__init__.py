"""Application behavior extraction — coherent units extracted from JarvisAssistant."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from jarvis.assistant import JarvisAssistant


@dataclass
class ApplicationBehavior:
    """A discoverable, testable behavior unit."""

    behavior_id: str
    name: str
    category: str
    description: str
    module_path: str
    test_module: str = ""
    action_names: list[str] = field(default_factory=list)

    def register(self) -> None:
        """Register handlers and capabilities for this behavior."""

    def descriptor(self, application_id: str) -> dict[str, Any]:
        return {
            "behavior_id": self.behavior_id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "module_path": self.module_path,
            "test_module": self.test_module,
            "actions": list(self.action_names),
            "extracted": True,
            "application_id": application_id,
        }


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


def register_behaviors() -> list[ApplicationBehavior]:
    loaded = discover_behaviors()
    for behavior in loaded:
        behavior.register()
    return loaded


def behavior_descriptors(application_id: str) -> list[dict[str, Any]]:
    return [behavior.descriptor(application_id) for behavior in discover_behaviors()]


_loaded = False


def _ensure_loaded() -> None:
    global _loaded
    if _loaded:
        return
    from jarvis.behaviors import git as _git  # noqa: F401

    _loaded = True
