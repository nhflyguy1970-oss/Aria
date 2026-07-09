"""Knowledge and retrieval adapter — legacy indexes remain authoritative."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from typing import Any, TypeVar

logger = logging.getLogger("jarvis.knowledge_retrieval_adapter")

_APPLICATION_ID = "aria"
T = TypeVar("T")


def knowledge_retrieval_enabled() -> bool:
    if os.getenv("JARVIS_DISABLE_PLATFORM_KNOWLEDGE_RETRIEVAL", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        return False
    if os.getenv("JARVIS_DISABLE_PLATFORM_ATTACHMENT", "").lower() in ("1", "true", "yes"):
        return False
    if os.getenv("JARVIS_PLATFORM_KNOWLEDGE_RETRIEVAL_ATTACHED") == "1":
        return True
    try:
        from jarvis.platform_knowledge_retrieval import is_knowledge_retrieval_attached

        return is_knowledge_retrieval_attached()
    except ImportError:
        return False


def _platform_retrieval_authoritative() -> bool:
    try:
        from jarvis.platform_cutover import platform_data_authoritative

        return platform_data_authoritative()
    except Exception:
        return False


def knowledge_search(
    corpus: str,
    legacy_search: Callable[..., list[dict[str, Any]]],
    query: str,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    if _platform_retrieval_authoritative():
        try:
            from aiplatform.applications.knowledge_retrieval.bridge import platform_search

            platform_results = platform_search(_APPLICATION_ID, corpus, query, limit=int(kwargs.get("limit", 5)))
            if platform_results:
                return platform_results
        except Exception as exc:
            logger.debug("platform retrieval fallback to legacy: %s", exc)

    results = legacy_search(query, **kwargs)
    if knowledge_retrieval_enabled():
        try:
            from aiplatform.applications.knowledge_retrieval.bridge import shadow_verify_retrieval
            from aiplatform.applications.knowledge_retrieval.metrics import record_legacy_retrieval

            record_legacy_retrieval(_APPLICATION_ID, corpus)
            limit = int(kwargs.get("limit", 5))
            shadow_verify_retrieval(_APPLICATION_ID, corpus, query, results, limit=limit)
        except Exception as exc:
            logger.debug("Knowledge shadow retrieval skipped: %s", exc)
    return results


def knowledge_index_build(
    corpus: str,
    legacy_build: Callable[..., list[dict[str, Any]]],
    *args: Any,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    chunks = legacy_build(*args, **kwargs)
    if knowledge_retrieval_enabled() and chunks:
        try:
            from aiplatform.applications.knowledge_retrieval.bridge import mirror_index_chunks

            mirror_index_chunks(_APPLICATION_ID, corpus, chunks)
        except Exception as exc:
            logger.warning("Knowledge index mirror failed (continuing): %s", exc)
    return chunks


def knowledge_context(
    corpus: str,
    legacy_context: Callable[..., tuple[str, list[str]]],
    query: str,
    **kwargs: Any,
) -> tuple[str, list[str]]:
    if knowledge_retrieval_enabled():
        try:
            from aiplatform.applications.knowledge_retrieval.metrics import record_legacy_retrieval

            record_legacy_retrieval(_APPLICATION_ID, corpus)
        except Exception:
            pass
    return legacy_context(query, **kwargs)
