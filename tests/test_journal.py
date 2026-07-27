"""Comprehensive Journal tests — rapid log, habits, promote, crypto, services."""

from __future__ import annotations

import json
import os
from datetime import date, timedelta
from pathlib import Path

import pytest

from jarvis.modules.journal import BulletJournal, _month_key, _today, _week_key
from jarvis.journal_crypto import decrypt_import, encrypt_export
from jarvis.journal_services import (
    create_backup,
    disambiguate_tasks_intent,
    migration_assistant,
    month_end_wizard,
    parse_voice_rapid_log,
    promotion_assistant,
    vision_import_preview,
    writing_assistant,
)


@pytest.fixture
def journal(tmp_path, monkeypatch):
    path = tmp_path / "bullet_journal.json"
    monkeypatch.setenv("JARVIS_LIVE_DATA_OK", "1")
    # Avoid planner DB side effects when possible
    j = BulletJournal(path=path)
    return j


class TestRapidLogRouting:
    def test_daily_section(self, journal):
        bullets = journal.parse_rapid_log("buy milk\nn: idea", section="daily")
        assert len(bullets) == 2
        day = journal.daily_get()
        contents = [b["content"] for b in day["bullets"]]
        assert "buy milk" in contents
        assert "idea" in contents

    def test_weekly_section(self, journal):
        wk = _week_key()
        bullets = journal.parse_rapid_log("week goal", section="weekly", week=wk)
        assert len(bullets) == 1
        page = journal.weekly_get(wk)
        assert any(b["content"] == "week goal" for b in page["bullets"])
        # Must not land in daily
        day = journal.daily_get()
        assert not any(b["content"] == "week goal" for b in day.get("bullets", []))

    def test_monthly_section(self, journal):
        mk = _month_key()
        journal.parse_rapid_log("month theme", section="monthly", month=mk)
        page = journal.monthly_get(mk)
        assert any(b["content"] == "month theme" for b in page["bullets"])

    def test_future_section(self, journal):
        mk = _month_key()
        journal.parse_rapid_log("someday trip", section="future", month=mk)
        fl = journal.future_list(mk)
        assert any(b["content"] == "someday trip" for b in fl)

    def test_invalid_section(self, journal):
        with pytest.raises(ValueError):
            journal.parse_rapid_log("x", section="galaxy")

    def test_nesting_indent(self, journal):
        text = "parent task\n  child note"
        bullets = journal.parse_rapid_log(text, section="daily")
        assert len(bullets) == 2
        parent = journal.daily_get()["bullets"][0]
        assert parent["content"] == "parent task"
        assert parent.get("children")
        assert parent["children"][0]["content"] == "child note"

    def test_symbols(self, journal):
        bullets = journal.parse_rapid_log(
            "× done already\n> migrated item\n○ meetup\n— a note\n* priority"
        )
        by = {b["content"]: b for b in bullets}
        assert by["done already"]["status"] == "done"
        assert by["migrated item"]["status"] == "migrated"
        assert by["meetup"]["type"] == "event"
        assert by["a note"]["type"] == "note"
        assert "important" in by["priority"].get("signifiers", [])


class TestHabitStreaks:
    def test_streak_and_longest(self, journal):
        h = journal.habit_create("Walk")
        hid = h["id"]
        today = date.today()
        # Mark today and two prior days done (toggle from False → True)
        for i in range(3):
            d = (today - timedelta(days=i)).isoformat()
            journal.habit_toggle(hid, d)
        # Older broken streak of 2
        for i in range(10, 12):
            d = (today - timedelta(days=i)).isoformat()
            journal.habit_toggle(hid, d)
        tracker = journal.habit_tracker(_month_key())
        row = next(x for x in tracker["habits"] if x["id"] == hid)
        assert row["streak"] >= 3
        assert row["longest_streak"] >= 3
        assert row["completion_pct"] >= 0
        assert "week_done" in row


class TestPromotePlanner:
    def test_promote_and_unlink(self, journal, monkeypatch, tmp_path):
        monkeypatch.setenv("JARVIS_PLANNER", "1")
        from jarvis import planner_store

        db = tmp_path / "planner_test.db"
        monkeypatch.setattr(planner_store, "DB_PATH", db)
        planner_store._init_db()
        b = journal.daily_add("Ship the release", "task")
        result = journal.promote_to_planner(b["id"])
        assert result["ok"]
        assert result["planner_task_id"]
        found = journal._find_bullet(b["id"])[0]
        assert found["planner_task_id"] == result["planner_task_id"]
        again = journal.promote_to_planner(b["id"])
        assert again.get("already_linked")
        un = journal.unlink_planner(b["id"])
        assert un["ok"]
        assert "planner_task_id" not in journal._find_bullet(b["id"])[0]


class TestUndoHistorySidecar:
    def test_history_not_in_main_file(self, journal):
        journal.daily_add("one", "note")
        journal.daily_add("two", "note")
        raw = json.loads(journal.path.read_text(encoding="utf-8"))
        assert "history" not in raw or raw.get("history") in ([], None)
        # Sidecar may exist after saves
        side = journal._history_path()
        if side.exists():
            data = json.loads(side.read_text(encoding="utf-8"))
            assert "history" in data


class TestCrypto:
    def test_encrypt_roundtrip(self):
        payload = {"version": 1, "daily_log": {"2026-01-01": {"bullets": []}}}
        enc = encrypt_export(payload, "test-password")
        assert enc["format"] == "jarvis-journal-v1"
        out = decrypt_import(enc, "test-password")
        assert out["version"] == 1

    def test_wrong_password(self):
        enc = encrypt_export({"a": 1}, "correct-horse")
        with pytest.raises(ValueError):
            decrypt_import(enc, "wrong")


class TestServices:
    def test_disambiguate_planner(self):
        r = disambiguate_tasks_intent("open my planner tasks")
        assert r["action"] == "planner_today"

    def test_disambiguate_journal(self):
        r = disambiguate_tasks_intent("show journal tasks")
        assert r["action"] == "journal_open_tasks"

    def test_disambiguate_ambiguous(self):
        r = disambiguate_tasks_intent("open tasks")
        assert r["action"] == "clarify"
        assert r.get("needs_clarification")

    def test_voice_parse(self):
        r = parse_voice_rapid_log("task buy bread then note call mom")
        assert r["ok"]
        assert "buy bread" in r["text"]
        assert r["requires_confirmation"]

    def test_vision_preview(self):
        r = vision_import_preview(ocr_text="• one\n• two", source="notebook")
        assert r["ok"]
        assert len(r["preview_lines"]) == 2
        assert r["requires_confirmation"]

    def test_writing_assistant(self):
        r = writing_assistant("t: ship\nn: thought", mode="organize")
        assert r["ok"]
        assert r["suggestions"]

    def test_promotion_and_migration(self, journal):
        journal.daily_add("finish taxes", "task")
        journal.daily_add("meet dentist tomorrow", "task")
        p = promotion_assistant(journal)
        assert p["ok"]
        m = migration_assistant(journal, "daily")
        assert m["ok"]
        assert m["requires_confirmation"]

    def test_month_end_wizard(self, journal):
        w = month_end_wizard(journal)
        assert w["ok"]
        assert w["steps"]

    def test_backup(self, journal):
        journal.daily_add("backup me", "note")
        r = create_backup(journal)
        assert r["ok"]
        assert Path(r["path"]).exists()


class TestSearchMigrationReflection:
    def test_search(self, journal):
        journal.daily_add("unique-zebra-thought", "note")
        hits = journal.search("zebra")
        assert hits

    def test_migrate_bullet(self, journal):
        b = journal.daily_add("carry me", "task")
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        moved = journal.bullet_migrate(b["id"], tomorrow)
        assert moved
        day = journal.daily_get(tomorrow)
        assert any(x["content"] == "carry me" for x in day["bullets"])

    def test_open_tasks(self, journal):
        journal.daily_add("still open", "task")
        journal.daily_add("a note", "note")
        tasks = journal.open_tasks()
        assert any(t["content"] == "still open" for t in tasks)

    def test_collections(self, journal):
        journal.collection_create("Ideas", "seed")
        journal.collection_add("Ideas", "spark", "note")
        col = journal.collection_get("Ideas")
        assert col and col["bullets"]


class TestImportValidation:
    def test_import_strips_history(self, journal):
        journal.import_all(
            {
                "version": 1,
                "daily_log": {},
                "history": [{"ts": "x", "data": {}}],
                "redo": [{"ts": "y", "data": {}}],
            }
        )
        exported = journal.export_all()
        assert "history" not in exported
        assert "redo" not in exported
