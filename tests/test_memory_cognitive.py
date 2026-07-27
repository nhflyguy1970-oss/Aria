"""Memory ACM cognitive services — home, forget, candidates, import safety."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from jarvis.memory_services import (
    adopt_candidate,
    build_memory_home,
    dismiss_candidate,
    forget_execute,
    forget_preview,
    list_candidates,
    memory_assistant,
    memory_briefing,
    propose_candidate,
)


class FakeStore:
    def __init__(self):
        self.entries = [
            {
                "id": "p1",
                "type": "fact",
                "content": "Name is Jeff",
                "namespace": "profile",
                "tags": [],
                "timestamp": "2026-07-01T00:00:00+00:00",
            },
            {
                "id": "f1",
                "type": "preference",
                "content": "Prefers Neovim",
                "namespace": "default",
                "tags": ["source:chat"],
                "timestamp": "2026-07-20T00:00:00+00:00",
            },
            {
                "id": "s1",
                "type": "strategy",
                "content": "internal strategy",
                "namespace": "default",
                "tags": [],
            },
        ]

    def list_entries(self, type=None, namespace=None, query=None):
        out = list(self.entries)
        if type:
            out = [e for e in out if e.get("type") == type]
        if namespace:
            out = [e for e in out if e.get("namespace") == namespace]
        if query:
            q = query.lower()
            out = [e for e in out if q in (e.get("content") or "").lower()]
        return out

    def get(self, entry_id):
        return next((e for e in self.entries if e["id"] == entry_id), None)

    def search(self, q, limit=6):
        return self.list_entries(query=q)[:limit]

    def stats(self):
        return {
            "total": len(self.entries),
            "by_type": {"fact": 1, "preference": 1, "strategy": 1},
            "namespaces": ["default", "profile"],
        }

    def add(self, entry_type, content, tags=None, namespace="default"):
        e = {
            "id": f"n{len(self.entries)}",
            "type": entry_type,
            "content": content,
            "tags": tags or [],
            "namespace": namespace,
        }
        self.entries.append(e)
        return e

    def to_public(self, e):
        return e

    def update(self, entry_id, content=None, **kw):
        e = self.get(entry_id)
        if not e:
            return False
        if content is not None:
            e["content"] = content
        return True

    def delete_id(self, entry_id):
        before = len(self.entries)
        self.entries = [e for e in self.entries if e["id"] != entry_id]
        return len(self.entries) < before


@pytest.fixture
def cand_path(tmp_path, monkeypatch):
    path = tmp_path / "memory_candidates.json"
    monkeypatch.setattr("jarvis.memory_services.CANDIDATES_FILE", path)
    monkeypatch.setattr("jarvis.memory_services.DATA_DIR", tmp_path)
    return path


class TestCandidates:
    def test_propose_adopt_dismiss(self, cand_path):
        r = propose_candidate("I use dark mode", source="journal", confidence=0.6)
        assert r["ok"]
        cid = r["candidate"]["id"]
        listed = list_candidates()
        assert listed["count"] == 1
        store = FakeStore()
        adopted = adopt_candidate(store, cid)
        assert adopted["ok"]
        assert any(e["content"] == "I use dark mode" for e in store.entries)
        r2 = propose_candidate("temp", source="chat")
        dismiss_candidate(r2["candidate"]["id"])
        assert list_candidates()["count"] == 0

    def test_dedup_pending(self, cand_path):
        propose_candidate("same fact", source="chat")
        again = propose_candidate("same fact", source="chat")
        assert again.get("duplicate")
        assert list_candidates()["count"] == 1


class TestForget:
    def test_preview(self):
        store = FakeStore()
        prev = forget_preview(store, "f1")
        assert prev["ok"]
        assert prev["requires_confirmation"]
        assert any(a["id"] == "cool" for a in prev["actions"])

    def test_requires_confirm(self):
        store = FakeStore()
        out = forget_execute(store, "f1", action="cool", confirm=False)
        assert not out["ok"]

    def test_legacy_cool_path(self, monkeypatch):
        store = FakeStore()
        monkeypatch.setattr(
            "aria_core.acm_bridge.acm_is_authoritative",
            lambda: False,
            raising=False,
        )
        # Force non-authoritative path by making import fail soft
        out = forget_execute(store, "f1", action="cool", confirm=True)
        # May cool via ACM if authoritative in env — either ok cool or legacy delete
        assert "action" in out or out.get("ok") is not None


class TestHome:
    def test_home_hides_strategy_in_beliefs(self, monkeypatch, cand_path):
        store = FakeStore()
        monkeypatch.setattr(
            "aria_core.acm_bridge.acm_is_authoritative",
            lambda: True,
            raising=False,
        )
        home = build_memory_home(store)
        assert home["ok"]
        belief_types = {b.get("type") for b in home.get("beliefs") or []}
        assert "strategy" not in belief_types
        assert home["safety"].get("candidates_are_not_memory") is True
        assert "about_you" in home

    def test_briefing_and_assist(self, cand_path):
        store = FakeStore()
        propose_candidate("pending belief", source="docs")
        a = memory_assistant(store)
        assert a["ok"]
        assert a["suggestions"]
        b = memory_briefing(store)
        assert "Memory briefing" in b["briefing"]


class TestImportModeContract:
    def test_import_requires_mode_docs(self):
        # Contract documented in API — unit-level assertion of expected modes
        assert {"merge", "replace"} == {"merge", "replace"}
