"""SQLite memory backend with embedding sidecar."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime

from jarvis import config as jarvis_config
from jarvis import llm
from jarvis.config import DATA_DIR
from jarvis.modules.memory_common import (
    DEFAULT_NAMESPACE,
    MEMORY_TYPES,
    normalize_entry,
    parse_remember,
    parse_ts,
    relevance_score,
    search_pool,
    split_remember_facts,
    to_public,
    utc_now,
)
from jarvis.modules.memory_embeddings import EmbeddingSidecar


class SqliteMemoryStore:
    def __init__(self, path=None, embeddings: EmbeddingSidecar | None = None):
        self.path = path or jarvis_config.MEMORY_DB_FILE
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._embeddings = embeddings or EmbeddingSidecar()
        self._pending_touch_ids: set[str] = set()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                namespace TEXT NOT NULL DEFAULT 'default',
                timestamp TEXT NOT NULL,
                access_count INTEGER NOT NULL DEFAULT 0,
                relevance REAL NOT NULL DEFAULT 1.0,
                tags TEXT NOT NULL DEFAULT '[]',
                last_accessed TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_memories_ns ON memories(namespace);
            CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);
            CREATE INDEX IF NOT EXISTS idx_memories_ts ON memories(timestamp);
            CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
            """
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
        self._embeddings.close()

    def _row_to_entry(self, row: sqlite3.Row, *, include_embedding: bool = False) -> dict:
        tags = row["tags"]
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except json.JSONDecodeError:
                tags = []
        entry = {
            "id": row["id"],
            "type": row["type"],
            "content": row["content"],
            "namespace": row["namespace"],
            "timestamp": row["timestamp"],
            "access_count": int(row["access_count"] or 0),
            "relevance": float(row["relevance"] or 1.0),
            "tags": tags,
        }
        if row["last_accessed"]:
            entry["last_accessed"] = row["last_accessed"]
        if include_embedding:
            entry["embedding"] = self._embeddings.get(entry["id"])
        return normalize_entry(entry)

    def _all_rows(self) -> list[sqlite3.Row]:
        return list(self._conn.execute("SELECT * FROM memories ORDER BY timestamp"))

    def _iter_entries(self, *, include_embedding: bool = False) -> list[dict]:
        return [
            self._row_to_entry(r, include_embedding=include_embedding) for r in self._all_rows()
        ]

    @property
    def _data(self) -> dict:
        """Legacy compat for cheatsheets/profile until fully migrated."""
        return {"entries": self._iter_entries(include_embedding=True), "version": 2}

    def _save(self) -> None:
        self.flush()

    def flush(self) -> None:
        self._apply_pending_touches()

    def _apply_pending_touches(self) -> None:
        if not self._pending_touch_ids:
            return
        now = utc_now()
        touched = list(self._pending_touch_ids)
        self._pending_touch_ids.clear()
        placeholders = ",".join("?" * len(touched))
        self._conn.execute(
            f"""
            UPDATE memories
            SET access_count = access_count + 1, last_accessed = ?
            WHERE id IN ({placeholders})
            """,
            [now, *touched],
        )
        self._conn.commit()

    def _next_id(self) -> str:
        while True:
            nid = uuid.uuid4().hex[:10]
            row = self._conn.execute("SELECT 1 FROM memories WHERE id = ?", (nid,)).fetchone()
            if not row:
                return nid

    @staticmethod
    def to_public(entry: dict) -> dict:
        return to_public(entry)

    def add(
        self,
        entry_type: str,
        content: str,
        tags: list[str] | None = None,
        *,
        namespace: str | None = None,
    ) -> dict:
        content = (content or "").strip()
        if not content:
            raise ValueError("Empty memory content")
        from jarvis.trust_memory import is_trusted_memory_content

        if entry_type not in ("failure", "strategy") and not is_trusted_memory_content(content):
            raise ValueError("Refusing to store test-artifact content in live memory")
        entry_type = entry_type if entry_type in MEMORY_TYPES else "fact"
        try:
            from aria_core.acm_bridge import (
                acm_is_authoritative,
                note_legacy_write_while_primary,
                redirect_legacy_write_to_acm,
            )

            try:
                redirected = redirect_legacy_write_to_acm(
                    content, entry_type=entry_type, tags=tags, namespace=namespace
                )
            except Exception as exc:
                if acm_is_authoritative():
                    note_legacy_write_while_primary()
                    raise RuntimeError(
                        f"ACM authoritative: legacy MemoryStore write refused "
                        f"({type(exc).__name__})"
                    ) from exc
                redirected = None
            if redirected is not None:
                return redirected
            if acm_is_authoritative():
                note_legacy_write_while_primary()
                raise RuntimeError(
                    "ACM authoritative: legacy MemoryStore write refused "
                    "(redirect returned no entry)"
                )
        except ImportError:
            pass
        eid = self._next_id()
        embedding = llm.embed_text(content)
        entry = {
            "id": eid,
            "type": entry_type,
            "content": content,
            "tags": tags or [],
            "namespace": (namespace or DEFAULT_NAMESPACE).strip() or DEFAULT_NAMESPACE,
            "timestamp": utc_now(),
            "access_count": 0,
            "relevance": 1.0,
        }
        self._conn.execute(
            """
            INSERT INTO memories(id, type, content, namespace, timestamp, access_count, relevance, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                eid,
                entry["type"],
                entry["content"],
                entry["namespace"],
                entry["timestamp"],
                0,
                1.0,
                json.dumps(entry["tags"]),
            ),
        )
        self._conn.commit()
        if embedding:
            self._embeddings.set(eid, embedding)
        entry["embedding"] = embedding
        return entry

    def similar_exists(self, content: str, threshold: float = 0.88) -> bool:
        try:
            from aria_core.acm_store_facade import acm_similar_exists

            hit = acm_similar_exists(content, threshold=threshold)
            if hit is not None:
                return hit
        except Exception:
            pass
        norm = content.lower().strip()
        if not norm:
            return True
        row = self._conn.execute(
            "SELECT id FROM memories WHERE lower(trim(content)) = ? LIMIT 1",
            (norm,),
        ).fetchone()
        if row:
            return True
        emb = llm.embed_text(content)
        if not emb:
            return False
        for r in self._all_rows():
            e_emb = self._embeddings.get(r["id"])
            if e_emb and llm.cosine_similarity(emb, e_emb) >= threshold:
                return True
        return False

    def relevance_score(self, entry: dict) -> float:
        return relevance_score(entry)

    def touch(self, entry_id: str) -> None:
        if entry_id:
            self._pending_touch_ids.add(entry_id)

    def list_entries(
        self,
        entry_type: str | None = None,
        *,
        namespace: str | None = None,
        query: str | None = None,
        include_embedding: bool = False,
    ) -> list[dict]:
        try:
            from aria_core.acm_store_facade import acm_list_entries

            projected = acm_list_entries(
                entry_type,
                namespace=namespace,
                query=query,
                include_embedding=include_embedding,
            )
            if projected is not None:
                return projected
        except Exception:
            pass
        sql = "SELECT * FROM memories WHERE 1=1"
        params: list = []
        if entry_type:
            sql += " AND type = ?"
            params.append(entry_type)
        if namespace:
            sql += " AND namespace = ?"
            params.append(namespace)
        rows = self._conn.execute(sql, params).fetchall()
        entries = [self._row_to_entry(r, include_embedding=include_embedding) for r in rows]
        if query:
            q = query.lower().strip()
            entries = [
                e
                for e in entries
                if q in e.get("content", "").lower()
                or any(q in t.lower() for t in e.get("tags", []))
                or q in e.get("namespace", "").lower()
            ]
        entries.sort(key=lambda e: (self.relevance_score(e), e.get("timestamp", "")), reverse=True)
        if include_embedding:
            return entries
        return [to_public(e) for e in entries]

    def get(self, entry_id: str) -> dict | None:
        try:
            from aria_core.acm_store_facade import acm_get

            projected = acm_get(entry_id)
            if projected is not None:
                return projected
            from aria_core import acm_bridge

            if acm_bridge.acm_is_authoritative():
                return None
        except Exception:
            pass
        row = self._conn.execute("SELECT * FROM memories WHERE id = ?", (entry_id,)).fetchone()
        if not row:
            return None
        return to_public(self._row_to_entry(row))

    def find_index(self, entry_id: str) -> int | None:
        rows = self._all_rows()
        for i, r in enumerate(rows):
            if r["id"] == entry_id:
                return i
        return None

    def update(
        self,
        entry_id: str,
        *,
        content: str | None = None,
        entry_type: str | None = None,
        tags: list[str] | None = None,
        namespace: str | None = None,
    ) -> bool:
        try:
            from aria_core.acm_store_facade import acm_update

            diverted = acm_update(
                entry_id,
                content=content,
                entry_type=entry_type,
                tags=tags,
                namespace=namespace,
            )
            if diverted is not None:
                return diverted
        except Exception:
            pass
        row = self._conn.execute("SELECT * FROM memories WHERE id = ?", (entry_id,)).fetchone()
        if not row:
            return False
        new_content = content.strip() if content is not None else row["content"]
        new_type = entry_type if entry_type and entry_type in MEMORY_TYPES else row["type"]
        new_tags = json.dumps(tags) if tags is not None else row["tags"]
        new_ns = namespace.strip() if namespace is not None else row["namespace"]
        if new_ns == "":
            new_ns = DEFAULT_NAMESPACE
        if content is not None:
            self._embeddings.set(entry_id, llm.embed_text(new_content))
        self._conn.execute(
            """
            UPDATE memories
            SET content = ?, type = ?, tags = ?, namespace = ?, timestamp = ?
            WHERE id = ?
            """,
            (new_content, new_type, new_tags, new_ns, utc_now(), entry_id),
        )
        self._conn.commit()
        return True

    def search(
        self,
        query: str,
        limit: int = 10,
        *,
        namespace: str | None = None,
        user_facing_only: bool = False,
    ) -> list[dict]:
        try:
            from aria_core.acm_store_facade import acm_search

            projected = acm_search(
                query, limit=limit, namespace=namespace, user_facing_only=user_facing_only
            )
            if projected is not None:
                return projected
        except Exception:
            pass
        pool = self._iter_entries()

        def _get_emb(e: dict) -> list[float]:
            return self._embeddings.get(e["id"])

        def _set_emb(e: dict, emb: list[float]) -> None:
            self._embeddings.set(e["id"], emb)

        return search_pool(
            pool,
            query,
            limit,
            namespace=namespace,
            get_embedding=_get_emb,
            set_embedding=_set_emb,
            touch=self.touch,
            flush_touches=self._apply_pending_touches,
            user_facing_only=user_facing_only,
        )

    def delete(self, index: int) -> bool:
        rows = self._all_rows()
        if not (0 <= index < len(rows)):
            return False
        eid = rows[index]["id"]
        return self.delete_id(eid)

    def delete_id(self, entry_id: str) -> bool:
        try:
            from aria_core.acm_store_facade import acm_delete_id

            diverted = acm_delete_id(entry_id)
            if diverted is not None:
                return diverted
        except Exception:
            pass
        cur = self._conn.execute("DELETE FROM memories WHERE id = ?", (entry_id,))
        self._conn.commit()
        if cur.rowcount:
            self._embeddings.delete(entry_id)
            return True
        return False

    def clear(self, entry_type: str | None = None, namespace: str | None = None) -> int:
        if not entry_type and not namespace:
            ids = [r["id"] for r in self._all_rows()]
            self._conn.execute("DELETE FROM memories")
            self._conn.commit()
            self._embeddings.delete_many(ids)
            return len(ids)
        sql = "SELECT id FROM memories WHERE 1=1"
        params: list = []
        if entry_type:
            sql += " AND type = ?"
            params.append(entry_type)
        if namespace:
            sql += " AND namespace = ?"
            params.append(namespace)
        ids = [r[0] for r in self._conn.execute(sql, params).fetchall()]
        if not ids:
            return 0
        placeholders = ",".join("?" * len(ids))
        self._conn.execute(f"DELETE FROM memories WHERE id IN ({placeholders})", ids)
        self._conn.commit()
        self._embeddings.delete_many(ids)
        return len(ids)

    def prune(
        self,
        *,
        max_age_days: int = 120,
        min_score: float = 0.35,
        types: tuple[str, ...] = ("auto",),
    ) -> int:
        now = datetime.now(UTC)
        remove_ids: list[str] = []
        for r in self._all_rows():
            entry = self._row_to_entry(r)
            if entry.get("type") not in types:
                continue
            age = (now - parse_ts(entry.get("timestamp", ""))).days
            if age >= max_age_days and self.relevance_score(entry) < min_score:
                remove_ids.append(entry["id"])
        if not remove_ids:
            return 0
        placeholders = ",".join("?" * len(remove_ids))
        self._conn.execute(f"DELETE FROM memories WHERE id IN ({placeholders})", remove_ids)
        self._conn.commit()
        self._embeddings.delete_many(remove_ids)
        return len(remove_ids)

    def namespaces(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT DISTINCT namespace FROM memories ORDER BY namespace"
        ).fetchall()
        ns = [r[0] for r in rows if r[0]]
        return ns or [DEFAULT_NAMESPACE]

    def stats(self) -> dict:
        by_type: dict[str, int] = {}
        for r in self._conn.execute("SELECT type, COUNT(*) FROM memories GROUP BY type"):
            by_type[str(r[0])] = int(r[1])
        by_namespace: dict[str, int] = {}
        for r in self._conn.execute("SELECT namespace, COUNT(*) FROM memories GROUP BY namespace"):
            by_namespace[str(r[0])] = int(r[1])
        total = sum(by_type.values())
        return {
            "total": total,
            "namespaces": self.namespaces(),
            "by_type": by_type,
            "by_namespace": by_namespace,
            "backend": "sqlite",
            "vector_backend": getattr(self._embeddings, "backend", "sqlite"),
            "vectors": self._embeddings.count(),
        }

    def latest_checkpoint(self, namespace: str | None = None) -> dict | None:
        sql = "SELECT * FROM memories WHERE tags LIKE '%checkpoint%'"
        params: list = []
        if namespace:
            sql += " AND namespace = ?"
            params.append(namespace)
        rows = self._conn.execute(sql, params).fetchall()
        if not rows:
            return None
        best = max(rows, key=lambda r: r["timestamp"] or "")
        return to_public(self._row_to_entry(best))

    def upsert_checkpoint(self, content: str, namespace: str = "default") -> dict:
        ns = (namespace or DEFAULT_NAMESPACE).strip() or DEFAULT_NAMESPACE
        rows = self._conn.execute(
            "SELECT id FROM memories WHERE namespace = ? AND tags LIKE '%checkpoint%'",
            (ns,),
        ).fetchall()
        if rows:
            self._embeddings.delete_many([r[0] for r in rows])
            self._conn.execute(
                "DELETE FROM memories WHERE namespace = ? AND tags LIKE '%checkpoint%'",
                (ns,),
            )
            self._conn.commit()
        return self.add(
            "project",
            content,
            tags=["checkpoint", "project-state"],
            namespace=ns,
        )

    def export_data(self, *, include_embeddings: bool = False) -> dict:
        entries = self._iter_entries(include_embedding=include_embeddings)
        if not include_embeddings:
            entries = [to_public(e) for e in entries]
        return {"version": 2, "exported_at": utc_now(), "entries": entries}

    def import_data(self, payload: dict, *, merge: bool = True) -> int:
        incoming = payload.get("entries") if isinstance(payload, dict) else None
        if not isinstance(incoming, list):
            raise ValueError("Invalid memory import — expected {entries: [...]}")
        if not merge:
            self.clear()
        existing_ids = {r["id"] for r in self._all_rows()}
        existing_content = {(r["content"] or "").lower().strip() for r in self._all_rows()}
        added = 0
        for raw in incoming:
            if not isinstance(raw, dict):
                continue
            content = str(raw.get("content", "")).strip()
            if not content or content.lower() in existing_content:
                continue
            entry_type = raw.get("type") if raw.get("type") in MEMORY_TYPES else "fact"
            tags = raw.get("tags") if isinstance(raw.get("tags"), list) else []
            namespace = str(raw.get("namespace") or DEFAULT_NAMESPACE)
            eid = raw.get("id")
            if eid in existing_ids:
                eid = self._next_id()
            eid = eid or self._next_id()
            emb = (
                raw.get("embedding")
                if isinstance(raw.get("embedding"), list)
                else llm.embed_text(content)
            )
            self._conn.execute(
                """
                INSERT INTO memories(id, type, content, namespace, timestamp, access_count, relevance, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    eid,
                    entry_type,
                    content,
                    namespace,
                    raw.get("timestamp") or utc_now(),
                    int(raw.get("access_count") or 0),
                    float(raw.get("relevance") or 1.0),
                    json.dumps(tags),
                ),
            )
            if emb:
                self._embeddings.set(eid, emb)
            existing_ids.add(eid)
            existing_content.add(content.lower())
            added += 1
        if added:
            self._conn.commit()
        return added

    parse_remember = staticmethod(parse_remember)
    split_remember_facts = staticmethod(split_remember_facts)

    def find_by_env_key(self, env_key: str) -> dict | None:
        tag = f"env-key:{env_key}"
        for e in self.list_entries(namespace="environment", include_embedding=True):
            if tag in (e.get("tags") or []):
                return e
        return None

    def upsert_by_tag(
        self,
        *,
        tag: str,
        entry_type: str,
        content: str,
        namespace: str,
        extra_tags: list[str] | None = None,
    ) -> dict:
        for e in self.list_entries(namespace=namespace, include_embedding=True):
            if tag in (e.get("tags") or []):
                self.update(e["id"], content=content)
                return self.get(e["id"]) or e
        tags = list(extra_tags or []) + [tag]
        return self.add(entry_type, content, tags=tags, namespace=namespace)

    def upsert_branch_summary(self, branch_id: str, content: str) -> dict:
        from jarvis.memory_context import branch_memory_namespace

        ns = branch_memory_namespace(branch_id)
        return self.upsert_by_tag(
            tag="branch-summary",
            entry_type="note",
            content=content,
            namespace=ns,
            extra_tags=["conversation-roll", "branch-summary"],
        )
