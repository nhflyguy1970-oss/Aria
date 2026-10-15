"""Tests must not be able to modify production data.

The document parse cache, platform notifications and the activity log built
their paths from PROJECT_ROOT instead of DATA_DIR, so test runs wrote into the
live data/ directory. They now follow DATA_DIR, and an audit-hook barrier
(installed by conftest) refuses any write under the production roots.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest

from jarvis.live_data_guard import take_write_violations

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "data"
PROBE = LIVE / "documents" / ".cache" / "barrier-probe-never-created.json"


def _refused(fn) -> list[str]:
    with pytest.raises(PermissionError):
        fn()
    # Consume the violation so the autouse guard does not fail this test.
    return take_write_violations()


def test_file_writes_under_live_data_are_refused():
    assert _refused(lambda: PROBE.write_text("x"))
    assert _refused(lambda: open(LIVE / "logs" / "barrier-probe.log", "a"))
    assert _refused(lambda: os.open(LIVE / "barrier-probe", os.O_CREAT | os.O_WRONLY))
    assert _refused(lambda: (LIVE / "barrier-probe-dir").mkdir())
    assert not PROBE.exists()


def test_relative_paths_are_resolved_against_the_cwd(monkeypatch):
    monkeypatch.chdir(ROOT)
    assert _refused(lambda: open("data/barrier-probe.txt", "w"))


def test_sqlite_write_connections_are_refused_but_read_only_ones_allowed():
    assert _refused(lambda: sqlite3.connect(LIVE / "barrier-probe.db"))
    live_db = LIVE / "memory.db"
    if live_db.is_file():
        sqlite3.connect(f"file:{live_db}?mode=ro", uri=True).close()
    assert take_write_violations() == []


def test_reads_are_still_allowed():
    env = LIVE / "jarvis.env"
    if env.is_file():
        env.read_bytes()
    assert take_write_violations() == []


def test_the_isolated_root_stays_writable(data_dir):
    (data_dir / "documents").mkdir(parents=True, exist_ok=True)
    (data_dir / "documents" / "ok.md").write_text("fine", encoding="utf-8")
    assert take_write_violations() == []


def test_former_leaks_now_follow_data_dir(data_dir):
    from jarvis import document_pipeline, platform_notifications, workstation_activity

    for path in (
        document_pipeline.DOCUMENTS_DIR,
        document_pipeline.CACHE_DIR,
        platform_notifications._STORE,
        workstation_activity._ACTIVITY_FILE,
    ):
        assert data_dir in Path(path).resolve().parents, path


def test_parsing_a_temp_document_caches_inside_the_test_root(tmp_path, data_dir):
    from jarvis import document_pipeline

    doc = tmp_path / "note.md"
    doc.write_text("# Note\nHook and thread.", encoding="utf-8")
    document_pipeline.parse_document(doc)
    cached = list(Path(document_pipeline.CACHE_DIR).glob("*.json"))
    assert cached and all(data_dir in c.resolve().parents for c in cached)
    assert take_write_violations() == []


def test_notifications_and_activity_write_inside_the_test_root(data_dir):
    from jarvis import platform_notifications, workstation_activity

    platform_notifications.notify("barrier test", detail="unit test")
    workstation_activity.record_event("test_event", component="test", detail="barrier test")
    assert (data_dir / "logs" / "platform_notifications.jsonl").is_file()
    assert (data_dir / "logs" / "workstation_activity.jsonl").is_file()
    assert take_write_violations() == []


def test_ai_platform_storage_is_confined(data_dir):
    """Platform storage derives from AI_ROOT, so DATA_ROOT alone never confined it."""
    from aiplatform.config import config

    for key in (
        "memory.storage_path",
        "history.storage_path",
        "knowledge.root",
        "embedding.index_location",
        "backups.root",
        "exports.root",
        "applications.root",
        "data.root",
    ):
        value = Path(str(config.get(key, "")))
        assert data_dir in value.resolve().parents, f"{key}={value}"
