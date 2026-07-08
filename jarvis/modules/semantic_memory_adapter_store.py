"""Dual-write semantic memory adapter — legacy vectors remain authoritative."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("jarvis.semantic_memory_adapter_store")

_APPLICATION_ID = "aria"


def semantic_memory_adapter_enabled() -> bool:
    if os.getenv("JARVIS_DISABLE_PLATFORM_SEMANTIC_MEMORY", "").lower() in ("1", "true", "yes"):
        return False
    if os.getenv("JARVIS_DISABLE_PLATFORM_ATTACHMENT", "").lower() in ("1", "true", "yes"):
        return False
    if os.getenv("JARVIS_PLATFORM_SEMANTIC_MEMORY_ATTACHED") == "1":
        return True
    try:
        from jarvis.platform_semantic_memory import is_semantic_memory_attached

        return is_semantic_memory_attached()
    except ImportError:
        return False


def wrap_semantic_memory_store(legacy_store: Any, application_id: str = _APPLICATION_ID) -> Any:
    if not semantic_memory_adapter_enabled():
        return legacy_store
    return SemanticMemoryAdapter(legacy_store, application_id=application_id)


class SemanticMemoryAdapter:
    """Wrap legacy vector storage and mirror writes with shadow reads to platform."""

    def __init__(self, legacy_store: Any, application_id: str = _APPLICATION_ID) -> None:
        self._legacy = legacy_store
        self._application_id = application_id

    def __getattr__(self, name: str) -> Any:
        return getattr(self._legacy, name)

    @property
    def path(self) -> Any:
        return getattr(self._legacy, "path", None)

    @property
    def backend(self) -> str:
        return getattr(self._legacy, "backend", "sqlite")

    def _record_legacy_write(self, namespace: str = "default") -> None:
        try:
            from aiplatform.applications.semantic.metrics import record_legacy_write

            record_legacy_write(self._application_id, namespace)
        except Exception as exc:
            logger.debug("Could not record legacy semantic write: %s", exc)

    def _mirror_upsert(
        self,
        memory_id: str,
        vector: list[float],
        *,
        namespace: str = "default",
        entry_type: str = "fact",
        content: str = "",
    ) -> None:
        try:
            from aiplatform.applications.semantic.bridge import mirror_upsert

            mirror_upsert(
                self._application_id,
                memory_id,
                vector,
                namespace=namespace,
                entry_type=entry_type,
                content=content,
            )
        except Exception as exc:
            logger.warning("Platform semantic mirror upsert failed (continuing): %s", exc)

    def _mirror_delete(self, memory_ids: list[str], namespace: str = "default") -> None:
        try:
            from aiplatform.applications.semantic.bridge import mirror_delete

            mirror_delete(self._application_id, memory_ids, namespace)
        except Exception as exc:
            logger.warning("Platform semantic mirror delete failed (continuing): %s", exc)

    def _shadow_get(self, memory_id: str, legacy_vector: list[float]) -> None:
        try:
            from aiplatform.applications.semantic.bridge import shadow_verify_get

            shadow_verify_get(self._application_id, memory_id, legacy_vector)
        except Exception as exc:
            logger.debug("Semantic shadow get verification skipped: %s", exc)

    def _shadow_search(
        self,
        query_vector: list[float],
        legacy_results: list[tuple[str, float]],
        *,
        namespace: str | None,
        limit: int,
        min_score: float,
    ) -> None:
        if not query_vector:
            return
        try:
            from aiplatform.applications.semantic.bridge import shadow_verify_search
            from aiplatform.vectorstore import manager as vector_store_manager

            platform_raw = vector_store_manager.store.search(query_vector, k=limit)
            platform_results = [(chunk.id, score) for chunk, score in platform_raw if score >= min_score]
            shadow_verify_search(
                self._application_id,
                legacy_results,
                platform_results,
                namespace=namespace,
            )
        except Exception as exc:
            logger.debug("Semantic shadow search verification skipped: %s", exc)

    def get(self, memory_id: str) -> list[float]:
        legacy_vector = self._legacy.get(memory_id)
        self._shadow_get(memory_id, legacy_vector)
        return legacy_vector

    def upsert(
        self,
        memory_id: str,
        vector: list[float],
        *,
        namespace: str = "default",
        entry_type: str = "fact",
        content: str = "",
    ) -> None:
        self._legacy.upsert(
            memory_id,
            vector,
            namespace=namespace,
            entry_type=entry_type,
            content=content,
        )
        ns = namespace or "default"
        self._record_legacy_write(ns)
        self._mirror_upsert(
            memory_id,
            vector,
            namespace=ns,
            entry_type=entry_type,
            content=content,
        )

    def set(self, memory_id: str, vector: list[float]) -> None:
        self.upsert(memory_id, vector)

    def delete(self, memory_id: str) -> None:
        self._legacy.delete(memory_id)
        self._record_legacy_write("default")
        self._mirror_delete([memory_id])

    def delete_many(self, memory_ids: list[str]) -> None:
        self._legacy.delete_many(memory_ids)
        if memory_ids:
            self._record_legacy_write("default")
            self._mirror_delete(memory_ids)

    def search(
        self,
        query_vector: list[float],
        limit: int,
        *,
        namespace: str | None = None,
        min_score: float = 0.3,
    ) -> list[tuple[str, float]]:
        legacy_results = self._legacy.search(
            query_vector,
            limit,
            namespace=namespace,
            min_score=min_score,
        )
        self._shadow_search(
            query_vector,
            legacy_results,
            namespace=namespace,
            limit=limit,
            min_score=min_score,
        )
        return legacy_results

    def count(self) -> int:
        return self._legacy.count()

    def close(self) -> None:
        self._legacy.close()
