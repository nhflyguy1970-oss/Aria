"""Knowledge behavior — retrieval, RAG, documents, web search, and citations."""

from __future__ import annotations

import os
from typing import Any

from jarvis.behaviors import register_behavior
from jarvis.behaviors.knowledge.context import KnowledgeContext
from jarvis.behaviors.knowledge.engine import KnowledgeEngine
from jarvis.behaviors.lifecycle import ApplicationBehavior
from jarvis.handlers.registry import register_action

_KNOWLEDGE_ACTIONS: dict[str, tuple[Any, bool]] = {
    "web_search": (KnowledgeEngine.web_search, False),
    "document_info": (KnowledgeEngine.document_info, True),
    "document_summarize": (KnowledgeEngine.document_summarize, False),
    "document_query": (KnowledgeEngine.document_query, False),
    "document_search": (KnowledgeEngine.document_search, False),
    "learn_about": (KnowledgeEngine.learn_about, False),
    "learn_remember": (KnowledgeEngine.learn_remember, False),
    "ingest_document": (KnowledgeEngine.ingest_document, False),
    "learn_from_document": (KnowledgeEngine.learn_from_document, False),
    "learn_from_url": (KnowledgeEngine.learn_from_url, False),
    "document_learn_recall": (KnowledgeEngine.document_learn_recall, True),
    "knowledge_research_run": (KnowledgeEngine.knowledge_research_run, False),
    "knowledge_research_list": (KnowledgeEngine.knowledge_research_list, True),
    "knowledge_registry": (KnowledgeEngine.knowledge_registry, True),
    "knowledge_sync": (KnowledgeEngine.knowledge_sync, False),
    "unified_search": (KnowledgeEngine.unified_search, False),
    "knowledge_ingest": (KnowledgeEngine.knowledge_ingest, False),
}

_KNOWLEDGE_DEPENDENCIES = ["retrieval", "semantic_memory", "capability_registry"]


def get_knowledge_behavior() -> KnowledgeBehavior | None:
    from jarvis.behaviors import get_behavior

    behavior = get_behavior("knowledge")
    return behavior if isinstance(behavior, KnowledgeBehavior) else None


@register_behavior
class KnowledgeBehavior(ApplicationBehavior):
    def __init__(self) -> None:
        super().__init__(
            behavior_id="knowledge",
            name="Knowledge",
            category="Knowledge",
            description=(
                "Retrieval, RAG, document library, web search, topic learning, and context assembly"
            ),
            module_path="jarvis.behaviors.knowledge",
            test_module="tests.test_behaviors",
            action_names=list(_KNOWLEDGE_ACTIONS.keys()),
            dependencies=list(_KNOWLEDGE_DEPENDENCIES),
            stability="stable",
            owner="application",
            version="1.0.0",
        )
        self._context: KnowledgeContext | None = None

    def initialize(self, orchestrator: Any) -> None:
        self._context = KnowledgeContext.from_orchestrator(orchestrator)

    def attach(self) -> list[str]:
        for action, (handler, info) in _KNOWLEDGE_ACTIONS.items():
            module = "memory" if action.startswith(("ingest_", "learn_from", "document_learn")) else "general"
            if action.startswith("document_"):
                module = "document"
            register_action(
                action,
                info=info,
                module=module,
                description=action.replace("_", " "),
            )(self._bind(handler))
        return []

    def validate(self) -> list[str]:
        checks = {
            "retrieval": "JARVIS_PLATFORM_KNOWLEDGE_RETRIEVAL_ATTACHED",
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
        ctx = self._context or KnowledgeContext.from_orchestrator(orchestrator)
        parts, citations, warnings = KnowledgeEngine.prepare_context(
            ctx,
            message,
            general=general,
            skip_project_context=skip_project_context,
        )
        self._last_warnings = warnings
        return parts, citations

    def execute(
        self,
        orchestrator: Any,
        action: str,
        params: dict,
        message: str,
    ) -> dict | None:
        spec = _KNOWLEDGE_ACTIONS.get(action)
        if spec is None:
            return None
        handler, _info = spec
        self.initialize(orchestrator)
        ctx = self._context or KnowledgeContext.from_orchestrator(orchestrator)
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
            ctx = self._context or KnowledgeContext.from_orchestrator(orchestrator)
            return handler(ctx, params, message)

        return _entry
