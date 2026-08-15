"""Long-term memory platform facade — episodic/semantic/procedural ops + I/O."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

log = logging.getLogger("jarvis.intelligence.memory_platform")


def memory_status() -> dict[str, Any]:
    """Aggregate memory subsystem health without requiring ACM to be loaded."""
    status: dict[str, Any] = {"ok": True, "subsystems": {}}
    try:
        from jarvis.memory.hierarchy import MemoryHierarchy

        h = MemoryHierarchy()
        status["subsystems"]["hierarchy"] = {"ok": True, "class": type(h).__name__}
    except Exception as exc:
        status["subsystems"]["hierarchy"] = {"ok": False, "error": str(exc)}
        status["ok"] = False

    try:
        from jarvis import memory_consolidation

        status["subsystems"]["consolidation"] = {
            "ok": True,
            "module": memory_consolidation.__name__,
        }
    except Exception as exc:
        status["subsystems"]["consolidation"] = {"ok": False, "error": str(exc)}

    try:
        from jarvis.modules import memory_embeddings

        status["subsystems"]["embeddings"] = {
            "ok": True,
            "module": memory_embeddings.__name__,
        }
    except Exception as exc:
        status["subsystems"]["embeddings"] = {"ok": False, "error": str(exc)}

    try:
        from jarvis.modules.graph_store import resolve_graph_backend

        status["subsystems"]["graph"] = {"ok": True, "backend": resolve_graph_backend()}
    except Exception as exc:
        status["subsystems"]["graph"] = {"ok": False, "error": str(exc)}

    return status


def consolidate_memories(*, force: bool = False) -> dict[str, Any]:
    """Run consolidation / aging pipelines when available."""
    started = time.time()
    try:
        from jarvis import memory_consolidation

        fn = getattr(memory_consolidation, "run_consolidation", None) or getattr(
            memory_consolidation, "consolidate", None
        )
        if not callable(fn):
            return {
                "ok": True,
                "result": {"skipped": True, "reason": "no consolidate entrypoint"},
                "elapsed_ms": int((time.time() - started) * 1000),
            }
        try:
            import inspect

            sig = inspect.signature(fn)
            kwargs = {}
            if "force" in sig.parameters:
                kwargs["force"] = force
            if "memory_store" in sig.parameters:
                # Cannot invent a store — skip gracefully
                return {
                    "ok": True,
                    "result": {"skipped": True, "reason": "memory_store required"},
                    "elapsed_ms": int((time.time() - started) * 1000),
                }
            result = fn(**kwargs) if kwargs else fn()
        except TypeError:
            return {
                "ok": True,
                "result": {"skipped": True, "reason": "incompatible consolidate signature"},
                "elapsed_ms": int((time.time() - started) * 1000),
            }
        return {
            "ok": True,
            "result": result if isinstance(result, dict) else {"detail": str(result)[:1000]},
            "elapsed_ms": int((time.time() - started) * 1000),
        }
    except Exception as exc:
        log.exception("memory consolidation failed")
        return {"ok": False, "error": str(exc), "elapsed_ms": int((time.time() - started) * 1000)}


def export_memories(*, limit: int = 500) -> dict[str, Any]:
    """Retired API: ACM owns memory export/import contracts."""
    del limit
    return {"ok": False, "error": "retired_memory_platform_export", "status": "retired"}


def import_memories(path: str | Path) -> dict[str, Any]:
    """Retired API: ACM owns memory export/import contracts."""
    del path
    return {"ok": False, "error": "retired_memory_platform_import", "status": "retired"}


def search_memories(query: str, *, limit: int = 10) -> dict[str, Any]:
    """Retired API: use ACM-backed memory read paths instead."""
    del limit
    q = (query or "").strip()
    return {"ok": False, "query": q, "error": "retired_memory_platform_search", "status": "retired", "results": []}
