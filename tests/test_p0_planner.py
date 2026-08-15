"""Tests for P0 planner and HA fuzzy helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def planner_db(tmp_path, monkeypatch):
    db = tmp_path / "planner.db"
    monkeypatch.setattr("jarvis.planner_store.DB_PATH", db)
    monkeypatch.setenv("JARVIS_PLANNER", "1")
    import jarvis.planner_store as ps

    ps._init_db()
    return ps


def test_planner_task_and_timer(planner_db):
    ps = planner_db
    task = ps.add_task("buy milk")
    assert task["text"] == "buy milk"
    assert len(ps.list_tasks()) == 1
    timer = ps.set_timer("5 minutes", "tea")
    assert timer["remaining_seconds"] >= 299
    assert len(ps.active_timers()) == 1


def test_parse_duration(planner_db):
    ps = planner_db
    assert ps._parse_duration("10 minutes") == 600
    assert ps._parse_duration("1 hour") == 3600


def test_ha_aliases_resolve(tmp_path, monkeypatch):
    alias_file = tmp_path / "ha_aliases.json"
    alias_file.write_text(
        json.dumps({"aliases": {"office": ["light.left", "light.right"]}}),
        encoding="utf-8",
    )
    monkeypatch.setattr("jarvis.ha_aliases.ALIASES_FILE", alias_file)
    from jarvis.ha_aliases import resolve_alias

    assert resolve_alias("office") == ["light.left", "light.right"]


def test_tool_permissions_defaults():
    from jarvis.tool_permissions import get_permissions

    perms = get_permissions()
    assert perms["write_file"] == "ask"
    assert perms["ha_control"] == "never"


def test_system_info_builds():
    from unittest.mock import MagicMock

    from jarvis.system_info import build_system_info

    info = build_system_info(assistant=MagicMock())
    assert "greeting" in info
    assert "feature_flags" in info


def test_checklist():
    from unittest.mock import MagicMock

    from jarvis.p0_checklist import run_checklist

    result = run_checklist(assistant=MagicMock())
    assert "checks" in result
    assert result["total"] >= 3
