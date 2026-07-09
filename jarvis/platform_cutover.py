"""Platform migration cutover — safe authority switch with rollback."""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

logger = logging.getLogger("jarvis.platform_cutover")

_CUTOVER_FILE = DATA_DIR / "platform" / "cutover.json"
_APPLICATION_ID = "aria"
_MODES = frozenset({"legacy", "dual_write", "platform_authoritative"})
_MIN_SHADOW_AGREEMENT_RATE = 0.95


def _default_state() -> dict[str, Any]:
    return {
        "version": 1,
        "mode": "dual_write",
        "backfill_completed_at": "",
        "enabled_at": "",
        "rollback_count": 0,
        "last_verification": {},
    }


def _load() -> dict[str, Any]:
    if not _CUTOVER_FILE.is_file():
        return _default_state()
    try:
        data = json.loads(_CUTOVER_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {**_default_state(), **data}
    except (json.JSONDecodeError, OSError):
        pass
    return _default_state()


def _save(data: dict[str, Any]) -> None:
    _CUTOVER_FILE.parent.mkdir(parents=True, exist_ok=True)
    _CUTOVER_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _env_truthy(name: str) -> bool:
    return os.getenv(name, "").lower() in ("1", "true", "yes")


def current_mode() -> str:
    if _env_truthy("JARVIS_PLATFORM_DATA_AUTHORITATIVE"):
        return "platform_authoritative"
    mode = str(_load().get("mode") or "dual_write")
    return mode if mode in _MODES else "dual_write"


def platform_data_authoritative() -> bool:
    return current_mode() == "platform_authoritative"


def apply_cutover_state_on_startup() -> dict[str, Any]:
    """Hydrate authoritative env from persisted cutover state before platform attach."""
    state = _load()
    mode = str(state.get("mode") or "dual_write")
    if mode != "platform_authoritative":
        return {"applied": False, "mode": mode}

    if not _env_truthy("JARVIS_PLATFORM_DATA_AUTHORITATIVE"):
        os.environ["JARVIS_PLATFORM_DATA_AUTHORITATIVE"] = "1"

    logger.info(
        "Platform cutover state hydrated from %s (mode=platform_authoritative)",
        _CUTOVER_FILE,
    )
    return {
        "applied": True,
        "mode": "platform_authoritative",
        "cutover_file": str(_CUTOVER_FILE),
    }


def _check_memory_layer() -> tuple[dict[str, Any], list[str], list[str]]:
    layer: dict[str, Any] = {"ok": True}
    blockers: list[str] = []
    warnings: list[str] = []

    if os.getenv("JARVIS_PLATFORM_MEMORY_ATTACHED") != "1":
        layer["ok"] = False
        blockers.append("platform memory adapter not attached")
        return layer, blockers, warnings

    metrics: dict[str, Any] = {}
    try:
        from aiplatform.applications.memory.metrics import metrics_view

        metrics = metrics_view(_APPLICATION_ID).to_dict()
        layer["metrics"] = metrics
        failures = int(metrics.get("verification_failures") or 0)
        if failures > 0:
            layer["ok"] = False
            blockers.append(f"memory verification failures: {failures}")
    except Exception as exc:
        layer["ok"] = False
        warnings.append(f"memory metrics unavailable: {exc}")

    try:
        from aiplatform.applications.manager import manager as application_manager
        from aiplatform.applications.memory.validator import namespace_status

        app = application_manager.get(_APPLICATION_ID)
        if app is not None:
            required, bridged, missing = namespace_status(app)
            layer["namespaces"] = {
                "required": required,
                "bridged": bridged,
                "missing": missing,
            }
            if missing:
                layer["ok"] = False
                blockers.append(f"memory namespaces not bridged: {', '.join(missing)}")
    except Exception as exc:
        warnings.append(f"memory namespace check unavailable: {exc}")

    return layer, blockers, warnings


def _check_semantic_layer() -> tuple[dict[str, Any], list[str], list[str]]:
    layer: dict[str, Any] = {"ok": True, "attached": False}
    blockers: list[str] = []
    warnings: list[str] = []

    if os.getenv("JARVIS_PLATFORM_SEMANTIC_MEMORY_ATTACHED") != "1":
        layer["skipped"] = True
        return layer, blockers, warnings

    layer["attached"] = True
    try:
        from aiplatform.applications.semantic.metrics import metrics_view

        metrics = metrics_view(_APPLICATION_ID).to_dict()
        layer["metrics"] = metrics
        read_failures = int(metrics.get("read_verification_failures") or 0)
        embed_failures = int(metrics.get("embedding_verification_failures") or 0)
        verify_failures = int(metrics.get("verification_failures") or 0)
        if read_failures > 0:
            layer["ok"] = False
            blockers.append(f"semantic read verification failures: {read_failures}")
        if embed_failures > 0:
            layer["ok"] = False
            blockers.append(f"semantic embedding verification failures: {embed_failures}")
        if verify_failures > 0:
            layer["ok"] = False
            blockers.append(f"semantic verification failures: {verify_failures}")
    except Exception as exc:
        layer["ok"] = False
        warnings.append(f"semantic metrics unavailable: {exc}")

    return layer, blockers, warnings


def _check_knowledge_layer() -> tuple[dict[str, Any], list[str], list[str]]:
    layer: dict[str, Any] = {"ok": True, "attached": False}
    blockers: list[str] = []
    warnings: list[str] = []

    if os.getenv("JARVIS_PLATFORM_KNOWLEDGE_RETRIEVAL_ATTACHED") != "1":
        layer["skipped"] = True
        return layer, blockers, warnings

    layer["attached"] = True
    try:
        from aiplatform.applications.knowledge_retrieval.metrics import metrics_view

        metrics = metrics_view(_APPLICATION_ID).to_dict()
        layer["metrics"] = metrics
        failures = int(metrics.get("retrieval_verification_failures") or 0)
        if failures > 0:
            layer["ok"] = False
            blockers.append(f"knowledge retrieval verification failures: {failures}")

        comparisons = int(metrics.get("shadow_retrieval_comparisons") or 0)
        agreements = int(metrics.get("retrieval_agreements") or 0)
        if comparisons > 0:
            rate = agreements / comparisons
            layer["shadow_agreement_rate"] = round(rate, 4)
            if rate < _MIN_SHADOW_AGREEMENT_RATE:
                layer["ok"] = False
                blockers.append(
                    f"knowledge shadow agreement too low: {rate:.1%} "
                    f"(minimum {_MIN_SHADOW_AGREEMENT_RATE:.0%})"
                )
    except Exception as exc:
        layer["ok"] = False
        warnings.append(f"knowledge metrics unavailable: {exc}")

    return layer, blockers, warnings


def _check_backfill_gate() -> tuple[dict[str, Any], list[str], list[str]]:
    state = _load()
    stats = state.get("backfill_stats") or {}
    layer = {
        "ok": True,
        "completed_at": state.get("backfill_completed_at") or "",
        "stats": stats,
    }
    blockers: list[str] = []
    warnings: list[str] = []

    if not layer["completed_at"]:
        layer["ok"] = False
        blockers.append("memory backfill has not completed")
    else:
        errors = int(stats.get("errors") or 0)
        total = int(stats.get("total") or 0)
        mirrored = int(stats.get("mirrored") or 0)
        if errors > 0:
            layer["ok"] = False
            blockers.append(f"memory backfill errors: {errors}")
        elif total > 0 and mirrored < total:
            layer["ok"] = False
            blockers.append(f"memory backfill incomplete: {mirrored}/{total} mirrored")

    return layer, blockers, warnings


def verify_data_parity() -> dict[str, Any]:
    """Compare legacy memory inventory with platform mirror."""
    state = _load()
    stats = state.get("backfill_stats") or {}
    legacy_count = 0
    platform_count = 0
    contentful_legacy = 0
    error = ""
    try:
        from jarvis.assistant_instance import get_assistant

        legacy_store = _legacy_memory_store(get_assistant().memory)
        if hasattr(legacy_store, "list_entries"):
            entries = legacy_store.list_entries()
            legacy_count = len(entries)
            contentful_legacy = sum(
                1
                for e in entries
                if str(e.get("id", "")).strip() and str(e.get("content", "")).strip()
            )
    except Exception as exc:
        error = str(exc)[:200]

    if os.getenv("JARVIS_PLATFORM_MEMORY_ATTACHED") == "1":
        try:
            platform_count = _platform_memory_count(_APPLICATION_ID)
        except Exception as exc:
            if not error:
                error = str(exc)[:200]

    mirrored = int(stats.get("mirrored") or 0)
    total = int(stats.get("total") or 0)
    ok = (
        not error
        and mirrored >= contentful_legacy
        and platform_count >= contentful_legacy
        and (total == 0 or total == legacy_count)
    )
    return {
        "ok": ok,
        "legacy_count": legacy_count,
        "contentful_legacy": contentful_legacy,
        "platform_count": platform_count,
        "mirrored": mirrored,
        "backfill_total": total,
        "error": error,
    }


def verify_readiness(*, persist: bool = True) -> dict[str, Any]:
    """Check whether platform cutover is safe."""
    blockers: list[str] = []
    warnings: list[str] = []
    layers: dict[str, Any] = {}

    if _env_truthy("JARVIS_DISABLE_PLATFORM_ATTACHMENT"):
        blockers.append("platform attachment disabled")

    if os.getenv("JARVIS_PLATFORM_ATTACHED") != "1":
        blockers.append("platform infrastructure not attached")

    legacy_path = Path(os.getenv("JARVIS_LEGACY_DATA_DIR", str(DATA_DIR)))
    if not legacy_path.is_dir():
        blockers.append(f"legacy data dir missing: {legacy_path}")

    platform_path = os.getenv("JARVIS_PLATFORM_DATA_DIR", "")
    if not platform_path:
        blockers.append("platform data dir not configured")
    elif not Path(platform_path).is_dir():
        blockers.append(f"platform data dir missing: {platform_path}")

    memory_layer, mem_blockers, mem_warnings = _check_memory_layer()
    layers["memory"] = memory_layer
    blockers.extend(mem_blockers)
    warnings.extend(mem_warnings)

    semantic_layer, sem_blockers, sem_warnings = _check_semantic_layer()
    layers["semantic"] = semantic_layer
    blockers.extend(sem_blockers)
    warnings.extend(sem_warnings)

    knowledge_layer, know_blockers, know_warnings = _check_knowledge_layer()
    layers["knowledge"] = knowledge_layer
    blockers.extend(know_blockers)
    warnings.extend(know_warnings)

    backfill_layer, backfill_blockers, backfill_warnings = _check_backfill_gate()
    layers["backfill"] = backfill_layer
    blockers.extend(backfill_blockers)
    warnings.extend(backfill_warnings)

    parity = verify_data_parity()
    layers["parity"] = parity
    if not parity.get("ok") and parity.get("contentful_legacy", parity.get("legacy_count", 0)) > 0:
        if parity.get("platform_count", 0) < parity.get("contentful_legacy", 0):
            blockers.append(
                "memory parity mismatch: "
                f"legacy={parity.get('contentful_legacy', parity.get('legacy_count'))} "
                f"platform={parity.get('platform_count', 0)} "
                f"mirrored={parity.get('mirrored')}"
            )

    ready = not blockers
    result = {
        "ready": ready,
        "blockers": blockers,
        "warnings": warnings,
        "layers": layers,
        "ts": time.time(),
    }
    if persist:
        state = _load()
        state["last_verification"] = result
        _save(state)
    return result


def _platform_memory_count(application_id: str = _APPLICATION_ID) -> int:
    try:
        from aiplatform.memory.manager import manager as memory_manager

        provider = memory_manager.provider
        if provider is None:
            return 0
        query = memory_manager._build_query(application=application_id, top_k=1_000_000)
        return provider.count(query)
    except Exception:
        return 0


def _legacy_memory_store(mem: Any) -> Any:
    """Return the legacy JsonMemoryStore regardless of adapter wrapping."""
    legacy = getattr(mem, "_legacy", None)
    if legacy is not None and hasattr(legacy, "list_entries"):
        return legacy
    return mem


def ensure_memory_namespaces() -> dict[str, str]:
    """Register required namespace aliases on the running process."""
    try:
        from aiplatform.applications.memory.metrics import ensure_namespace_mappings

        return ensure_namespace_mappings(_APPLICATION_ID)
    except Exception as exc:
        logger.warning("ensure_memory_namespaces failed: %s", exc)
        return {}


def backfill_memory(*, dry_run: bool = False) -> dict[str, Any]:
    """Mirror existing legacy memory entries to platform storage."""
    if os.getenv("JARVIS_PLATFORM_MEMORY_ATTACHED") != "1":
        return {"ok": False, "error": "platform memory not attached"}

    try:
        ensure_memory_namespaces()
        from jarvis.assistant_instance import get_assistant

        mem = _legacy_memory_store(get_assistant().memory)
        if not hasattr(mem, "list_entries"):
            return {"ok": False, "error": "memory store has no list_entries"}
        entries = mem.list_entries()
        if dry_run:
            namespaces: dict[str, int] = {}
            for entry in entries:
                ns = str(entry.get("namespace") or "default")
                namespaces[ns] = namespaces.get(ns, 0) + 1
            return {
                "ok": True,
                "dry_run": True,
                "entries": len(entries),
                "namespaces": namespaces,
            }

        from aiplatform.applications.memory.bridge import mirror_add

        mirrored = 0
        errors = 0
        skipped = 0
        for entry in entries:
            content = str(entry.get("content", "")).strip()
            entry_id = str(entry.get("id", "")).strip()
            if not content or not entry_id:
                skipped += 1
                continue
            try:
                mirror_add(_APPLICATION_ID, entry)
                mirrored += 1
            except Exception as exc:
                errors += 1
                logger.debug("backfill entry failed: %s", exc)

        state = _load()
        state["backfill_completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        state["backfill_stats"] = {
            "mirrored": mirrored,
            "errors": errors,
            "skipped": skipped,
            "total": len(entries),
        }
        _save(state)
        return {
            "ok": errors == 0 and mirrored + skipped == len(entries),
            "mirrored": mirrored,
            "errors": errors,
            "skipped": skipped,
            "total": len(entries),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def verify_memory_records(*, sample_limit: int = 0) -> dict[str, Any]:
    """Verify every legacy memory record exists on platform with matching fields."""
    if os.getenv("JARVIS_PLATFORM_MEMORY_ATTACHED") != "1":
        return {"ok": False, "error": "platform memory not attached"}

    try:
        from aiplatform.applications.memory.bridge import (
            map_memory_type,
            map_namespace,
            verify_platform_record,
        )
        from aiplatform.memory.manager import manager as memory_manager

        from jarvis.assistant_instance import get_assistant

        legacy_store = _legacy_memory_store(get_assistant().memory)
        entries = legacy_store.list_entries()
        if sample_limit > 0:
            entries = entries[:sample_limit]

        missing: list[str] = []
        content_mismatch: list[str] = []
        namespace_mismatch: list[str] = []
        metadata_issues: list[str] = []
        skipped: list[str] = []
        namespaces: dict[str, int] = {}
        verified = 0

        for entry in entries:
            entry_id = str(entry.get("id", "")).strip()
            content = str(entry.get("content", "")).strip()
            ns = map_namespace(entry.get("namespace"))
            namespaces[ns] = namespaces.get(ns, 0) + 1
            if not entry_id or not content:
                skipped.append(entry_id or "(no-id)")
                continue

            platform_record = memory_manager.get(entry_id)
            if platform_record is None:
                missing.append(entry_id)
                continue

            ok, reason = verify_platform_record(platform_record, entry)
            if not ok:
                if reason == "content mismatch":
                    content_mismatch.append(entry_id)
                elif reason == "namespace mismatch":
                    namespace_mismatch.append(entry_id)
                else:
                    metadata_issues.append(f"{entry_id}:{reason}")
                continue

            meta = getattr(platform_record, "metadata", None) or {}
            legacy_type = str(entry.get("type", "fact"))
            if str(meta.get("jarvis_type", "")) != legacy_type:
                metadata_issues.append(f"{entry_id}:jarvis_type")
            legacy_ts = str(entry.get("timestamp", ""))
            if legacy_ts and str(meta.get("jarvis_timestamp", "")) != legacy_ts:
                metadata_issues.append(f"{entry_id}:timestamp")
            expected_mem_type = map_memory_type(legacy_type)
            if str(getattr(platform_record, "memory_type", "")) != expected_mem_type:
                metadata_issues.append(f"{entry_id}:memory_type")
            verified += 1

        platform_count = _platform_memory_count(_APPLICATION_ID)
        ok = not (missing or content_mismatch or namespace_mismatch or metadata_issues)
        return {
            "ok": ok,
            "legacy_total": len(legacy_store.list_entries()),
            "checked": len(entries),
            "verified": verified,
            "skipped": len(skipped),
            "platform_count": platform_count,
            "namespaces": namespaces,
            "missing": missing[:20],
            "missing_count": len(missing),
            "content_mismatch_count": len(content_mismatch),
            "namespace_mismatch_count": len(namespace_mismatch),
            "metadata_issue_count": len(metadata_issues),
            "metadata_issues": metadata_issues[:20],
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def verify_dual_read(*, sample_size: int = 25) -> dict[str, Any]:
    """Compare legacy get() vs platform get() for a sample of entries."""
    if os.getenv("JARVIS_PLATFORM_MEMORY_ATTACHED") != "1":
        return {"ok": False, "error": "platform memory not attached"}

    try:
        from aiplatform.memory.manager import manager as memory_manager

        from jarvis.assistant_instance import get_assistant

        legacy_store = _legacy_memory_store(get_assistant().memory)
        entries = [
            e
            for e in legacy_store.list_entries()
            if str(e.get("id", "")).strip() and str(e.get("content", "")).strip()
        ]
        sample = entries[:sample_size] if sample_size > 0 else entries
        mismatches: list[str] = []
        for entry in sample:
            entry_id = str(entry["id"])
            legacy = legacy_store.get(entry_id)
            platform = memory_manager.get(entry_id)
            if platform is None:
                mismatches.append(f"{entry_id}:platform_missing")
                continue
            if str(legacy.get("content", "")).strip() != str(platform.content or "").strip():
                mismatches.append(f"{entry_id}:content")
        return {
            "ok": not mismatches,
            "sampled": len(sample),
            "mismatches": mismatches[:20],
            "mismatch_count": len(mismatches),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def verify_semantic_parity(*, sample_size: int = 50) -> dict[str, Any]:
    """Verify legacy vectors exist on platform; reset stale verification counters when aligned."""
    if os.getenv("JARVIS_PLATFORM_SEMANTIC_MEMORY_ATTACHED") != "1":
        return {"ok": False, "error": "platform semantic memory not attached"}

    try:
        _ensure_semantic_vector_store()
        from aiplatform.applications.semantic.bridge import verify_embedding
        from aiplatform.applications.semantic.metrics import (
            metrics_view,
            reset_verification_counters,
        )

        from jarvis.config import MEMORY_VECTORS_FILE
        from jarvis.modules.vector_store import SqliteVectorStore

        legacy_store = SqliteVectorStore(path=MEMORY_VECTORS_FILE)
        entries = legacy_store.iter_entries()
        legacy_total = len(entries)
        sample = entries if sample_size <= 0 else entries[:sample_size]
        missing: list[str] = []
        embedding_issues: list[str] = []

        from aiplatform.vectorstore import manager as vector_store_manager

        platform_chunks = {
            chunk_id: chunk for chunk_id, chunk in vector_store_manager.store.list_chunks()
        }
        platform_total = len(platform_chunks)
        counters_reset = None
        metrics_ok = True
        for row in sample:
            memory_id = str(row.get("memory_id", ""))
            if not memory_id:
                continue
            chunk = platform_chunks.get(memory_id)
            if chunk is None:
                missing.append(memory_id)
                continue
            ok, reason = verify_embedding(row.get("vector") or [], chunk.embedding)
            if not ok:
                embedding_issues.append(f"{memory_id}:{reason}")

        if not missing and not embedding_issues and platform_total >= legacy_total:
            counters_reset = reset_verification_counters(_APPLICATION_ID)
            metrics = metrics_view(_APPLICATION_ID)
            metrics_ok = int(metrics.read_verification_failures) == 0

        return {
            "ok": (
                not missing
                and not embedding_issues
                and platform_total >= legacy_total
                and metrics_ok
            ),
            "legacy_total": legacy_total,
            "platform_total": platform_total,
            "sampled": len(sample),
            "missing_count": len(missing),
            "embedding_issue_count": len(embedding_issues),
            "counters_reset": counters_reset,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def verify_cutover_complete(*, persist: bool = True) -> dict[str, Any]:
    """Full cutover verification without enabling platform-authoritative mode."""
    ensure_memory_namespaces()
    semantic_parity = verify_semantic_parity(sample_size=50)
    readiness = verify_readiness(persist=False)
    memory_records = verify_memory_records()
    dual_read = verify_dual_read()
    parity = verify_data_parity()

    blockers = list(readiness.get("blockers") or [])
    if not memory_records.get("ok"):
        blockers.append(
            "memory record verification failed: "
            f"missing={memory_records.get('missing_count', 0)} "
            f"content={memory_records.get('content_mismatch_count', 0)} "
            f"metadata={memory_records.get('metadata_issue_count', 0)}"
        )
    if not dual_read.get("ok"):
        blockers.append(
            f"dual-read verification failed: {dual_read.get('mismatch_count', 0)} mismatches"
        )
    if os.getenv("JARVIS_PLATFORM_SEMANTIC_MEMORY_ATTACHED") == "1" and not semantic_parity.get(
        "ok"
    ):
        blockers.append(
            "semantic parity verification failed: "
            f"legacy={semantic_parity.get('legacy_total', 0)} "
            f"platform={semantic_parity.get('platform_total', 0)} "
            f"missing={semantic_parity.get('missing_count', 0)}"
        )

    ready = not blockers
    result = {
        "ready": ready,
        "blockers": blockers,
        "warnings": readiness.get("warnings") or [],
        "readiness": readiness,
        "memory_records": memory_records,
        "dual_read": dual_read,
        "semantic_parity": semantic_parity,
        "parity": parity,
        "mode": current_mode(),
        "ts": time.time(),
    }
    if persist:
        state = _load()
        state["last_full_verification"] = result
        _save(state)
    return result


def _ensure_semantic_vector_store() -> str:
    try:
        from aiplatform.applications.semantic.manager import manager as semantic_manager

        return semantic_manager.ensure_process_vector_store(_APPLICATION_ID)
    except Exception as exc:
        logger.warning("Could not ensure semantic vector store: %s", exc)
        return ""


def backfill_semantic_vectors(*, dry_run: bool = False) -> dict[str, Any]:
    """Mirror legacy embedding vectors into the platform vector store."""
    if os.getenv("JARVIS_PLATFORM_SEMANTIC_MEMORY_ATTACHED") != "1":
        return {"ok": False, "error": "platform semantic memory not attached"}

    try:
        index_path = _ensure_semantic_vector_store()
        from jarvis.config import MEMORY_VECTORS_FILE
        from jarvis.modules.vector_store import SqliteVectorStore

        store = SqliteVectorStore(path=MEMORY_VECTORS_FILE)
        entries = store.iter_entries()
        if dry_run:
            return {"ok": True, "dry_run": True, "vectors": len(entries)}

        from aiplatform.applications.semantic.bridge import mirror_upsert
        from aiplatform.applications.semantic.metrics import reset_verification_counters

        mirrored = 0
        errors = 0
        for row in entries:
            try:
                mirror_upsert(
                    _APPLICATION_ID,
                    row["memory_id"],
                    row["vector"],
                    namespace=row.get("namespace", "default"),
                    entry_type=row.get("entry_type", "fact"),
                )
                mirrored += 1
            except Exception as exc:
                errors += 1
                logger.debug("semantic backfill failed for %s: %s", row.get("memory_id"), exc)

        reset = reset_verification_counters(_APPLICATION_ID)
        from aiplatform.vectorstore import manager as vector_store_manager

        vector_store_manager.save_state()
        state = _load()
        state["semantic_backfill_completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        state["semantic_backfill_stats"] = {
            "mirrored": mirrored,
            "errors": errors,
            "total": len(entries),
            "reset_counters": reset,
            "index_path": index_path,
        }
        _save(state)
        return {"ok": errors == 0, "mirrored": mirrored, "errors": errors, "total": len(entries)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def classify_cutover_failures(verification: dict[str, Any] | None = None) -> dict[str, Any]:
    """Classify cutover blockers by root cause category."""
    data = verification or verify_readiness(persist=False)
    categories: dict[str, list[str]] = {
        "missing_vectors": [],
        "stale_vectors": [],
        "namespace_mismatch": [],
        "embedding_mismatch": [],
        "migration_bug": [],
        "backfill_incomplete": [],
        "attachment": [],
        "other": [],
    }
    for blocker in data.get("blockers") or []:
        low = blocker.lower()
        if "namespace" in low and ("bridg" in low or "missing" in low):
            categories["namespace_mismatch"].append(blocker)
        elif "platform vector missing" in low or "read verification failures" in low:
            categories["missing_vectors"].append(blocker)
        elif "embedding" in low:
            categories["embedding_mismatch"].append(blocker)
        elif "backfill" in low or "parity mismatch" in low:
            categories["backfill_incomplete"].append(blocker)
        elif "not attached" in low or "not configured" in low:
            categories["attachment"].append(blocker)
        else:
            categories["other"].append(blocker)

    layers = data.get("layers") or {}
    sem = layers.get("semantic") or {}
    metrics = sem.get("metrics") or {}
    read_failures = int(metrics.get("read_verification_failures") or 0)
    if read_failures > 0 and not categories["missing_vectors"]:
        categories["missing_vectors"].append(
            f"semantic read verification failures: {read_failures}"
        )

    return {
        "ready": bool(data.get("ready")),
        "blocker_count": len(data.get("blockers") or []),
        "categories": {k: v for k, v in categories.items() if v},
        "verification": data,
    }


def enable_platform_authoritative(*, force_backfill: bool = False) -> dict[str, Any]:
    """Switch to platform-authoritative reads. Legacy data is never deleted."""
    verification = verify_readiness()
    if not verification.get("ready"):
        return {
            "ok": False,
            "error": "cutover blocked",
            "verification": verification,
        }

    state = _load()
    if force_backfill or not state.get("backfill_completed_at"):
        backfill = backfill_memory()
        if not backfill.get("ok"):
            return {"ok": False, "error": "backfill failed", "backfill": backfill}
        verification = verify_readiness()
        if not verification.get("ready"):
            return {
                "ok": False,
                "error": "cutover blocked after backfill",
                "verification": verification,
                "backfill": backfill,
            }

    os.environ["JARVIS_PLATFORM_DATA_AUTHORITATIVE"] = "1"
    platform_dir = os.getenv("JARVIS_PLATFORM_DATA_DIR", "")
    if platform_dir:
        os.environ["JARVIS_DATA_DIR"] = platform_dir

    state["mode"] = "platform_authoritative"
    state["enabled_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _save(state)
    logger.info("Platform data cutover enabled — platform authoritative, legacy preserved")
    return {
        "ok": True,
        "mode": "platform_authoritative",
        "message": "Platform is now authoritative. Legacy data preserved.",
    }


def rollback_to_legacy() -> dict[str, Any]:
    """Revert to legacy-authoritative mode without data loss."""
    legacy_dir = os.getenv("JARVIS_LEGACY_DATA_DIR", str(DATA_DIR))
    os.environ.pop("JARVIS_PLATFORM_DATA_AUTHORITATIVE", None)
    os.environ["JARVIS_DATA_DIR"] = legacy_dir

    state = _load()
    state["mode"] = "dual_write"
    state["rollback_count"] = int(state.get("rollback_count") or 0) + 1
    state["last_rollback_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _save(state)
    logger.info("Rolled back to legacy-authoritative mode")
    return {
        "ok": True,
        "mode": "dual_write",
        "message": "Rolled back to legacy-authoritative mode. Platform mirror continues on writes.",
    }


def status() -> dict[str, Any]:
    state = _load()
    verification = verify_readiness()
    return {
        "ok": True,
        "mode": current_mode(),
        "state": state,
        "verification": verification,
        "legacy_data_dir": os.getenv("JARVIS_LEGACY_DATA_DIR", str(DATA_DIR)),
        "platform_data_dir": os.getenv("JARVIS_PLATFORM_DATA_DIR", ""),
        "effective_data_dir": os.getenv("JARVIS_DATA_DIR", str(DATA_DIR)),
        "platform_attached": os.getenv("JARVIS_PLATFORM_ATTACHED") == "1",
        "memory_attached": os.getenv("JARVIS_PLATFORM_MEMORY_ATTACHED") == "1",
    }


def format_status_markdown() -> str:
    snap = status()
    ver = snap.get("verification") or {}
    lines = [
        "## Platform Migration",
        f"**Mode:** `{snap.get('mode')}`",
        f"**Effective data:** `{snap.get('effective_data_dir')}`",
        f"**Ready for cutover:** {'yes' if ver.get('ready') else 'no'}",
    ]
    for blocker in ver.get("blockers") or []:
        lines.append(f"- blocker: {blocker}")
    for warning in ver.get("warnings") or []:
        lines.append(f"- warning: {warning}")
    return "\n".join(lines)
