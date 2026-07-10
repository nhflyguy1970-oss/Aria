"""Knowledge engine — retrieval context, RAG, documents, and web search."""

from __future__ import annotations

from jarvis import llm
from jarvis.behaviors.knowledge._extracted import KnowledgeOperations
from jarvis.behaviors.knowledge.context import KnowledgeContext


class KnowledgeEngine(KnowledgeOperations):
    """Isolated knowledge domain logic."""

    @classmethod
    def prepare_context(
        cls,
        ctx: KnowledgeContext,
        message: str,
        *,
        general: bool = False,
        skip_project_context: bool = False,
    ) -> tuple[list[str], list[dict], list[str]]:
        parts: list[str] = []
        citations: list[dict] = []
        warnings: list[str] = []

        if not llm.embed_available():
            warnings.append(
                f"Semantic memory/RAG unavailable — check embed model `{llm.embed_model()}`."
            )

        from jarvis.router import is_codebase_question

        if not skip_project_context and is_codebase_question(message, ctx.session):
            from jarvis import rag

            doc_ctx, rag_warnings = rag.context_for_query(message)
            warnings.extend(rag_warnings)
            if doc_ctx:
                parts.append(doc_ctx)

        from jarvis.knowledge import context_for_query as knowledge_context

        k_ctx, k_warnings = knowledge_context(message)
        warnings.extend(k_warnings)
        if k_ctx:
            parts.append(k_ctx)

        if not skip_project_context and not general:
            from jarvis.document_learning import document_learning_context_for_chat

            doc_learn_ctx = document_learning_context_for_chat(ctx.memory, message)
            if doc_learn_ctx:
                parts.append(doc_learn_ctx)

            from jarvis.documents_rag import context_for_query as library_context

            lib_ctx, lib_warnings = library_context(message)
            warnings.extend(lib_warnings)
            if lib_ctx:
                parts.append(lib_ctx)

        from jarvis import web_search
        from jarvis.profiles import web_search_disabled
        from jarvis.runtime_routing import is_runtime_routing_question

        if (
            not general
            and not is_runtime_routing_question(message)
            and not web_search_disabled()
            and web_search.auto_search_enabled()
            and web_search.should_auto_search(message)
        ):
            hits = web_search.search(message, limit=5)
            if hits:
                parts.append(
                    "Web search snippets (cite [n] if used; say if insufficient):\n"
                    + web_search.format_results_for_llm(hits)
                )

        return parts, citations, warnings
