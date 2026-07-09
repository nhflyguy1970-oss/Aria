"""Vector memory backends — sqlite (default), ChromaDB, Qdrant, Weaviate."""

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

    def get(self, memory_id: str) -> list[float]: ...

    def upsert(
        self,
        memory_id: str,
        vector: list[float],
        *,
        namespace: str = "default",
        entry_type: str = "fact",
        content: str = "",
    ) -> None: ...

    def delete(self, memory_id: str) -> None: ...

    def delete_many(self, memory_ids: list[str]) -> None: ...

    def count(self) -> int: ...

    def search(
        self,
        query_vector: list[float],
        limit: int,
        *,
        namespace: str | None = None,
        min_score: float = 0.3,
    ) -> list[tuple[str, float]]: ...

    def close(self) -> None: ...


def resolve_vector_backend() -> str:
    explicit = os.getenv("JARVIS_VECTOR_BACKEND", "").strip().lower()
    if explicit in VECTOR_BACKENDS:
        return explicit
    return "sqlite"


def _vector_root(data_dir: Path | None = None) -> Path:
    root = data_dir or DATA_DIR
    custom = os.getenv("JARVIS_VECTOR_PATH", "").strip()
    return Path(custom) if custom else root


class SqliteVectorStore:
    """Linear-scan fallback — same file as legacy embedding sidecar."""

    backend = "sqlite"

    def __init__(self, path: Path | None = None):
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
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    @staticmethod
    def _pack(vector: list[float]) -> tuple[int, bytes]:
        dims = len(vector)
        return dims, struct.pack(f"{dims}f", *vector)

    @staticmethod
    def _unpack(dims: int, blob: bytes) -> list[float]:
        return list(struct.unpack(f"{dims}f", blob))

    def get(self, memory_id: str) -> list[float]:
        row = self._conn.execute(
            "SELECT dims, vector FROM embeddings WHERE memory_id = ?",
            (memory_id,),
        ).fetchone()
        if not row:
            return []
        dims, blob = row
        return self._unpack(int(dims), blob)

    def upsert(
        self,
        memory_id: str,
        vector: list[float],
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
                dims=excluded.dims,
                vector=excluded.vector,
                namespace=excluded.namespace,
                entry_type=excluded.entry_type
            """,
            (memory_id, dims, blob, namespace or "default", entry_type or "fact"),
        )
        self._conn.commit()

    def set(self, memory_id: str, vector: list[float]) -> None:
        self.upsert(memory_id, vector)

    def delete(self, memory_id: str) -> None:
        self._conn.execute("DELETE FROM embeddings WHERE memory_id = ?", (memory_id,))
        self._conn.commit()

    def delete_many(self, memory_ids: list[str]) -> None:
        if not memory_ids:
            return
        placeholders = ",".join("?" * len(memory_ids))
        self._conn.execute(
            f"DELETE FROM embeddings WHERE memory_id IN ({placeholders})",
            memory_ids,
        )
        self._conn.commit()

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()
        return int(row[0]) if row else 0

    def iter_entries(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT memory_id, dims, vector, namespace, entry_type FROM embeddings"
        ).fetchall()
        out: list[dict[str, Any]] = []
        for memory_id, dims, blob, namespace, entry_type in rows:
            out.append(
                {
                    "memory_id": str(memory_id),
                    "vector": self._unpack(int(dims), blob),
                    "namespace": namespace or "default",
                    "entry_type": entry_type or "fact",
                }
            )
        return out

    def get_metadata(self, memory_id: str) -> dict[str, str]:
        row = self._conn.execute(
            "SELECT namespace, entry_type FROM embeddings WHERE memory_id = ?",
            (memory_id,),
        ).fetchone()
        if not row:
            return {"namespace": "default", "entry_type": "fact"}
        return {"namespace": row[0] or "default", "entry_type": row[1] or "fact"}

    def search(
        self,
        query_vector: list[float],
        limit: int,
        *,
        namespace: str | None = None,
        min_score: float = 0.3,
    ) -> list[tuple[str, float]]:
        from jarvis import llm

        if not query_vector:
            return []
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


class ChromaVectorStore:
    """Embedded ChromaDB — best local default when installed."""

    backend = "chroma"

    def __init__(self, path: Path | None = None):
        import chromadb

        root = path or (_vector_root() / "chroma_memory")
        root.mkdir(parents=True, exist_ok=True)
        self.path = root
        self._client = chromadb.PersistentClient(path=str(root))
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def close(self) -> None:
        return

    def get(self, memory_id: str) -> list[float]:
        try:
            got = self._collection.get(ids=[memory_id], include=["embeddings"])
            embs = got.get("embeddings") or []
            if embs and embs[0]:
                return [float(x) for x in embs[0]]
        except Exception:
            pass
        return []

    def upsert(
        self,
        memory_id: str,
        vector: list[float],
        *,
        namespace: str = "default",
        entry_type: str = "fact",
        content: str = "",
    ) -> None:
        if not vector:
            self.delete(memory_id)
            return
        self._collection.upsert(
            ids=[memory_id],
            embeddings=[vector],
            metadatas=[
                {
                    "namespace": namespace or "default",
                    "type": entry_type or "fact",
                }
            ],
            documents=[(content or "")[:2000]],
        )

    def delete(self, memory_id: str) -> None:
        try:
            self._collection.delete(ids=[memory_id])
        except Exception:
            pass

    def delete_many(self, memory_ids: list[str]) -> None:
        if not memory_ids:
            return
        try:
            self._collection.delete(ids=memory_ids)
        except Exception:
            pass

    def count(self) -> int:
        return int(self._collection.count())

    def search(
        self,
        query_vector: list[float],
        limit: int,
        *,
        namespace: str | None = None,
        min_score: float = 0.3,
    ) -> list[tuple[str, float]]:
        if not query_vector:
            return []
        kwargs: dict[str, Any] = {
            "query_embeddings": [query_vector],
            "n_results": max(limit, 1),
            "include": ["distances"],
        }
        if namespace:
            kwargs["where"] = {"namespace": {"$eq": namespace}}
        try:
            result = self._collection.query(**kwargs)
        except Exception as exc:
            logger.warning("Chroma query failed: %s", exc)
            return []
        ids = (result.get("ids") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        out: list[tuple[str, float]] = []
        for mid, dist in zip(ids, distances):
            sim = max(0.0, 1.0 - float(dist))
            if sim >= min_score:
                out.append((str(mid), sim))
        return out[:limit]


class QdrantVectorStore:
    """Embedded Qdrant — file-backed, no Docker required."""

    backend = "qdrant"

    def __init__(self, path: Path | None = None):
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams

        root = path or (_vector_root() / "qdrant_memory")
        root.mkdir(parents=True, exist_ok=True)
        self.path = root
        self._client = QdrantClient(path=str(root))
        self._collection = COLLECTION_NAME
        if not self._client.collection_exists(self._collection):
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE),
            )

    def close(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass

    def get(self, memory_id: str) -> list[float]:
        try:
            points = self._client.retrieve(
                collection_name=self._collection,
                ids=[memory_id],
                with_vectors=True,
            )
            if points and points[0].vector:
                return [float(x) for x in points[0].vector]  # type: ignore[arg-type]
        except Exception:
            pass
        return []

    def upsert(
        self,
        memory_id: str,
        vector: list[float],
        *,
        namespace: str = "default",
        entry_type: str = "fact",
        content: str = "",
    ) -> None:
        from qdrant_client.models import PointStruct

        if not vector:
            self.delete(memory_id)
            return
        self._client.upsert(
            collection_name=self._collection,
            points=[
                PointStruct(
                    id=memory_id,
                    vector=vector,
                    payload={
                        "namespace": namespace or "default",
                        "type": entry_type or "fact",
                        "content": (content or "")[:2000],
                    },
                )
            ],
        )

    def delete(self, memory_id: str) -> None:
        try:
            self._client.delete(collection_name=self._collection, points_selector=[memory_id])
        except Exception:
            pass

    def delete_many(self, memory_ids: list[str]) -> None:
        if not memory_ids:
            return
        try:
            self._client.delete(collection_name=self._collection, points_selector=memory_ids)
        except Exception:
            pass

    def count(self) -> int:
        try:
            info = self._client.get_collection(self._collection)
            return int(info.points_count or 0)
        except Exception:
            return 0

    def search(
        self,
        query_vector: list[float],
        limit: int,
        *,
        namespace: str | None = None,
        min_score: float = 0.3,
    ) -> list[tuple[str, float]]:
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        if not query_vector:
            return []
        query_filter = None
        if namespace:
            query_filter = Filter(
                must=[FieldCondition(key="namespace", match=MatchValue(value=namespace))]
            )
        try:
            hits = self._client.search(
                collection_name=self._collection,
                query_vector=query_vector,
                limit=max(limit, 1),
                query_filter=query_filter,
                score_threshold=min_score,
            )
        except Exception as exc:
            logger.warning("Qdrant search failed: %s", exc)
            return []
        return [(str(h.id), float(h.score)) for h in hits][:limit]


class WeaviateVectorStore:
    """Weaviate server — set JARVIS_WEAVIATE_URL (default http://localhost:8080)."""

    backend = "weaviate"

    def __init__(self, url: str | None = None):
        self.url = url or os.getenv("JARVIS_WEAVIATE_URL", "http://localhost:8080")
        self._client = self._connect()
        self._class = "JarvisMemory"
        self._ensure_schema()

    def _connect(self):
        try:
            import weaviate

            if hasattr(weaviate, "connect_to_custom"):
                host = self.url.replace("http://", "").replace("https://", "").split(":")[0]
                port = 8080
                secure = self.url.startswith("https")
                if ":" in self.url.split("//")[-1]:
                    port = int(self.url.split(":")[-1].split("/")[0])
                return weaviate.connect_to_custom(
                    http_host=host,
                    http_port=port,
                    http_secure=secure,
                    grpc_host=host,
                    grpc_port=50051,
                    grpc_secure=secure,
                )
            return weaviate.Client(self.url)
        except Exception as exc:
            raise RuntimeError(f"Weaviate unavailable at {self.url}: {exc}") from exc

    def _ensure_schema(self) -> None:
        try:
            if hasattr(self._client, "collections"):
                cols = self._client.collections
                if not cols.exists(self._class):
                    cols.create(
                        name=self._class,
                        vectorizer_config=None,
                        properties=[
                            {"name": "memory_id", "dataType": ["text"]},
                            {"name": "namespace", "dataType": ["text"]},
                            {"name": "type", "dataType": ["text"]},
                            {"name": "content", "dataType": ["text"]},
                        ],
                    )
            else:
                schema = self._client.schema.get()
                classes = {c["class"] for c in schema.get("classes", [])}
                if self._class not in classes:
                    self._client.schema.create_class(
                        {
                            "class": self._class,
                            "vectorizer": "none",
                            "properties": [
                                {"name": "memory_id", "dataType": ["text"]},
                                {"name": "namespace", "dataType": ["text"]},
                                {"name": "type", "dataType": ["text"]},
                                {"name": "content", "dataType": ["text"]},
                            ],
                        }
                    )
        except Exception as exc:
            logger.warning("Weaviate schema setup: %s", exc)

    def close(self) -> None:
        try:
            if hasattr(self._client, "close"):
                self._client.close()
        except Exception:
            pass

    def _uuid_for(self, memory_id: str) -> str:
        import uuid

        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"jarvis.memory.{memory_id}"))

    def get(self, memory_id: str) -> list[float]:
        return []

    def upsert(
        self,
        memory_id: str,
        vector: list[float],
        *,
        namespace: str = "default",
        entry_type: str = "fact",
        content: str = "",
    ) -> None:
        if not vector:
            self.delete(memory_id)
            return
        uid = self._uuid_for(memory_id)
        props = {
            "memory_id": memory_id,
            "namespace": namespace or "default",
            "type": entry_type or "fact",
            "content": (content or "")[:2000],
        }
        try:
            if hasattr(self._client, "collections"):
                col = self._client.collections.get(self._class)
                col.data.insert(properties=props, vector=vector, uuid=uid)
            else:
                self._client.data_object.create(
                    data_object=props,
                    class_name=self._class,
                    vector=vector,
                    uuid=uid,
                )
        except Exception as exc:
            logger.warning("Weaviate upsert %s: %s", memory_id, exc)

    def delete(self, memory_id: str) -> None:
        try:
            uid = self._uuid_for(memory_id)
            if hasattr(self._client, "collections"):
                self._client.collections.get(self._class).data.delete_by_id(uid)
            else:
                self._client.data_object.delete(uuid=uid, class_name=self._class)
        except Exception:
            pass

    def delete_many(self, memory_ids: list[str]) -> None:
        for mid in memory_ids:
            self.delete(mid)

    def count(self) -> int:
        try:
            if hasattr(self._client, "collections"):
                col = self._client.collections.get(self._class)
                agg = col.aggregate.over_all(total_count=True)
                return int(agg.total_count or 0)
        except Exception:
            pass
        return 0

    def search(
        self,
        query_vector: list[float],
        limit: int,
        *,
        namespace: str | None = None,
        min_score: float = 0.3,
    ) -> list[tuple[str, float]]:
        if not query_vector:
            return []
        try:
            if hasattr(self._client, "collections"):
                col = self._client.collections.get(self._class)
                kwargs: dict[str, Any] = {
                    "near_vector": query_vector,
                    "limit": limit,
                    "return_properties": ["memory_id"],
                }
                if namespace:
                    from weaviate.classes.query import Filter

                    kwargs["filters"] = Filter.by_property("namespace").equal(namespace)
                result = col.query.near_vector(**kwargs)
                out: list[tuple[str, float]] = []
                for obj in result.objects:
                    mid = (obj.properties or {}).get("memory_id", "")
                    dist = getattr(obj.metadata, "distance", None)
                    sim = 1.0 - float(dist) if dist is not None else min_score
                    if mid and sim >= min_score:
                        out.append((str(mid), sim))
                return out[:limit]
            result = (
                self._client.query.get(self._class, ["memory_id"])
                .with_near_vector({"vector": query_vector})
                .with_limit(limit)
                .do()
            )
            hits = result.get("data", {}).get("Get", {}).get(self._class, [])
            return [(str(h.get("memory_id")), min_score) for h in hits if h.get("memory_id")][
                :limit
            ]
        except Exception as exc:
            logger.warning("Weaviate search failed: %s", exc)
            return []


def create_vector_store(
    data_dir: Path | None = None,
    *,
    backend: str | None = None,
    sqlite_path: Path | None = None,
) -> VectorMemoryStore:
    """Factory for vector memory backend."""
    name = (backend or resolve_vector_backend()).lower()
    root = _vector_root(data_dir)

    if name == "chroma":
        try:
            return ChromaVectorStore(root / "chroma_memory")
        except ImportError as exc:
            logger.warning("chromadb not installed, falling back to sqlite: %s", exc)
            name = "sqlite"
    elif name == "qdrant":
        try:
            return QdrantVectorStore(root / "qdrant_memory")
        except ImportError as exc:
            logger.warning("qdrant-client not installed, falling back to sqlite: %s", exc)
            name = "sqlite"
    elif name == "weaviate":
        try:
            return WeaviateVectorStore()
        except Exception as exc:
            logger.warning("Weaviate unavailable, falling back to sqlite: %s", exc)
            name = "sqlite"

    path = sqlite_path or (root / "memory_vectors.db")
    if data_dir and sqlite_path is None:
        path = data_dir / "memory_vectors.db"
    store = SqliteVectorStore(path)
    return store


def migrate_sqlite_vectors_to(
    target: VectorMemoryStore, source: SqliteVectorStore | None = None
) -> int:
    """One-time import from sqlite sidecar into chroma/qdrant/weaviate."""
    if target.backend == "sqlite":
        return 0
    src = source or SqliteVectorStore()
    if src.count() == 0:
        return 0
    rows = src._conn.execute(
        "SELECT memory_id, dims, vector, namespace, entry_type FROM embeddings"
    ).fetchall()
    moved = 0
    for memory_id, dims, blob, namespace, entry_type in rows:
        vec = src._unpack(int(dims), blob)
        if not vec:
            continue
        target.upsert(
            str(memory_id),
            vec,
            namespace=namespace or "default",
            entry_type=entry_type or "fact",
        )
        moved += 1
    logger.info("Migrated %d vectors sqlite → %s", moved, target.backend)
    return moved
