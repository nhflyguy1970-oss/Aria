"""Engineering behavior — coding, git, LSP, refactoring, and code index."""

from __future__ import annotations

import os
from typing import Any

from jarvis.behaviors import register_behavior
from jarvis.behaviors.engineering.context import EngineeringContext
from jarvis.behaviors.engineering.engine import EngineeringEngine
from jarvis.behaviors.lifecycle import ApplicationBehavior
from jarvis.handlers.registry import register_action

_ENGINEERING_ACTIONS: dict[str, tuple[Any, bool]] = {
    "git_status": (EngineeringEngine.git_status, True),
    "git_diff": (EngineeringEngine.git_diff, False),
    "git_commit": (EngineeringEngine.git_commit, False),
    "git_branch": (EngineeringEngine.git_branch, False),
    "git_summarize": (EngineeringEngine.git_summarize, False),
    "git_pr": (EngineeringEngine.git_pr, False),
    "coding_read": (EngineeringEngine.coding_read, False),
    "coding_fix": (EngineeringEngine.coding_fix, False),
    "coding_fix_tests": (EngineeringEngine.coding_fix_tests, False),
    "coding_improve": (EngineeringEngine.coding_improve, False),
    "coding_find": (EngineeringEngine.coding_find, True),
    "coding_search": (EngineeringEngine.coding_search, False),
    "coding_run": (EngineeringEngine.coding_run, False),
    "coding_project": (EngineeringEngine.coding_project, True),
    "coding_review": (EngineeringEngine.coding_review, False),
    "coding_show": (EngineeringEngine.coding_show, True),
    "coding_create": (EngineeringEngine.coding_create, False),
    "coding_agent": (EngineeringEngine.coding_agent, False),
    "coding_chat": (EngineeringEngine.coding_chat, False),
    "coding_diagnose": (EngineeringEngine.coding_diagnose, False),
    "coding_refactor": (EngineeringEngine.coding_refactor, False),
    "code_index": (EngineeringEngine.code_index, False),
    "code_search": (EngineeringEngine.code_search, False),
    "syntax_check": (EngineeringEngine.syntax_check, False),
    "coding_task": (EngineeringEngine.coding_task, False),
    "extract_function": (EngineeringEngine.extract_function, False),
    "move_module": (EngineeringEngine.move_module, False),
    "rename_symbol": (EngineeringEngine.rename_symbol, False),
    "find_references": (EngineeringEngine.find_references, True),
    "coding_run_tests": (EngineeringEngine.coding_run_tests, False),
    "coding_run_command": (EngineeringEngine.coding_run_command, False),
    "coding_editor_status": (EngineeringEngine.coding_editor_status, True),
    "coding_explain_selection": (EngineeringEngine.coding_explain_selection, False),
    "coding_lsp": (EngineeringEngine.coding_lsp, False),
    "lsp_definition": (EngineeringEngine.lsp_definition, False),
    "lsp_references": (EngineeringEngine.lsp_references, False),
    "lsp_hover": (EngineeringEngine.lsp_hover, False),
    "lsp_format": (EngineeringEngine.lsp_format, False),
    "lsp_symbols": (EngineeringEngine.lsp_symbols, True),
}

_ENGINEERING_DEPENDENCIES = ["workflow_manager", "capability_registry", "retrieval"]


def get_engineering_behavior() -> EngineeringBehavior | None:
    from jarvis.behaviors import get_behavior

    behavior = get_behavior("engineering")
    return behavior if isinstance(behavior, EngineeringBehavior) else None


def engineering_context(orchestrator: Any) -> EngineeringContext:
    return EngineeringContext.from_orchestrator(orchestrator)


@register_behavior
class EngineeringBehavior(ApplicationBehavior):
    def __init__(self) -> None:
        super().__init__(
            behavior_id="engineering",
            name="Engineering",
            category="Coding",
            description="Coding agent, git, LSP, refactoring, and semantic code index",
            module_path="jarvis.behaviors.engineering",
            test_module="tests.test_behaviors",
            action_names=list(_ENGINEERING_ACTIONS.keys()),
            dependencies=list(_ENGINEERING_DEPENDENCIES),
            stability="stable",
            owner="application",
            version="1.0.0",
        )
        self._context: EngineeringContext | None = None

    def initialize(self, orchestrator: Any) -> None:
        self._context = EngineeringContext.from_orchestrator(orchestrator)

    def attach(self) -> list[str]:
        for action, (handler, info) in _ENGINEERING_ACTIONS.items():
            register_action(
                action,
                info=info,
                module="coding",
                description=action.replace("_", " "),
            )(self._bind(handler))
        return []

    def validate(self) -> list[str]:
        checks = {
            "workflow_manager": "JARVIS_PLATFORM_WORKFLOW_ORCHESTRATION_ATTACHED",
            "capability_registry": "JARVIS_PLATFORM_TOOL_CAPABILITY_ATTACHED",
            "retrieval": "JARVIS_PLATFORM_KNOWLEDGE_RETRIEVAL_ATTACHED",
        }
        warnings: list[str] = []
        for dep in self.dependencies:
            env_key = checks.get(dep)
            if env_key and os.getenv(env_key) != "1":
                warnings.append(f"dependency not attached: {dep}")
        return warnings

    def execute(
        self,
        orchestrator: Any,
        action: str,
        params: dict,
        message: str,
    ) -> dict | None:
        spec = _ENGINEERING_ACTIONS.get(action)
        if spec is None:
            return None
        handler, _info = spec
        self.initialize(orchestrator)
        ctx = self._context or EngineeringContext.from_orchestrator(orchestrator)
        return handler(ctx, params, message)

    def health(self) -> dict[str, Any]:
        report = super().health()
        report["validation_warnings"] = self.validate()
        report["stability"] = self.stability
        report["owner"] = self.owner
        report["version"] = self.version
        return report

    def shutdown(self) -> None:
        self._context = None

    def _bind(self, handler):
        def _entry(orchestrator, params: dict, message: str) -> dict:
            self.initialize(orchestrator)
            ctx = self._context or EngineeringContext.from_orchestrator(orchestrator)
            return handler(ctx, params, message)

        return _entry
