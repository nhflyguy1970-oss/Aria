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


def register_behaviors(orchestrator: JarvisAssistant | None = None) -> list[ApplicationBehavior]:
    loaded = discover_behaviors()
    for behavior in loaded:
        behavior.attach()
        if orchestrator is not None:
            behavior.initialize(orchestrator)
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
    from jarvis.behaviors.briefing import BriefingBehavior as _briefing  # noqa: F401
    from jarvis.behaviors.data import DataBehavior as _data  # noqa: F401
    from jarvis.behaviors.vision import VisionBehavior as _vision  # noqa: F401
    from jarvis.behaviors.audio import AudioBehavior as _audio  # noqa: F401
    from jarvis.behaviors.media import MediaBehavior as _media_behavior  # noqa: F401
    from jarvis.behaviors.engineering import EngineeringBehavior as _engineering  # noqa: F401
    from jarvis.behaviors.knowledge import KnowledgeBehavior as _knowledge  # noqa: F401
    from jarvis.behaviors.memory import MemoryBehavior as _memory  # noqa: F401
    from jarvis.behaviors.planning import PlanningBehavior as _planning  # noqa: F401
    from jarvis.behaviors.smarthome import SmartHomeBehavior as _smarthome  # noqa: F401
    from jarvis.behaviors.operations import OperationsBehavior as _operations  # noqa: F401
    from jarvis.behaviors.tools import ToolsBehavior as _tools  # noqa: F401
    from jarvis.behaviors.agents import AgentsBehavior as _agents  # noqa: F401
    from jarvis.behaviors.personalization import PersonalizationBehavior as _personalization  # noqa: F401

    _loaded = True


__all__ = [
    "ApplicationBehavior",
    "behavior_descriptors",
    "discover_behaviors",
    "get_behavior",
    "register_behavior",
    "register_behaviors",
]
