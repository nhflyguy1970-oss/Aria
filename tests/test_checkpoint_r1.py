"""R1: project checkpoint write/read must share one authoritative SoT."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture()
def primary_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_LEGACY_READ_FALLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_AUTO_PERSIST", "1")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "cog.db"))
    monkeypatch.setenv("ARIA_TEACHING_DEBUG", "0")
    from aria_core import acm_bridge, memory_manager

    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
    yield
    acm_bridge.reset_for_tests()
    memory_manager.reset_for_tests()


@pytest.fixture()
def rollback_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "1")
    monkeypatch.setenv("ARIA_ACM_LEGACY_READ_FALLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_AUTO_PERSIST", "0")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "cog-rollback.db"))
    from aria_core import acm_bridge, memory_manager

    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
    yield
    acm_bridge.reset_for_tests()
    memory_manager.reset_for_tests()


def _legacy_poison(store, content: str = "LEGACY_POISON_CHECKPOINT") -> None:
    store._data["entries"] = [
        {
            "id": "legacy-cp-poison",
            "type": "project",
            "content": content,
            "tags": ["checkpoint", "project-state"],
            "namespace": "default",
            "timestamp": "2099-01-01T00:00:00+00:00",
            "access_count": 0,
            "relevance": 1.0,
        }
    ]


def test_checkpoint_create_and_lookup_primary(primary_env, tmp_path):
    from jarvis.modules.memory import MemoryStore

    store = MemoryStore(tmp_path / "cp.json")
    _legacy_poison(store)
    written = store.upsert_checkpoint("ACM checkpoint alpha", namespace="default")
    assert "alpha" in written["content"]
    assert written.get("source") == "acm" or written.get("id")
    hit = store.latest_checkpoint("default")
    assert hit is not None
    assert "alpha" in hit["content"]
    assert "LEGACY_POISON" not in hit["content"]
    assert hit.get("source") == "acm"


def test_checkpoint_update_keeps_latest(primary_env, tmp_path):
    from jarvis.modules.memory import MemoryStore

    store = MemoryStore(tmp_path / "cp.json")
    store.upsert_checkpoint("first state", namespace="work")
    store.upsert_checkpoint("second state", namespace="work")
    hit = store.latest_checkpoint("work")
    assert hit is not None
    assert "second state" in hit["content"]
    assert store.latest_checkpoint("other") is None


def test_checkpoint_ignores_legacy_vault_under_primary(primary_env, tmp_path):
    from jarvis.modules.memory import MemoryStore

    store = MemoryStore(tmp_path / "cp.json")
    _legacy_poison(store, "only in legacy vault")
    assert store.latest_checkpoint() is None
    assert store.latest_checkpoint("default") is None


def test_checkpoint_restart_persists(primary_env, tmp_path, monkeypatch):
    from aria_core import acm_bridge, memory_manager
    from jarvis.modules.memory import MemoryStore

    persist = tmp_path / "cog.db"
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(persist))
    store = MemoryStore(tmp_path / "cp.json")
    store.upsert_checkpoint("survives restart", namespace="default")
    assert "survives restart" in (store.latest_checkpoint("default") or {}).get("content", "")

    acm_bridge.reset_for_tests()
    memory_manager.reset_for_tests()
    store2 = MemoryStore(tmp_path / "cp2.json")
    _legacy_poison(store2, "post-restart poison")
    hit = store2.latest_checkpoint("default")
    assert hit is not None
    assert "survives restart" in hit["content"]
    assert "poison" not in hit["content"]


def test_checkpoint_rollback_uses_legacy_only(rollback_env, tmp_path):
    from aria_core import acm_bridge
    from jarvis.modules.memory import MemoryStore

    assert acm_bridge.acm_is_authoritative() is False
    store = MemoryStore(tmp_path / "cp.json")
    written = store.upsert_checkpoint("legacy rollback cp", namespace="default")
    assert any(e.get("id") == written["id"] for e in store._data["entries"])
    hit = store.latest_checkpoint("default")
    assert hit is not None
    assert "legacy rollback cp" in hit["content"]
    assert hit.get("source") != "acm"


def test_sqlite_checkpoint_primary_round_trip(primary_env, tmp_path):
    from jarvis.modules.memory_sqlite import SqliteMemoryStore

    db = tmp_path / "mem.db"
    store = SqliteMemoryStore(path=db)
    # Insert poison row directly into sqlite vault
    store._conn.execute(
        "INSERT INTO memories (id, type, content, tags, namespace, timestamp, access_count, relevance) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "legacy-sql-cp",
            "project",
            "SQL_POISON",
            '["checkpoint","project-state"]',
            "default",
            "2099-01-01T00:00:00+00:00",
            0,
            1.0,
        ),
    )
    store._conn.commit()
    store.upsert_checkpoint("sqlite acm checkpoint", namespace="default")
    hit = store.latest_checkpoint("default")
    assert hit is not None
    assert "sqlite acm checkpoint" in hit["content"]
    assert "SQL_POISON" not in hit["content"]


def test_project_resume_reads_acm_checkpoint(primary_env, tmp_path, monkeypatch):
    from jarvis.behaviors.memory.engine import MemoryEngine
    from jarvis.modules.memory import MemoryStore

    store = MemoryStore(tmp_path / "cp.json")
    _legacy_poison(store, "should not resume")
    store.upsert_checkpoint("resume from ACM content", namespace="default")

    ctx = SimpleNamespace(
        memory=store,
        session=SimpleNamespace(last_file=None, memory_namespace="default"),
    )
    monkeypatch.setattr(MemoryEngine, "project_namespace", classmethod(lambda cls, c: "default"))
    out = MemoryEngine.project_resume(ctx, {}, "")
    assert out.get("ok") is True
    assert "resume from ACM content" in (out.get("response") or out.get("message") or str(out))
    assert "should not resume" not in str(out)
