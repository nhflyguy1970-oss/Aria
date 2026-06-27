"""Graph memory backends — sqlite (default), Memgraph, Neo4j (Bolt/Cypher)."""

from __future__ import annotations

import logging
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from jarvis import config as jarvis_config
from jarvis.config import DATA_DIR

logger = logging.getLogger("jarvis.graph_store")

GRAPH_BACKENDS = ("sqlite", "memgraph", "neo4j")
ENTITY_LABEL = "Entity"


def resolve_graph_backend() -> str:
    explicit = os.getenv("JARVIS_GRAPH_BACKEND", "").strip().lower()
    if explicit in GRAPH_BACKENDS:
        return explicit
    return "sqlite"


def _graph_root(data_dir: Path | None = None) -> Path:
    root = data_dir or DATA_DIR
    custom = os.getenv("JARVIS_GRAPH_PATH", "").strip()
    return Path(custom) if custom else root


def _bolt_config() -> tuple[str, str | None, str | None]:
    uri = os.getenv("JARVIS_GRAPH_URL", "bolt://localhost:7687").strip()
    user = os.getenv("JARVIS_GRAPH_USER", "").strip() or None
    password = os.getenv("JARVIS_GRAPH_PASSWORD", "").strip() or None
    return uri, user, password


def _normalize_rel(rel: str) -> str:
    token = re.sub(r"[^A-Za-z0-9_]+", "_", (rel or "RELATED_TO").strip().upper())
    token = re.sub(r"_+", "_", token).strip("_")
    if not token:
        token = "RELATED_TO"
    if token[0].isdigit():
        token = f"REL_{token}"
    return token[:48]


class GraphMemoryStore(Protocol):
    backend: str

    def merge_node(
        self,
        name: str,
        *,
        kind: str = "entity",
        namespace: str = "default",
        memory_id: str = "",
        props: dict[str, Any] | None = None,
    ) -> str: ...

    def merge_relationship(
        self,
        subject: str,
        predicate: str,
        obj: str,
        *,
        namespace: str = "default",
        memory_id: str = "",
        props: dict[str, Any] | None = None,
    ) -> str: ...

    def neighbors(self, name: str, *, depth: int = 1, limit: int = 24) -> list[dict]: ...

    def search_nodes(self, query: str, *, limit: int = 12) -> list[dict]: ...

    def related_triples(self, names: list[str], *, depth: int = 1, limit: int = 24) -> list[dict]: ...

    def stats(self) -> dict[str, int]: ...

    def close(self) -> None: ...


class SqliteGraphStore:
    """Embedded graph — zero extra services."""

    backend = "sqlite"

    def __init__(self, path: Path | None = None):
        self.path = path or (jarvis_config.DATA_DIR / "relationship_graph.db")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                kind TEXT NOT NULL DEFAULT 'entity',
                namespace TEXT NOT NULL DEFAULT 'default',
                memory_id TEXT NOT NULL DEFAULT '',
                props TEXT NOT NULL DEFAULT '{}',
                UNIQUE(name, namespace)
            );
            CREATE TABLE IF NOT EXISTS edges (
                id TEXT PRIMARY KEY,
                src TEXT NOT NULL,
                dst TEXT NOT NULL,
                rel TEXT NOT NULL,
                namespace TEXT NOT NULL DEFAULT 'default',
                memory_id TEXT NOT NULL DEFAULT '',
                props TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                UNIQUE(src, rel, dst, namespace)
            );
            CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name);
            CREATE INDEX IF NOT EXISTS idx_edges_src ON edges(src);
            CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(dst);
            """
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def _node_id(self, name: str, namespace: str) -> str:
        row = self._conn.execute(
            "SELECT id FROM nodes WHERE lower(name) = lower(?) AND namespace = ?",
            (name.strip(), namespace),
        ).fetchone()
        if row:
            return str(row["id"])
        nid = uuid.uuid4().hex[:12]
        self._conn.execute(
            "INSERT INTO nodes(id, name, kind, namespace, memory_id, props) VALUES (?, ?, ?, ?, ?, ?)",
            (nid, name.strip(), "entity", namespace, "", "{}"),
        )
        return nid

    def merge_node(
        self,
        name: str,
        *,
        kind: str = "entity",
        namespace: str = "default",
        memory_id: str = "",
        props: dict[str, Any] | None = None,
    ) -> str:
        import json

        name = name.strip()
        if not name:
            return ""
        row = self._conn.execute(
            "SELECT id FROM nodes WHERE lower(name) = lower(?) AND namespace = ?",
            (name, namespace),
        ).fetchone()
        payload = json.dumps(props or {})
        if row:
            nid = str(row["id"])
            self._conn.execute(
                "UPDATE nodes SET kind = ?, memory_id = COALESCE(NULLIF(?, ''), memory_id), props = ? WHERE id = ?",
                (kind, memory_id, payload, nid),
            )
        else:
            nid = uuid.uuid4().hex[:12]
            self._conn.execute(
                "INSERT INTO nodes(id, name, kind, namespace, memory_id, props) VALUES (?, ?, ?, ?, ?, ?)",
                (nid, name, kind, namespace, memory_id or "", payload),
            )
        self._conn.commit()
        return nid

    def merge_relationship(
        self,
        subject: str,
        predicate: str,
        obj: str,
        *,
        namespace: str = "default",
        memory_id: str = "",
        props: dict[str, Any] | None = None,
    ) -> str:
        import json

        subject, obj = subject.strip(), obj.strip()
        rel = _normalize_rel(predicate)
        if not subject or not obj:
            return ""
        src = self.merge_node(subject, namespace=namespace)
        dst = self.merge_node(obj, namespace=namespace)
        row = self._conn.execute(
            "SELECT id FROM edges WHERE src = ? AND dst = ? AND rel = ? AND namespace = ?",
            (src, dst, rel, namespace),
        ).fetchone()
        now = datetime.now(timezone.utc).isoformat()
        payload = json.dumps(props or {})
        if row:
            eid = str(row["id"])
            self._conn.execute(
                "UPDATE edges SET memory_id = COALESCE(NULLIF(?, ''), memory_id), props = ? WHERE id = ?",
                (memory_id, payload, eid),
            )
        else:
            eid = uuid.uuid4().hex[:12]
            self._conn.execute(
                """
                INSERT INTO edges(id, src, dst, rel, namespace, memory_id, props, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (eid, src, dst, rel, namespace, memory_id or "", payload, now),
            )
        self._conn.commit()
        return eid

    def _node_name(self, node_id: str) -> str:
        row = self._conn.execute("SELECT name FROM nodes WHERE id = ?", (node_id,)).fetchone()
        return str(row["name"]) if row else ""

    def neighbors(self, name: str, *, depth: int = 1, limit: int = 24) -> list[dict]:
        name = name.strip()
        if not name:
            return []
        start = self._conn.execute(
            "SELECT id, name FROM nodes WHERE lower(name) = lower(?) LIMIT 1",
            (name,),
        ).fetchone()
        if not start:
            return []
        seen_edges: set[str] = set()
        frontier = {str(start["id"])}
        out: list[dict] = []
        for _ in range(max(1, depth)):
            if not frontier:
                break
            next_frontier: set[str] = set()
            for nid in frontier:
                rows = self._conn.execute(
                    "SELECT id, src, dst, rel FROM edges WHERE src = ? OR dst = ?",
                    (nid, nid),
                ).fetchall()
                for row in rows:
                    eid = str(row["id"])
                    if eid in seen_edges:
                        continue
                    seen_edges.add(eid)
                    src_name = self._node_name(str(row["src"]))
                    dst_name = self._node_name(str(row["dst"]))
                    out.append({
                        "subject": src_name,
                        "predicate": str(row["rel"]),
                        "object": dst_name,
                    })
                    next_frontier.add(str(row["src"]))
                    next_frontier.add(str(row["dst"]))
                    if len(out) >= limit:
                        return out
            frontier = next_frontier
        return out[:limit]

    def search_nodes(self, query: str, *, limit: int = 12) -> list[dict]:
        q = f"%{(query or '').strip()}%"
        if q == "%%":
            return []
        rows = self._conn.execute(
            "SELECT name, kind, namespace FROM nodes WHERE name LIKE ? ORDER BY name LIMIT ?",
            (q, limit),
        ).fetchall()
        return [{"name": r["name"], "kind": r["kind"], "namespace": r["namespace"]} for r in rows]

    def related_triples(self, names: list[str], *, depth: int = 1, limit: int = 24) -> list[dict]:
        out: list[dict] = []
        seen: set[tuple[str, str, str]] = set()
        for name in names:
            for triple in self.neighbors(name, depth=depth, limit=limit):
                key = (triple["subject"], triple["predicate"], triple["object"])
                if key in seen:
                    continue
                seen.add(key)
                out.append(triple)
                if len(out) >= limit:
                    return out
        return out

    def stats(self) -> dict[str, int]:
        nodes = self._conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
        edges = self._conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        return {"nodes": int(nodes), "edges": int(edges)}


class BoltGraphStore:
    """Memgraph or Neo4j via Bolt protocol (neo4j Python driver)."""

    def __init__(self, uri: str, user: str | None, password: str | None, *, backend_name: str):
        from neo4j import GraphDatabase

        auth = None
        if user is not None or password is not None:
            auth = (user or "", password or "")
        self.backend = backend_name
        self._driver = GraphDatabase.driver(uri, auth=auth)
        self._ensure_constraints()

    def close(self) -> None:
        self._driver.close()

    def _ensure_constraints(self) -> None:
        try:
            with self._driver.session() as session:
                session.run(
                    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{ENTITY_LABEL}) REQUIRE n.name IS UNIQUE"
                )
        except Exception as exc:
            logger.debug("Graph constraint setup: %s", exc)

    def merge_node(
        self,
        name: str,
        *,
        kind: str = "entity",
        namespace: str = "default",
        memory_id: str = "",
        props: dict[str, Any] | None = None,
    ) -> str:
        name = name.strip()
        if not name:
            return ""
        extra = props or {}
        with self._driver.session() as session:
            session.run(
                f"""
                MERGE (n:{ENTITY_LABEL} {{name: $name}})
                SET n.kind = $kind,
                    n.namespace = $namespace,
                    n.memory_id = CASE WHEN $memory_id <> '' THEN $memory_id ELSE n.memory_id END,
                    n += $props
                """,
                name=name,
                kind=kind,
                namespace=namespace,
                memory_id=memory_id or "",
                props=extra,
            )
        return name

    def merge_relationship(
        self,
        subject: str,
        predicate: str,
        obj: str,
        *,
        namespace: str = "default",
        memory_id: str = "",
        props: dict[str, Any] | None = None,
    ) -> str:
        subject, obj = subject.strip(), obj.strip()
        rel = _normalize_rel(predicate)
        if not subject or not obj:
            return ""
        extra = props or {}
        cypher = f"""
        MERGE (a:{ENTITY_LABEL} {{name: $subject}})
        MERGE (b:{ENTITY_LABEL} {{name: $object}})
        MERGE (a)-[r:{rel}]->(b)
        SET r.namespace = $namespace,
            r.memory_id = CASE WHEN $memory_id <> '' THEN $memory_id ELSE r.memory_id END,
            r += $props
        """
        with self._driver.session() as session:
            session.run(
                cypher,
                subject=subject,
                object=obj,
                namespace=namespace,
                memory_id=memory_id or "",
                props=extra,
            )
        return f"{subject}-{rel}-{obj}"

    def neighbors(self, name: str, *, depth: int = 1, limit: int = 24) -> list[dict]:
        name = name.strip()
        if not name:
            return []
        cypher = f"""
        MATCH (n:{ENTITY_LABEL} {{name: $name}})-[r*1..{max(1, depth)}]-(m:{ENTITY_LABEL})
        WITH n, m, r LIMIT $limit
        UNWIND r AS rel
        RETURN DISTINCT startNode(rel).name AS subject, type(rel) AS predicate, endNode(rel).name AS object
        LIMIT $limit
        """
        with self._driver.session() as session:
            result = session.run(cypher, name=name, limit=limit)
            return [
                {"subject": rec["subject"], "predicate": rec["predicate"], "object": rec["object"]}
                for rec in result
                if rec["subject"] and rec["object"]
            ]

    def search_nodes(self, query: str, *, limit: int = 12) -> list[dict]:
        q = (query or "").strip().lower()
        if not q:
            return []
        cypher = f"""
        MATCH (n:{ENTITY_LABEL})
        WHERE toLower(n.name) CONTAINS $q
        RETURN n.name AS name, coalesce(n.kind, 'entity') AS kind, coalesce(n.namespace, 'default') AS namespace
        ORDER BY n.name LIMIT $limit
        """
        with self._driver.session() as session:
            result = session.run(cypher, q=q, limit=limit)
            return [dict(rec) for rec in result]

    def related_triples(self, names: list[str], *, depth: int = 1, limit: int = 24) -> list[dict]:
        cleaned = [n.strip() for n in names if (n or "").strip()]
        if not cleaned:
            return []
        out: list[dict] = []
        seen: set[tuple[str, str, str]] = set()
        for name in cleaned:
            for triple in self.neighbors(name, depth=depth, limit=limit):
                key = (triple["subject"], triple["predicate"], triple["object"])
                if key in seen:
                    continue
                seen.add(key)
                out.append(triple)
                if len(out) >= limit:
                    return out
        return out

    def stats(self) -> dict[str, int]:
        with self._driver.session() as session:
            nodes = session.run(f"MATCH (n:{ENTITY_LABEL}) RETURN count(n) AS c").single()
            edges = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()
        return {
            "nodes": int(nodes["c"]) if nodes else 0,
            "edges": int(edges["c"]) if edges else 0,
        }


def create_graph_store(
    data_dir: Path | None = None,
    *,
    backend: str | None = None,
    sqlite_path: Path | None = None,
) -> GraphMemoryStore:
    name = (backend or resolve_graph_backend()).lower()
    root = _graph_root(data_dir)

    if name in ("memgraph", "neo4j"):
        try:
            uri, user, password = _bolt_config()
            store = BoltGraphStore(uri, user, password, backend_name=name)
            store.stats()
            return store
        except Exception as exc:
            logger.warning("%s unavailable, falling back to sqlite graph: %s", name, exc)
            name = "sqlite"

    path = sqlite_path or (root / "relationship_graph.db")
    return SqliteGraphStore(path)


_GRAPH_SINGLETON: GraphMemoryStore | None = None


def get_graph_store() -> GraphMemoryStore:
    global _GRAPH_SINGLETON
    if _GRAPH_SINGLETON is None:
        _GRAPH_SINGLETON = create_graph_store()
    return _GRAPH_SINGLETON
