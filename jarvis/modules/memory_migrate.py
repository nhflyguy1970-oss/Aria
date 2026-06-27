"""Migrate JSON memory store to SQLite + embedding sidecar."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from jarvis.config import MEMORY_DB_FILE, MEMORY_FILE
from jarvis.modules.memory_embeddings import EmbeddingSidecar
from jarvis.modules.memory_sqlite import SqliteMemoryStore

logger = logging.getLogger("jarvis.memory")


def migrate_json_to_sqlite(
    json_path: Path | None = None,
    db_path: Path | None = None,
    *,
    embeddings: EmbeddingSidecar | None = None,
) -> int:
    """Import memory.json into memory.db. Returns entry count."""
    src = json_path or MEMORY_FILE
    if not src.exists():
        return 0
    try:
        payload = json.loads(src.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("JSON memory migration skipped: %s", exc)
        return 0
    entries = payload.get("entries") or []
    if not entries:
        return 0

    store = SqliteMemoryStore(path=db_path or MEMORY_DB_FILE, embeddings=embeddings)
    added = store.import_data(payload, merge=False)

    sidecar = embeddings or EmbeddingSidecar()
    for raw in entries:
        if not isinstance(raw, dict):
            continue
        eid = raw.get("id")
        emb = raw.get("embedding")
        if eid and isinstance(emb, list) and emb:
            sidecar.set(str(eid), emb)

    logger.info("Migrated %d memories from %s to SQLite", added, src)
    return added


def strip_json_embeddings(json_path: Path | None = None) -> int:
    """Move inline embeddings from memory.json to sidecar; strip from file."""
    from jarvis.modules.memory_embeddings import EmbeddingSidecar

    src = json_path or MEMORY_FILE
    if not src.exists():
        return 0
    try:
        data = json.loads(src.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return 0
    entries = data.get("entries") or []
    sidecar = EmbeddingSidecar()
    moved = 0
    for e in entries:
        emb = e.pop("embedding", None)
        eid = e.get("id")
        if eid and isinstance(emb, list) and emb:
            sidecar.set(str(eid), emb)
            moved += 1
    if moved:
        src.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return moved
