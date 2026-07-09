"""Knowledge ingestion — watch folders and trigger indexing."""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR, PROJECT_ROOT

logger = logging.getLogger("jarvis.knowledge.ingestion")

WATCH_DIRS = (
    DATA_DIR / "documents",
    DATA_DIR / "notes",
    DATA_DIR / "youtube",
    PROJECT_ROOT / "docs",
)


def ingest_all(*, force: bool = False) -> dict[str, Any]:
    """Run indexing for all registered ingestible sources."""
    results: list[dict[str, Any]] = []
    started = time.time()

    try:
        from jarvis.documents_rag import build_index

        chunks = build_index(force=force)
        results.append({"target": "document_library", "ok": True, "chunks": len(chunks)})
    except Exception as exc:
        results.append({"target": "document_library", "ok": False, "error": str(exc)[:200]})

    try:
        from jarvis.code_index import build_index as build_code

        chunks = build_code()
        results.append({"target": "code_index", "ok": True, "chunks": len(chunks)})
    except Exception as exc:
        results.append({"target": "code_index", "ok": False, "error": str(exc)[:200]})

    try:
        from jarvis.knowledge.registry import sync_registry

        sync_registry()
        results.append({"target": "knowledge_registry", "ok": True})
    except Exception as exc:
        results.append({"target": "knowledge_registry", "ok": False, "error": str(exc)[:200]})

    elapsed = int((time.time() - started) * 1000)
    ok = all(r.get("ok") for r in results)
    return {"ok": ok, "elapsed_ms": elapsed, "results": results}


def watch_paths() -> list[str]:
    paths = []
    for p in WATCH_DIRS:
        if p.is_dir():
            paths.append(str(p))
    extra = os.getenv("JARVIS_KNOWLEDGE_WATCH_DIRS", "")
    for part in extra.split(":"):
        part = part.strip()
        if part and Path(part).is_dir():
            paths.append(part)
    return paths


def needs_ingest() -> bool:
    try:
        from jarvis.documents_rag import index_needs_rebuild

        if index_needs_rebuild():
            return True
    except Exception:
        pass
    for path in watch_paths():
        marker = Path(path)
        if not marker.is_dir():
            continue
        for item in marker.rglob("*"):
            if item.is_file() and not item.name.startswith("."):
                try:
                    if item.stat().st_mtime > time.time() - 3600:
                        return True
                except OSError:
                    continue
    return False


def maybe_scheduled_ingest() -> dict[str, Any] | None:
    """Called from nightly maintenance when auto-ingest enabled."""
    if os.getenv("JARVIS_AUTO_INGEST", "1") == "0":
        return None
    if not needs_ingest():
        return {"ok": True, "skipped": True, "reason": "indexes fresh"}
    return ingest_all(force=False)
