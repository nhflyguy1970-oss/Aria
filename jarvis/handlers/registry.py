"""Action handler registry — register once, dispatch from assistant."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from jarvis.assistant import JarvisAssistant

HandlerFn = Callable[["JarvisAssistant", dict, str], dict]


@dataclass
class ActionSpec:
    name: str
    handler: HandlerFn | None = None
    queue: str | None = None  # media | background | coding | fix_tests
    info: bool = False
    module: str | None = None
    description: str = ""


_REGISTRY: dict[str, ActionSpec] = {}


def register_action(
    name: str,
    *,
    queue: str | None = None,
    info: bool = False,
    module: str | None = None,
    description: str = "",
) -> Callable[[HandlerFn], HandlerFn]:
    def decorator(fn: HandlerFn) -> HandlerFn:
        _REGISTRY[name] = ActionSpec(
            name=name,
            handler=fn,
            queue=queue,
            info=info,
            module=module,
            description=description or name.replace("_", " "),
        )
        return fn

    return decorator


def register_queue(
    name: str,
    queue: str,
    *,
    info: bool = False,
    module: str | None = None,
    description: str = "",
) -> None:
    """Register queue-only metadata (handler runs via existing assistant method)."""
    _REGISTRY[name] = ActionSpec(
        name=name,
        handler=None,
        queue=queue,
        info=info,
        module=module,
        description=description or name.replace("_", " "),
    )


def has_action(name: str) -> bool:
    return name in _REGISTRY


def get_spec(name: str) -> ActionSpec | None:
    return _REGISTRY.get(name)


def get_action(name: str) -> HandlerFn | None:
    spec = _REGISTRY.get(name)
    return spec.handler if spec else None


def get_queue(name: str) -> str | None:
    spec = _REGISTRY.get(name)
    return spec.queue if spec else None


def is_info_action(name: str) -> bool:
    spec = _REGISTRY.get(name)
    return bool(spec and spec.info)


def all_actions() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for spec in sorted(_REGISTRY.values(), key=lambda s: s.name):
        out.append({
            "action": spec.name,
            "queue": spec.queue,
            "info": spec.info,
            "module": spec.module,
            "description": spec.description,
            "registered": spec.handler is not None,
        })
    return out


def call_action(assistant: JarvisAssistant, action: str, params: dict, message: str) -> dict:
    from jarvis.modules.capability_adapter import capability_invoke

    return capability_invoke(_call_action_impl, assistant, action, params, message)


def _call_action_impl(assistant: JarvisAssistant, action: str, params: dict, message: str) -> dict:
    spec = _REGISTRY.get(action)
    if not spec or not spec.handler:
        raise KeyError(action)
    return spec.handler(assistant, params, message)
