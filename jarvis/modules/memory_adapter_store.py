"""Dual-write memory adapter — legacy storage remains authoritative."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("jarvis.memory_adapter_store")

_APPLICATION_ID = "aria"


def memory_adapter_enabled() -> bool:
    if os.getenv("JARVIS_DISABLE_PLATFORM_MEMORY", "").lower() in ("1", "true", "yes"):
        return False
    if os.getenv("JARVIS_DISABLE_PLATFORM_ATTACHMENT", "").lower() in ("1", "true", "yes"):
        return False
    if os.getenv("JARVIS_PLATFORM_MEMORY_ATTACHED") == "1":
        return True
    try:
        from jarvis.platform_memory import is_memory_attached

        return is_memory_attached()
    except ImportError:
        return False


def wrap_memory_store(legacy_store: Any, application_id: str = _APPLICATION_ID) -> Any:
    if not memory_adapter_enabled():
        return legacy_store
    return DualWriteMemoryAdapter(legacy_store, application_id=application_id)


class DualWriteMemoryAdapter:
    """Wrap legacy memory storage and mirror writes to AI Platform memory manager."""

    def __init__(self, legacy_store: Any, application_id: str = _APPLICATION_ID) -> None:
        self._legacy = legacy_store
        self._application_id = application_id

    def __getattr__(self, name: str) -> Any:
        return getattr(self._legacy, name)

    @property
    def path(self) -> Any:
        return getattr(self._legacy, "path", None)

    @property
    def _data(self) -> Any:
        return self._legacy._data

    def _save(self) -> None:
        self._legacy._save()

    def _record_legacy_write(self, namespace: str | None) -> None:
        try:
            from aiplatform.applications.memory.metrics import record_legacy_write

            record_legacy_write(self._application_id, namespace or "default")
        except Exception as exc:
            logger.debug("Could not record legacy memory write: %s", exc)

    def _mirror_add(self, entry: dict[str, Any]) -> None:
        try:
            from aiplatform.applications.memory.bridge import mirror_add

            mirror_add(self._application_id, entry)
        except Exception as exc:
            logger.warning("Platform memory mirror add failed (continuing): %s", exc)

    def _mirror_update(self, entry_id: str) -> None:
        legacy_entry = self._legacy.get(entry_id)
        try:
            from aiplatform.applications.memory.bridge import mirror_update

            mirror_update(self._application_id, entry_id, legacy_entry)
        except Exception as exc:
            logger.warning("Platform memory mirror update failed (continuing): %s", exc)

    def _mirror_delete(self, entry_id: str, namespace: str = "default") -> None:
        try:
            from aiplatform.applications.memory.bridge import mirror_delete

            mirror_delete(self._application_id, entry_id, namespace)
        except Exception as exc:
            logger.warning("Platform memory mirror delete failed (continuing): %s", exc)

    def _mirror_clear(
        self,
        *,
        entry_type: str | None = None,
        namespace: str | None = None,
    ) -> None:
        try:
            from aiplatform.applications.memory.bridge import mirror_clear

            mirror_clear(self._application_id, entry_type=entry_type, namespace=namespace)
        except Exception as exc:
            logger.warning("Platform memory mirror clear failed (continuing): %s", exc)

    def add(
        self,
        entry_type: str,
        content: str,
        tags: list[str] | None = None,
        *,
        namespace: str | None = None,
    ) -> dict:
        entry = self._legacy.add(entry_type, content, tags, namespace=namespace)
        self._record_legacy_write(entry.get("namespace"))
        self._mirror_add(entry)
        return entry

    def update(
        self,
        entry_id: str,
        *,
        content: str | None = None,
        entry_type: str | None = None,
        tags: list[str] | None = None,
        namespace: str | None = None,
    ) -> bool:
        updated = self._legacy.update(
            entry_id,
            content=content,
            entry_type=entry_type,
            tags=tags,
            namespace=namespace,
        )
        if updated:
            legacy_entry = self._legacy.get(entry_id)
            ns = (legacy_entry or {}).get("namespace", namespace or "default")
            self._record_legacy_write(ns)
            self._mirror_update(entry_id)
        return updated

    def delete(self, index: int) -> bool:
        entry_id = None
        namespace = "default"
        if hasattr(self._legacy, "list_entries"):
            entries = self._legacy.list_entries()
            if 0 <= index < len(entries):
                entry_id = entries[index].get("id")
                namespace = entries[index].get("namespace", "default")
        deleted = self._legacy.delete(index)
        if deleted and entry_id:
            self._record_legacy_write(namespace)
            self._mirror_delete(entry_id, namespace or "default")
        return deleted

    def delete_id(self, entry_id: str) -> bool:
        legacy_entry = self._legacy.get(entry_id)
        namespace = (legacy_entry or {}).get("namespace", "default")
        deleted = self._legacy.delete_id(entry_id)
        if deleted:
            self._record_legacy_write(namespace)
            self._mirror_delete(entry_id, namespace or "default")
        return deleted

    def clear(self, entry_type: str | None = None, namespace: str | None = None) -> int:
        count = self._legacy.clear(entry_type, namespace)
        if count:
            self._record_legacy_write(namespace or "default")
            self._mirror_clear(entry_type=entry_type, namespace=namespace)
        return count

    def prune(
        self,
        *,
        max_entries: int | None = None,
        min_relevance: float | None = None,
        namespace: str | None = None,
    ) -> int:
        before_ids = {entry.get("id") for entry in self._legacy.list_entries(namespace=namespace)}
        count = self._legacy.prune(
            max_entries=max_entries,
            min_relevance=min_relevance,
            namespace=namespace,
        )
        if count:
            after_ids = {entry.get("id") for entry in self._legacy.list_entries(namespace=namespace)}
            for entry_id in before_ids - after_ids:
                self._record_legacy_write(namespace or "default")
                self._mirror_delete(entry_id, namespace or "default")
        return count

    def import_data(self, payload: dict, *, merge: bool = True) -> int:
        before_ids = {entry.get("id") for entry in self._legacy.list_entries()}
        count = self._legacy.import_data(payload, merge=merge)
        if count:
            for entry in self._legacy.list_entries():
                if entry.get("id") not in before_ids:
                    self._record_legacy_write(entry.get("namespace"))
                    self._mirror_add(entry)
        return count

    def upsert_checkpoint(self, content: str, namespace: str = "default") -> dict:
        entry = self._legacy.upsert_checkpoint(content, namespace)
        self._record_legacy_write(entry.get("namespace", namespace))
        self._mirror_add(entry)
        return entry

    def upsert_by_tag(
        self,
        *,
        tag: str,
        entry_type: str,
        content: str,
        namespace: str,
        extra_tags: list[str] | None = None,
    ) -> dict:
        entry = self._legacy.upsert_by_tag(
            tag=tag,
            entry_type=entry_type,
            content=content,
            namespace=namespace,
            extra_tags=extra_tags,
        )
        self._record_legacy_write(entry.get("namespace", namespace))
        if entry.get("id"):
            self._mirror_update(entry["id"])
        else:
            self._mirror_add(entry)
        return entry

    def upsert_branch_summary(self, branch_id: str, content: str) -> dict:
        entry = self._legacy.upsert_branch_summary(branch_id, content)
        self._record_legacy_write(entry.get("namespace"))
        self._mirror_add(entry)
        return entry
