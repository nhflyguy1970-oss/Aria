"""Memory behavior — conversational memory, search, namespaces, and consolidation."""

from __future__ import annotations

import os
from typing import Any

from jarvis.behaviors import register_behavior
from jarvis.behaviors.lifecycle import ApplicationBehavior
from jarvis.behaviors.memory.context import MemoryContext
from jarvis.behaviors.memory.engine import MemoryEngine
from jarvis.handlers.registry import register_action

_MEMORY_ACTIONS: dict[str, tuple[Any, bool]] = {
    "remember": (MemoryEngine.remember, False),
    "recall": (MemoryEngine.recall, True),
    "memory_search": (MemoryEngine.memory_search, False),
    "memory_forget": (MemoryEngine.memory_forget, False),
    "memory_correct": (MemoryEngine.memory_correct, False),
    "memory_prune": (MemoryEngine.memory_prune, False),
    "memory_consolidate": (MemoryEngine.memory_consolidate, False),
    "memory_hierarchy": (MemoryEngine.memory_hierarchy, True),
    "memory_summarize": (MemoryEngine.memory_summarize, False),
    "memory_namespace": (MemoryEngine.memory_namespace, False),
    "memory_about_user": (MemoryEngine.memory_about_user, True),
    "cheatsheet_list": (MemoryEngine.cheatsheet_list, True),
    "cheatsheet_show": (MemoryEngine.cheatsheet_show, False),
    "cheatsheet_reset": (MemoryEngine.cheatsheet_reset, False),
    "project_checkpoint": (MemoryEngine.project_checkpoint, False),
    "project_resume": (MemoryEngine.project_resume, True),
    "remember_image": (MemoryEngine.remember_image, False),
    "journal_remember": (MemoryEngine.journal_remember, False),
}

_MEMORY_DEPENDENCIES = ["memory", "semantic_memory", "capability_registry"]


def ensure_memory_engine(orchestrator: Any) -> MemoryEngine:
    behavior = get_memory_behavior()
    if behavior is not None:
        behavior.initialize(orchestrator)
    return MemoryEngine()


def get_memory_behavior() -> MemoryBehavior | None:
    from jarvis.behaviors import get_behavior

    behavior = get_behavior("memory")
    return behavior if isinstance(behavior, MemoryBehavior) else None


@register_behavior
class MemoryBehavior(ApplicationBehavior):
    def __init__(self) -> None:
        super().__init__(
            behavior_id="memory",
            name="Memory",
            category="Memory",
            description=(
                "Conversational memory, episodic notes, summaries, auto-remember, "
                "search, namespace management, and consolidation hooks"
            ),
            module_path="jarvis.behaviors.memory",
            test_module="tests.test_behaviors",
            action_names=list(_MEMORY_ACTIONS.keys()),
            dependencies=list(_MEMORY_DEPENDENCIES),
            stability="stable",
            owner="application",
            version="1.0.0",
        )
        self._context: MemoryContext | None = None

    def initialize(self, orchestrator: Any) -> None:
        self._context = MemoryContext.from_orchestrator(orchestrator)

    def attach(self) -> list[str]:
        for action, (handler, info) in _MEMORY_ACTIONS.items():
            module = "journal" if action == "journal_remember" else "memory"
            register_action(
                action,
                info=info,
                module=module,
                description=action.replace("_", " "),
            )(self._bind(handler))
        return []

    def validate(self) -> list[str]:
        checks = {
            "memory": "JARVIS_PLATFORM_MEMORY_ATTACHED",
            "semantic_memory": "JARVIS_PLATFORM_SEMANTIC_MEMORY_ATTACHED",
            "capability_registry": "JARVIS_PLATFORM_TOOL_CAPABILITY_ATTACHED",
        }
        warnings: list[str] = []
        for dep in self.dependencies:
            env_key = checks.get(dep)
            if env_key and os.getenv(env_key) != "1":
                warnings.append(f"dependency not attached: {dep}")
        return warnings

    def prepare_context(
        self,
        orchestrator: Any,
        message: str,
        *,
        general: bool = False,
        skip_project_context: bool = False,
    ) -> tuple[list[str], list[dict]]:
        self.initialize(orchestrator)
        ctx = self._context or MemoryContext.from_orchestrator(orchestrator)
        return MemoryEngine.prepare_context(
            ctx,
            message,
            general=general,
            skip_project_context=skip_project_context,
        )

    def auto_remember(self, orchestrator: Any, user_msg: str, assistant_msg: str) -> None:
        self.initialize(orchestrator)
        ctx = self._context or MemoryContext.from_orchestrator(orchestrator)
        MemoryEngine.auto_remember(ctx, user_msg, assistant_msg)

    def execute(
        self,
        orchestrator: Any,
        action: str,
        params: dict,
        message: str,
    ) -> dict | None:
        spec = _MEMORY_ACTIONS.get(action)
        if spec is None:
            return None
        handler, _info = spec
        self.initialize(orchestrator)
        ctx = self._context or MemoryContext.from_orchestrator(orchestrator)
        return handler(ctx, params, message)

    def health(self) -> dict[str, Any]:
        report = super().health()
        report["validation_warnings"] = self.validate()
        report["stability"] = self.stability
        report["owner"] = self.owner
        report["version"] = self.version
        if self._context is not None:
            report["memory_stats"] = MemoryEngine.memory_stats(self._context)
        return report

    def shutdown(self) -> None:
        self._context = None

    def _bind(self, handler):
        def _entry(orchestrator, params: dict, message: str) -> dict:
            self.initialize(orchestrator)
            ctx = self._context or MemoryContext.from_orchestrator(orchestrator)
            return handler(ctx, params, message)

        return _entry
