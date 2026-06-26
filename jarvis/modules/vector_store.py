"""Vector memory backends — sqlite (default) with optional Chroma."""

from __future__ import annotations

import logging
import os
import sqlite3
import struct
from pathlib import Path
from typing import Any, Protocol

from jarvis import config as jarvis_config
from jarvis.config import DATA_DIR

logger = logging.getLogger("jarvis.vector_store")
VECTOR_BACKENDS = ("sqlite", "chroma", "qdrant", "weaviate")
COLLECTION_NAME = "jarvis_memory"


class VectorMemoryStore(Protocol):
    backend: str

    def upsert(self, memory_id: str, vector: list[float], *, namespace: str, entry_type: str, content: str = "") -> None: ...
    def delete(self, memory_id: str) -> None: ...
    def search(self, query_vector: list[float], limit: int, *, namespace: str | None, min_score: float) -> list[tuple[str, float]]: ...
    def close(self) -> None: ...


def resolve_vector_backend() -> str:
    explicit = os.getenv("JARVIS_VECTOR_BACKEND", "").strip().lower()
    if explicit in VECTOR_BACKENDS:
        return explicit
    return "sqlite"


def _vector_root(data_dir: Path | None = None) -> Path:
    root = data_dir or DATA_DIR
    custom = os.getenv("JARVIS_VECTOR_PATH", "").strip()
    if custom:
        return Path(custom)
    return root


class SqliteVectorStore:
    backend = "sqlite"

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or jarvis_config.MEMORY_VECTORS_FILE
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS embeddings (
                memory_id TEXT PRIMARY KEY,
                dims INTEGER NOT NULL,
                vector BLOB NOT NULL,
                namespace TEXT NOT NULL DEFAULT 'default',
                entry_type TEXT NOT NULL DEFAULT 'fact'
            )
            """
        )

    def close(self) -> None:
        self._conn.close()

    @staticmethod
    def _pack(vector: list[float]) -> tuple[int, bytes]:
        dims = len(vector)
        return dims, struct.pack(f"{dims}f", *vector)

    @staticmethod
    def _unpack(dims: int, blob: bytes) -> list[float]:
        return list(struct.unpack(f"{dims}f", blob))

    def upsert(
        self,
        memory_id: str,
        vector: list[float] | None,
        *,
        namespace: str = "default",
        entry_type: str = "fact",
        content: str = "",
    ) -> None:
        if not vector:
            self.delete(memory_id)
            return
        dims, blob = self._pack(vector)
        self._conn.execute(
            """
            INSERT INTO embeddings(memory_id, dims, vector, namespace, entry_type)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(memory_id) DO UPDATE SET
                dims=excluded.dims, vector=excluded.vector,
                namespace=excluded.namespace, entry_type=excluded.entry_type
            """,
            (memory_id, dims, blob, namespace, entry_type),
        )
        self._conn.commit()

    def delete(self, memory_id: str) -> None:
        self._conn.execute("DELETE FROM embeddings WHERE memory_id = ?", (memory_id,))
        self._conn.commit()

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()
        return int(row[0]) if row else 0

    def search(
        self,
        query_vector: list[float],
        limit: int = 10,
        *,
        namespace: str | None = None,
        min_score: float = 0.0,
    ) -> list[tuple[str, float]]:
        from jarvis import llm

        sql = "SELECT memory_id, dims, vector FROM embeddings"
        params: list[Any] = []
        if namespace:
            sql += " WHERE namespace = ?"
            params.append(namespace)
        rows = self._conn.execute(sql, params).fetchall()
        scored: list[tuple[str, float]] = []
        for memory_id, dims, blob in rows:
            vec = self._unpack(int(dims), blob)
            sim = llm.cosine_similarity(query_vector, vec)
            if sim >= min_score:
                scored.append((str(memory_id), sim))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit]


def create_vector_store(data_dir: Path | None = None, *, backend: str | None = None, sqlite_path: Path | None = None):
    name = (backend or resolve_vector_backend()).lower()
    if name == "chroma":
        try:
            import chromadb  # noqa: F401

            root = _vector_root(data_dir) / "chroma_memory"
            root.mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(path=str(root))
            col = client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

            class _ChromaWrap(SqliteVectorStore):
                backend = "chroma"

                def __init__(self) -> None:
                    self._col = col

                def upsert(self, memory_id, vector, *, namespace="default", entry_type="fact", content=""):
                    if not vector:
                        return self.delete(memory_id)
                    self._col.upsert(
                        ids=[memory_id],
                        embeddings=[vector],
                        metadatas=[{"namespace": namespace, "type": entry_type}],
                    )

                def delete(self, memory_id: str) -> None:
                    try:
                        self._col.delete(ids=[memory_id])
                    except Exception:
                        pass

                def search(self, query_vector, limit=10, *, namespace=None, min_score=0.0):
                    kwargs: dict[str, Any] = {"query_embeddings": [query_vector], "n_results": max(limit, 1)}
                    if namespace:
                        kwargs["where"] = {"namespace": {"$eq": namespace}}
                    res = self._col.query(**kwargs)
                    ids = (res.get("ids") or [[]])[0]
                    dists = (res.get("distances") or [[]])[0]
                    out = []
                    for mid, dist in zip(ids, dists):
                        sim = 1.0 - float(dist)
                        if sim >= min_score:
                            out.append((str(mid), sim))
                    return out[:limit]

                def close(self) -> None:
                    pass

            return _ChromaWrap()
        except Exception as exc:
            logger.warning("Chroma unavailable (%s) — using sqlite vectors", exc)
    return SqliteVectorStore(path=sqlite_path)


def migrate_sqlite_vectors_to(target, source: SqliteVectorStore | None = None) -> int:
    if getattr(target, "backend", "") == "sqlite":
        return 0
    src = source or SqliteVectorStore()
    if src.count() == 0:
        return 0
    rows = src._conn.execute("SELECT memory_id, dims, vector, namespace, entry_type FROM embeddings").fetchall()
    moved = 0
    for memory_id, dims, blob, namespace, entry_type in rows:
        vec = src._unpack(int(dims), blob)
        target.upsert(str(memory_id), vec, namespace=namespace or "default", entry_type=entry_type or "fact")
        moved += 1
    logger.info("Migrated %d vectors sqlite → %s", moved, getattr(target, "backend", "?"))
    return moved
