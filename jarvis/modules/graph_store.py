"""Graph memory backends — sqlite (default), Memgraph, Neo4j (Bolt/Cypher).

Connections (Knowledge Graph) persistence. Not Memory. Not Documents.
ACM remains cognitive SoT; this store mirrors relationships with provenance.
"""

from __future__ import annotations

import json
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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _bolt_list_nodes_query(
    *,
    namespace: str = "",
    kind: str = "",
    limit: int = 50,
    offset: int = 0,
    q: str = "",
) -> tuple[str, dict[str, Any]]:
    """Cypher for browsing Entity nodes. Empty q lists all (unlike search_nodes)."""
    conds: list[str] = []
    params: dict[str, Any] = {
        "limit": max(1, min(int(limit or 50), 2000)),
        "offset": max(0, int(offset or 0)),
    }
    if namespace:
        conds.append("n.namespace = $ns")
        params["ns"] = namespace
    if kind:
        conds.append("n.kind = $kind")
        params["kind"] = kind
    needle = (q or "").strip()
    if needle:
        conds.append("toLower(n.name) CONTAINS toLower($q)")
        params["q"] = needle
    where = ("WHERE " + " AND ".join(conds)) if conds else ""
    cypher = f"""
        MATCH (n:{ENTITY_LABEL})
        {where}
        RETURN n.name AS name,
               coalesce(n.kind, 'entity') AS kind,
               coalesce(n.namespace, 'default') AS namespace,
               coalesce(n.memory_id, '') AS memory_id
        ORDER BY n.name
        SKIP $offset LIMIT $limit
        """
    return cypher, params


def _bolt_list_edges_query(
    *,
    namespace: str = "",
    limit: int = 50,
    offset: int = 0,
    q: str = "",
) -> tuple[str, dict[str, Any]]:
    """Cypher for browsing relationships. Empty q lists all."""
    conds: list[str] = []
    params: dict[str, Any] = {
        "limit": max(1, min(int(limit or 50), 2000)),
        "offset": max(0, int(offset or 0)),
    }
    if namespace:
        conds.append("coalesce(rel.namespace, startNode(rel).namespace, 'default') = $ns")
        params["ns"] = namespace
    needle = (q or "").strip()
    if needle:
        conds.append(
            "("
            "toLower(type(rel)) CONTAINS toLower($q) OR "
            "toLower(startNode(rel).name) CONTAINS toLower($q) OR "
            "toLower(endNode(rel).name) CONTAINS toLower($q)"
            ")"
        )
        params["q"] = needle
    where = ("WHERE " + " AND ".join(conds)) if conds else ""
    cypher = f"""
        MATCH (a:{ENTITY_LABEL})-[rel]->(b:{ENTITY_LABEL})
        {where}
        RETURN startNode(rel).name AS subject,
               type(rel) AS predicate,
               endNode(rel).name AS object,
               coalesce(rel.namespace, 'default') AS namespace,
               coalesce(rel.memory_id, '') AS memory_id,
               coalesce(rel.confidence, 0.0) AS confidence,
               coalesce(rel.source, 'unknown') AS source
        ORDER BY subject, predicate, object
        SKIP $offset LIMIT $limit
        """
    return cypher, params


def _parse_props(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return dict(raw)
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


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

    def related_triples(
        self, names: list[str], *, depth: int = 1, limit: int = 24
    ) -> list[dict]: ...

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
        self._migrate()
        self._conn.commit()

    def _migrate(self) -> None:
        cols_n = {r[1] for r in self._conn.execute("PRAGMA table_info(nodes)").fetchall()}
        if "updated_at" not in cols_n:
            self._conn.execute("ALTER TABLE nodes ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''")
        if "created_at" not in cols_n:
            self._conn.execute("ALTER TABLE nodes ADD COLUMN created_at TEXT NOT NULL DEFAULT ''")
        cols_e = {r[1] for r in self._conn.execute("PRAGMA table_info(edges)").fetchall()}
        if "updated_at" not in cols_e:
            self._conn.execute("ALTER TABLE edges ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''")

    def close(self) -> None:
        self._conn.close()

    def _row_node(self, row: sqlite3.Row) -> dict[str, Any]:
        props = _parse_props(row["props"])
        return {
            "id": str(row["id"]),
            "name": str(row["name"]),
            "kind": str(row["kind"] or "entity"),
            "namespace": str(row["namespace"] or "default"),
            "memory_id": str(row["memory_id"] or ""),
            "props": props,
            "description": str(props.get("description") or ""),
            "confidence": float(props.get("confidence") or 0.0),
            "source": str(props.get("source") or ("memory" if row["memory_id"] else "unknown")),
            "document": str(props.get("document") or ""),
            "project": str(props.get("project") or ""),
            "created_at": str(row["created_at"] or props.get("created") or ""),
            "updated_at": str(row["updated_at"] or props.get("updated") or ""),
        }

    def _row_edge(
        self, row: sqlite3.Row, *, src_name: str = "", dst_name: str = ""
    ) -> dict[str, Any]:
        props = _parse_props(row["props"])
        src_name = src_name or self._node_name(str(row["src"]))
        dst_name = dst_name or self._node_name(str(row["dst"]))
        return {
            "id": str(row["id"]),
            "subject": src_name,
            "predicate": str(row["rel"]),
            "object": dst_name,
            "src": str(row["src"]),
            "dst": str(row["dst"]),
            "namespace": str(row["namespace"] or "default"),
            "memory_id": str(row["memory_id"] or ""),
            "props": props,
            "confidence": float(props.get("confidence") or 0.0),
            "source": str(props.get("source") or ("memory" if row["memory_id"] else "unknown")),
            "document": str(props.get("document") or ""),
            "project": str(props.get("project") or ""),
            "journal": str(props.get("journal") or ""),
            "created_at": str(row["created_at"] or ""),
            "updated_at": str(row["updated_at"] or props.get("updated") or ""),
            "provenance": {
                "source": str(props.get("source") or ("memory" if row["memory_id"] else "unknown")),
                "memory_id": str(row["memory_id"] or ""),
                "document": str(props.get("document") or ""),
                "project": str(props.get("project") or ""),
                "journal": str(props.get("journal") or ""),
                "confidence": float(props.get("confidence") or 0.0),
                "timestamp": str(row["created_at"] or ""),
                "namespace": str(row["namespace"] or "default"),
            },
        }

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
        now = _now()
        row = self._conn.execute(
            "SELECT id, props FROM nodes WHERE lower(name) = lower(?) AND namespace = ?",
            (name, namespace),
        ).fetchone()
        incoming = dict(props or {})
        if "updated" not in incoming:
            incoming["updated"] = now
        if row:
            nid = str(row["id"])
            merged = {**_parse_props(row["props"]), **incoming}
            if "created" not in merged:
                merged["created"] = now
            self._conn.execute(
                """
                UPDATE nodes SET kind = ?, memory_id = COALESCE(NULLIF(?, ''), memory_id),
                    props = ?, updated_at = ? WHERE id = ?
                """,
                (kind, memory_id, json.dumps(merged), now, nid),
            )
        else:
            nid = uuid.uuid4().hex[:12]
            incoming.setdefault("created", now)
            self._conn.execute(
                """
                INSERT INTO nodes(id, name, kind, namespace, memory_id, props, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (nid, name, kind, namespace, memory_id or "", json.dumps(incoming), now, now),
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
        subject, obj = subject.strip(), obj.strip()
        rel = _normalize_rel(predicate)
        if not subject or not obj:
            return ""
        now = _now()
        incoming = dict(props or {})
        if "source" not in incoming and not memory_id:
            incoming["source"] = "unknown"
        if memory_id and "source" not in incoming:
            incoming["source"] = "memory"
        incoming.setdefault("updated", now)
        src = self.merge_node(
            subject, namespace=namespace, props={"source": incoming.get("source", "manual")}
        )
        dst = self.merge_node(
            obj, namespace=namespace, props={"source": incoming.get("source", "manual")}
        )
        row = self._conn.execute(
            "SELECT id, props FROM edges WHERE src = ? AND dst = ? AND rel = ? AND namespace = ?",
            (src, dst, rel, namespace),
        ).fetchone()
        if row:
            eid = str(row["id"])
            merged = {**_parse_props(row["props"]), **incoming}
            self._conn.execute(
                """
                UPDATE edges SET memory_id = COALESCE(NULLIF(?, ''), memory_id),
                    props = ?, updated_at = ? WHERE id = ?
                """,
                (memory_id, json.dumps(merged), now, eid),
            )
        else:
            eid = uuid.uuid4().hex[:12]
            incoming.setdefault("created", now)
            self._conn.execute(
                """
                INSERT INTO edges(id, src, dst, rel, namespace, memory_id, props, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (eid, src, dst, rel, namespace, memory_id or "", json.dumps(incoming), now, now),
            )
        self._conn.commit()
        return eid

    def _node_name(self, node_id: str) -> str:
        row = self._conn.execute("SELECT name FROM nodes WHERE id = ?", (node_id,)).fetchone()
        return str(row["name"]) if row else ""

    def get_node(self, name: str, *, namespace: str | None = None) -> dict[str, Any] | None:
        name = (name or "").strip()
        if not name:
            return None
        if namespace:
            row = self._conn.execute(
                "SELECT * FROM nodes WHERE lower(name) = lower(?) AND namespace = ?",
                (name, namespace),
            ).fetchone()
        else:
            row = self._conn.execute(
                "SELECT * FROM nodes WHERE lower(name) = lower(?) ORDER BY namespace LIMIT 1",
                (name,),
            ).fetchone()
        return self._row_node(row) if row else None

    def get_node_by_id(self, node_id: str) -> dict[str, Any] | None:
        row = self._conn.execute("SELECT * FROM nodes WHERE id = ?", (node_id,)).fetchone()
        return self._row_node(row) if row else None

    def get_edge(self, edge_id: str) -> dict[str, Any] | None:
        row = self._conn.execute("SELECT * FROM edges WHERE id = ?", (edge_id,)).fetchone()
        return self._row_edge(row) if row else None

    def list_nodes(
        self,
        *,
        namespace: str = "",
        kind: str = "",
        limit: int = 50,
        offset: int = 0,
        q: str = "",
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        args: list[Any] = []
        if namespace:
            clauses.append("namespace = ?")
            args.append(namespace)
        if kind:
            clauses.append("kind = ?")
            args.append(kind)
        if q.strip():
            clauses.append("name LIKE ?")
            args.append(f"%{q.strip()}%")
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = self._conn.execute(
            f"SELECT * FROM nodes{where} ORDER BY updated_at DESC, name LIMIT ? OFFSET ?",
            (*args, limit, offset),
        ).fetchall()
        return [self._row_node(r) for r in rows]

    def list_edges(
        self,
        *,
        namespace: str = "",
        limit: int = 50,
        offset: int = 0,
        q: str = "",
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        args: list[Any] = []
        if namespace:
            clauses.append("e.namespace = ?")
            args.append(namespace)
        if q.strip():
            clauses.append("(e.rel LIKE ? OR sn.name LIKE ? OR dn.name LIKE ?)")
            like = f"%{q.strip()}%"
            args.extend([like, like, like])
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = self._conn.execute(
            f"""
            SELECT e.*, sn.name AS src_name, dn.name AS dst_name
            FROM edges e
            JOIN nodes sn ON sn.id = e.src
            JOIN nodes dn ON dn.id = e.dst
            {where}
            ORDER BY e.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (*args, limit, offset),
        ).fetchall()
        return [
            self._row_edge(r, src_name=str(r["src_name"]), dst_name=str(r["dst_name"]))
            for r in rows
        ]

    def namespaces(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT namespace, COUNT(*) AS nodes FROM nodes GROUP BY namespace ORDER BY namespace
            """
        ).fetchall()
        edge_counts = {
            str(r["namespace"]): int(r["c"])
            for r in self._conn.execute(
                "SELECT namespace, COUNT(*) AS c FROM edges GROUP BY namespace"
            ).fetchall()
        }
        return [
            {
                "namespace": str(r["namespace"]),
                "nodes": int(r["nodes"]),
                "edges": edge_counts.get(str(r["namespace"]), 0),
            }
            for r in rows
        ]

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
                    "SELECT * FROM edges WHERE src = ? OR dst = ?",
                    (nid, nid),
                ).fetchall()
                for row in rows:
                    eid = str(row["id"])
                    if eid in seen_edges:
                        continue
                    seen_edges.add(eid)
                    out.append(self._row_edge(row))
                    next_frontier.add(str(row["src"]))
                    next_frontier.add(str(row["dst"]))
                    if len(out) >= limit:
                        return out
            frontier = next_frontier
        return out[:limit]

    def search_nodes(self, query: str, *, limit: int = 12, namespace: str = "") -> list[dict]:
        q = (query or "").strip()
        if not q:
            return []
        if namespace:
            rows = self._conn.execute(
                """
                SELECT * FROM nodes
                WHERE name LIKE ? AND namespace = ?
                ORDER BY name LIMIT ?
                """,
                (f"%{q}%", namespace, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM nodes WHERE name LIKE ? ORDER BY name LIMIT ?",
                (f"%{q}%", limit),
            ).fetchall()
        return [self._row_node(r) for r in rows]

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

    def delete_node(self, name: str, *, namespace: str = "default") -> dict[str, Any]:
        node = self.get_node(name, namespace=namespace)
        if not node:
            return {"ok": False, "error": "node not found"}
        nid = node["id"]
        edges = self._conn.execute(
            "SELECT * FROM edges WHERE src = ? OR dst = ?", (nid, nid)
        ).fetchall()
        snapshot = {
            "node": node,
            "edges": [self._row_edge(e) for e in edges],
        }
        self._conn.execute("DELETE FROM edges WHERE src = ? OR dst = ?", (nid, nid))
        self._conn.execute("DELETE FROM nodes WHERE id = ?", (nid,))
        self._conn.commit()
        return {"ok": True, "deleted": "node", "snapshot": snapshot}

    def delete_edge(self, edge_id: str) -> dict[str, Any]:
        edge = self.get_edge(edge_id)
        if not edge:
            return {"ok": False, "error": "edge not found"}
        self._conn.execute("DELETE FROM edges WHERE id = ?", (edge_id,))
        self._conn.commit()
        return {"ok": True, "deleted": "edge", "snapshot": {"edge": edge}}

    def prune_orphans(self, *, namespace: str = "") -> dict[str, Any]:
        if namespace:
            rows = self._conn.execute(
                """
                SELECT n.* FROM nodes n
                WHERE n.namespace = ?
                  AND NOT EXISTS (SELECT 1 FROM edges e WHERE e.src = n.id OR e.dst = n.id)
                """,
                (namespace,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT n.* FROM nodes n
                WHERE NOT EXISTS (SELECT 1 FROM edges e WHERE e.src = n.id OR e.dst = n.id)
                """
            ).fetchall()
        snapshots = [self._row_node(r) for r in rows]
        for r in rows:
            self._conn.execute("DELETE FROM nodes WHERE id = ?", (r["id"],))
        self._conn.commit()
        return {"ok": True, "pruned": len(snapshots), "snapshot": {"nodes": snapshots}}

    def clear_namespace(self, namespace: str) -> dict[str, Any]:
        ns = (namespace or "").strip()
        if not ns or ns in {"relationships"}:
            # Allow clearing queries pollution; protect ACM mirror namespace unless explicit force via caller
            if ns != "queries":
                return {"ok": False, "error": "refusing to clear protected or empty namespace"}
        nodes = self.list_nodes(namespace=ns, limit=10000)
        edges = self.list_edges(namespace=ns, limit=10000)
        self._conn.execute("DELETE FROM edges WHERE namespace = ?", (ns,))
        self._conn.execute("DELETE FROM nodes WHERE namespace = ?", (ns,))
        self._conn.commit()
        return {
            "ok": True,
            "cleared": ns,
            "snapshot": {"nodes": nodes, "edges": edges},
        }

    def merge_entities(
        self,
        keep_name: str,
        drop_name: str,
        *,
        namespace: str = "default",
    ) -> dict[str, Any]:
        keep = self.get_node(keep_name, namespace=namespace)
        drop = self.get_node(drop_name, namespace=namespace)
        if not keep or not drop:
            return {"ok": False, "error": "both entities required"}
        if keep["id"] == drop["id"]:
            return {"ok": False, "error": "same entity"}
        kid, did = keep["id"], drop["id"]
        # Rewire edges
        for row in self._conn.execute("SELECT * FROM edges WHERE src = ? OR dst = ?", (did, did)):
            src = kid if row["src"] == did else row["src"]
            dst = kid if row["dst"] == did else row["dst"]
            if src == dst:
                self._conn.execute("DELETE FROM edges WHERE id = ?", (row["id"],))
                continue
            existing = self._conn.execute(
                "SELECT id FROM edges WHERE src = ? AND dst = ? AND rel = ? AND namespace = ?",
                (src, dst, row["rel"], row["namespace"]),
            ).fetchone()
            if existing:
                self._conn.execute("DELETE FROM edges WHERE id = ?", (row["id"],))
            else:
                self._conn.execute(
                    "UPDATE edges SET src = ?, dst = ? WHERE id = ?",
                    (src, dst, row["id"]),
                )
        snap = {"keep": keep, "drop": drop}
        self._conn.execute("DELETE FROM nodes WHERE id = ?", (did,))
        self._conn.commit()
        return {"ok": True, "merged_into": keep["name"], "snapshot": snap}

    def recent_activity(self, *, limit: int = 20) -> list[dict[str, Any]]:
        edges = self.list_edges(limit=limit)
        nodes = self.list_nodes(limit=limit)
        items: list[dict[str, Any]] = []
        for e in edges:
            items.append({"kind": "relationship", "at": e.get("created_at") or "", "item": e})
        for n in nodes:
            items.append(
                {
                    "kind": "entity",
                    "at": n.get("updated_at") or n.get("created_at") or "",
                    "item": n,
                }
            )
        items.sort(key=lambda x: x.get("at") or "", reverse=True)
        return items[:limit]

    def stats(self) -> dict[str, Any]:
        nodes = self._conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
        edges = self._conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        orphans = self._conn.execute(
            """
            SELECT COUNT(*) FROM nodes n
            WHERE NOT EXISTS (SELECT 1 FROM edges e WHERE e.src = n.id OR e.dst = n.id)
            """
        ).fetchone()[0]
        unknown = self._conn.execute(
            """
            SELECT COUNT(*) FROM edges
            WHERE memory_id = '' AND (props NOT LIKE '%"source"%' OR props LIKE '%"source": "unknown"%')
            """
        ).fetchone()[0]
        return {
            "nodes": int(nodes),
            "edges": int(edges),
            "orphans": int(orphans),
            "missing_provenance": int(unknown),
            "namespaces": len(self.namespaces()),
        }


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
        RETURN DISTINCT startNode(rel).name AS subject, type(rel) AS predicate, endNode(rel).name AS object,
               coalesce(rel.namespace, 'default') AS namespace,
               coalesce(rel.memory_id, '') AS memory_id,
               coalesce(rel.confidence, 0.0) AS confidence,
               coalesce(rel.source, 'unknown') AS source
        LIMIT $limit
        """
        with self._driver.session() as session:
            result = session.run(cypher, name=name, limit=limit)
            out = []
            for rec in result:
                if not rec["subject"] or not rec["object"]:
                    continue
                out.append(
                    {
                        "subject": rec["subject"],
                        "predicate": rec["predicate"],
                        "object": rec["object"],
                        "namespace": rec["namespace"],
                        "memory_id": rec["memory_id"],
                        "confidence": float(rec["confidence"] or 0),
                        "source": rec["source"],
                        "provenance": {
                            "source": rec["source"],
                            "memory_id": rec["memory_id"],
                            "confidence": float(rec["confidence"] or 0),
                            "namespace": rec["namespace"],
                        },
                    }
                )
            return out

    def search_nodes(self, query: str, *, limit: int = 12, namespace: str = "") -> list[dict]:
        q = (query or "").strip().lower()
        if not q:
            return []
        cypher = f"""
        MATCH (n:{ENTITY_LABEL})
        WHERE toLower(n.name) CONTAINS $q
          AND ($namespace = '' OR n.namespace = $namespace)
        RETURN n.name AS name, coalesce(n.kind, 'entity') AS kind,
               coalesce(n.namespace, 'default') AS namespace,
               coalesce(n.memory_id, '') AS memory_id
        ORDER BY n.name LIMIT $limit
        """
        with self._driver.session() as session:
            result = session.run(cypher, q=q, limit=limit, namespace=namespace or "")
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

    def stats(self) -> dict[str, Any]:
        with self._driver.session() as session:
            nodes = session.run(f"MATCH (n:{ENTITY_LABEL}) RETURN count(n) AS c").single()
            edges = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()
        return {
            "nodes": int(nodes["c"]) if nodes else 0,
            "edges": int(edges["c"]) if edges else 0,
            "orphans": 0,
            "missing_provenance": 0,
            "namespaces": 0,
        }

    # Destructive ops — best-effort on Bolt
    def get_node(self, name: str, *, namespace: str | None = None) -> dict[str, Any] | None:
        hits = self.search_nodes(name, limit=5, namespace=namespace or "")
        for h in hits:
            if str(h.get("name") or "").lower() == name.strip().lower():
                return h
        return hits[0] if hits else None

    def delete_node(self, name: str, *, namespace: str = "default") -> dict[str, Any]:
        with self._driver.session() as session:
            session.run(
                f"MATCH (n:{ENTITY_LABEL} {{name: $name}}) DETACH DELETE n",
                name=name.strip(),
            )
        return {"ok": True, "deleted": "node", "snapshot": {"name": name}}

    def delete_edge(self, edge_id: str) -> dict[str, Any]:
        return {
            "ok": False,
            "error": "bolt edge delete by id not supported; use subject/predicate/object",
        }

    def prune_orphans(self, *, namespace: str = "") -> dict[str, Any]:
        with self._driver.session() as session:
            result = session.run(
                # `NOT (n)--()` is a Neo4j-ism: Memgraph rejects the anonymous
                # pattern outright ("Not yet implemented: atom expression"), so
                # pruning always failed with a 500 against a Memgraph backend.
                # Counting incident relationships is plain Cypher and works on
                # both.
                f"""
                MATCH (n:{ENTITY_LABEL})
                WHERE ($namespace = '' OR n.namespace = $namespace)
                OPTIONAL MATCH (n)-[r]-()
                WITH n, count(r) AS degree
                WHERE degree = 0
                DETACH DELETE n
                RETURN count(*) AS c
                """,
                namespace=namespace or "",
            )
            c = result.single()
        return {"ok": True, "pruned": int(c["c"]) if c else 0, "snapshot": {"nodes": []}}

    def clear_namespace(self, namespace: str) -> dict[str, Any]:
        if namespace != "queries":
            return {"ok": False, "error": "refusing to clear protected namespace on bolt"}
        with self._driver.session() as session:
            session.run(
                f"MATCH (n:{ENTITY_LABEL} {{namespace: $ns}}) DETACH DELETE n",
                ns=namespace,
            )
        return {"ok": True, "cleared": namespace, "snapshot": {"nodes": [], "edges": []}}

    def namespaces(self) -> list[dict[str, Any]]:
        with self._driver.session() as session:
            result = session.run(
                f"""
                MATCH (n:{ENTITY_LABEL})
                RETURN coalesce(n.namespace, 'default') AS namespace, count(*) AS nodes
                """
            )
            return [
                {"namespace": r["namespace"], "nodes": int(r["nodes"]), "edges": 0} for r in result
            ]

    def list_nodes(
        self, *, namespace: str = "", kind: str = "", limit: int = 50, offset: int = 0, q: str = ""
    ) -> list[dict]:
        cypher, params = _bolt_list_nodes_query(
            namespace=namespace, kind=kind, limit=limit, offset=offset, q=q
        )
        with self._driver.session() as session:
            return [dict(rec) for rec in session.run(cypher, **params)]

    def list_edges(
        self, *, namespace: str = "", limit: int = 50, offset: int = 0, q: str = ""
    ) -> list[dict]:
        cypher, params = _bolt_list_edges_query(
            namespace=namespace, limit=limit, offset=offset, q=q
        )
        with self._driver.session() as session:
            out = []
            for rec in session.run(cypher, **params):
                if not rec["subject"] or not rec["object"]:
                    continue
                out.append(
                    {
                        "subject": rec["subject"],
                        "predicate": rec["predicate"],
                        "object": rec["object"],
                        "namespace": rec["namespace"],
                        "memory_id": rec["memory_id"],
                        "confidence": float(rec["confidence"] or 0),
                        "source": rec["source"],
                        "provenance": {
                            "source": rec["source"],
                            "memory_id": rec["memory_id"],
                            "confidence": float(rec["confidence"] or 0),
                            "namespace": rec["namespace"],
                        },
                    }
                )
            return out

    def get_edge(self, edge_id: str) -> dict[str, Any] | None:
        return None

    def merge_entities(
        self, keep_name: str, drop_name: str, *, namespace: str = "default"
    ) -> dict[str, Any]:
        self.delete_node(drop_name, namespace=namespace)
        return {"ok": True, "merged_into": keep_name, "snapshot": {}}

    def recent_activity(self, *, limit: int = 20) -> list[dict[str, Any]]:
        return []


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


def reset_graph_store_for_tests(store: GraphMemoryStore | None = None) -> GraphMemoryStore | None:
    """Replace or clear the process singleton (tests only)."""
    global _GRAPH_SINGLETON
    if _GRAPH_SINGLETON is not None:
        try:
            _GRAPH_SINGLETON.close()
        except Exception:
            pass
    _GRAPH_SINGLETON = store
    return _GRAPH_SINGLETON
