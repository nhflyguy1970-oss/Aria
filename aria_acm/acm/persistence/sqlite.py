"""SQLite durable backend — replaceable technology choice owned by ACM."""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from time import time
from typing import Any

from acm.core.store import CognitiveStore
from acm.persistence.codec import export_store, import_store, verify_snapshot
from acm.persistence.schema import SCHEMA_VERSION


class SqliteDurableStore:
    """Transactional snapshot persistence for CognitiveStore."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS meta (
                  key TEXT PRIMARY KEY,
                  value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS snapshots (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  kind TEXT NOT NULL,
                  created REAL NOT NULL,
                  schema_version INTEGER NOT NULL,
                  checksum TEXT NOT NULL,
                  payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS ops (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  created REAL NOT NULL,
                  op TEXT NOT NULL,
                  detail TEXT NOT NULL
                );
                """
            )
            cur = self._conn.execute(
                "SELECT value FROM meta WHERE key='schema_version'"
            )
            row = cur.fetchone()
            if row is None:
                self._conn.execute(
                    "INSERT INTO meta(key, value) VALUES('schema_version', ?)",
                    (str(SCHEMA_VERSION),),
                )
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def save(self, store: CognitiveStore, *, kind: str = "checkpoint") -> dict[str, Any]:
        payload = export_store(store)
        with self._lock:
            self._conn.execute(
                "INSERT INTO snapshots(kind, created, schema_version, checksum, payload) "
                "VALUES(?,?,?,?,?)",
                (
                    kind,
                    time(),
                    int(payload["schema_version"]),
                    str(payload["checksum"]),
                    json.dumps(payload),
                ),
            )
            self._conn.execute(
                "INSERT INTO ops(created, op, detail) VALUES(?,?,?)",
                (time(), "save", kind),
            )
            self._conn.commit()
        return {
            "ok": True,
            "kind": kind,
            "checksum": payload["checksum"],
            "schema_version": payload["schema_version"],
            "path": str(self.path),
        }

    def load_latest(self, store: CognitiveStore | None = None) -> CognitiveStore:
        with self._lock:
            cur = self._conn.execute(
                "SELECT payload FROM snapshots ORDER BY id DESC LIMIT 1"
            )
            row = cur.fetchone()
        if row is None:
            return store or CognitiveStore()
        payload = json.loads(row[0])
        errors = verify_snapshot(payload)
        if errors:
            raise ValueError(f"corrupt snapshot: {'; '.join(errors)}")
        loaded = import_store(payload, store=store)
        with self._lock:
            self._conn.execute(
                "INSERT INTO ops(created, op, detail) VALUES(?,?,?)",
                (time(), "load", payload.get("checksum", "")),
            )
            self._conn.commit()
        return loaded

    def export_file(self, store: CognitiveStore, dest: str | Path) -> dict[str, Any]:
        payload = export_store(store)
        dest_p = Path(dest)
        dest_p.parent.mkdir(parents=True, exist_ok=True)
        dest_p.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        with self._lock:
            self._conn.execute(
                "INSERT INTO ops(created, op, detail) VALUES(?,?,?)",
                (time(), "export", str(dest_p)),
            )
            self._conn.commit()
        return {"ok": True, "path": str(dest_p), "checksum": payload["checksum"]}

    def import_file(self, src: str | Path, store: CognitiveStore | None = None) -> CognitiveStore:
        payload = json.loads(Path(src).read_text(encoding="utf-8"))
        errors = verify_snapshot(payload)
        if errors:
            raise ValueError("; ".join(errors))
        loaded = import_store(payload, store=store)
        self.save(loaded, kind="import")
        return loaded

    def backup(self, dest: str | Path) -> dict[str, Any]:
        dest_p = Path(dest)
        dest_p.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            self._conn.commit()
            backup = sqlite3.connect(str(dest_p))
            try:
                self._conn.backup(backup)
            finally:
                backup.close()
            self._conn.execute(
                "INSERT INTO ops(created, op, detail) VALUES(?,?,?)",
                (time(), "backup", str(dest_p)),
            )
            self._conn.commit()
        return {"ok": True, "path": str(dest_p)}

    def restore_backup(self, src: str | Path) -> dict[str, Any]:
        src_p = Path(src)
        with self._lock:
            self._conn.close()
            self.path.write_bytes(src_p.read_bytes())
            self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._init_schema()
            self._conn.execute(
                "INSERT INTO ops(created, op, detail) VALUES(?,?,?)",
                (time(), "restore", str(src_p)),
            )
            self._conn.commit()
        return {"ok": True, "path": str(self.path), "restored_from": str(src_p)}

    def integrity(self) -> dict[str, Any]:
        with self._lock:
            cur = self._conn.execute("PRAGMA integrity_check")
            result = cur.fetchone()[0]
            count = self._conn.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0]
            latest = self._conn.execute(
                "SELECT checksum, schema_version, created FROM snapshots ORDER BY id DESC LIMIT 1"
            ).fetchone()
        return {
            "integrity_check": result,
            "snapshot_count": int(count),
            "latest_checksum": None if latest is None else latest[0],
            "latest_schema_version": None if latest is None else latest[1],
            "latest_created": None if latest is None else latest[2],
            "ok": result == "ok",
        }

    def metrics(self) -> dict[str, Any]:
        info = self.integrity()
        size = self.path.stat().st_size if self.path.exists() else 0
        return {
            "backend": "sqlite",
            "path": str(self.path),
            "bytes": size,
            **info,
        }
