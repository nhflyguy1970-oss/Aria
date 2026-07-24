"""Regression: calendar day merges planner tasks; knowledge search always tries memory."""

from __future__ import annotations

from datetime import date
from unittest.mock import patch


def test_pick_strategies_includes_memory_without_retrieval_flag():
    from jarvis.knowledge.registry import KnowledgeSource
    from jarvis.knowledge.search import _pick_strategies

    sources = [
        KnowledgeSource(
            id="conv",
            type="conversation",
            label="Conversation Memory",
            location="memory",
            retrieval_available=False,
        ),
        KnowledgeSource(
            id="notes",
            type="notes",
            label="Journal",
            location="journal",
            retrieval_available=True,
        ),
    ]
    strategies = _pick_strategies("jeff", sources)
    assert "memory" in strategies
    assert "journal" in strategies


def test_search_memory_falls_through_when_acm_returns_empty():
    from jarvis.knowledge import search as ks

    class Mem:
        def search(self, query, limit=5):
            return [{"id": "m1", "content": f"local hit for {query}", "namespace": "profile"}]

    class Asst:
        memory = Mem()

    with patch("aria_core.acm_bridge.acm_is_authoritative", return_value=True), patch(
        "aria_core.acm_bridge.primary_search", return_value=[]
    ), patch("jarvis.assistant_instance.get_assistant", return_value=Asst()):
        hits = ks._search_memory("Jeff", 5)
    assert hits
    assert "local hit" in hits[0]["excerpt"]


def test_calendar_day_includes_planner_tasks_for_today(data_dir, monkeypatch):
    from jarvis import calendar_tab
    from jarvis import planner_store

    monkeypatch.setattr(planner_store, "DB_PATH", data_dir / "planner.db")
    planner_store._init_db()
    task = planner_store.add_task("cert-calendar-merge-task")

    class FakeJournal:
        def monthly_calendar(self, mk):
            return {"calendar_notes": {}, "holidays": {}}

        def daily_get(self, day, enrich=False):
            return {"title": day, "bullets": []}

        def daily_timeline(self, day):
            return {"events": []}

    detail = calendar_tab.day_detail(FakeJournal(), date.today().isoformat())
    assert any(t.get("id") == task["id"] for t in detail.get("planner_tasks") or [])
    assert any("cert-calendar-merge-task" in (t.get("content") or "") for t in detail["planner_tasks"])
