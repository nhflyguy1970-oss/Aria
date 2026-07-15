"""Regression: recall answers, search ranks user facts, forget is precise."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from jarvis.behaviors.memory.engine import MemoryEngine
from jarvis.modules.memory import create_memory_store
from jarvis.modules.memory_common import (
    filter_user_facing,
    format_recall_answer,
    normalize_memory_query,
    select_forget_targets,
)
from jarvis.session import SessionContext


@pytest.fixture()
def mem_ctx(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # Forensic CRUD ranking helpers — run with PRIMARY off (ROLLBACK window tests).
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "0")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    store = create_memory_store(tmp_path / "mem.json")
    store.add(
        "preference",
        "My favorite coffee is medium roast.",
        tags=["layer:long_term"],
        namespace="default",
    )
    store.add(
        "fact",
        "My favorite color is blue.",
        tags=["layer:long_term"],
        namespace="default",
    )
    store.add(
        "fact",
        "My dog's name is Zeus.",
        tags=["layer:long_term"],
        namespace="default",
    )
    store.add(
        "strategy",
        "Tool `memory_search` worked for: coffee",
        tags=["tool-outcome", "memory_search"],
        namespace="jarvis",
    )
    store.add(
        "strategy",
        "When answering, prefer bullets.",
        tags=["trust", "user"],
        namespace="jarvis",
    )
    store.add(
        "auto",
        "Telemetry: session duration 42s gpu util 0.1",
        tags=["telemetry"],
        namespace="default",
    )
    store.add(
        "note",
        "Fly tying notes: use CDC feathers for dry flies.",
        tags=["layer:long_term"],
        namespace="default",
    )

    class Ctx:
        memory = store
        session = SessionContext()
        conversation = SimpleNamespace(messages=[])

        def refresh_system_prompt(self):
            pass

    return Ctx()


def test_normalize_strips_question_wrapper():
    assert normalize_memory_query("What is my favorite coffee?") == "favorite coffee"
    assert normalize_memory_query("Search memory for fly tying") == "fly tying"


def test_filter_hides_strategies_and_telemetry(mem_ctx):
    visible = filter_user_facing(mem_ctx.memory.list_entries())
    texts = " ".join(e["content"] for e in visible).lower()
    assert "coffee" in texts
    assert "tool `" not in texts
    assert "telemetry" not in texts
    assert "prefer bullets" not in texts


def test_recall_coffee_answers_not_dump(mem_ctx):
    result = MemoryEngine.memory_search(
        mem_ctx,
        {"query": "What is my favorite coffee?"},
        "What is my favorite coffee?",
    )
    assert result["ok"]
    msg = result["message"]
    assert "medium roast" in msg.lower()
    assert "Found these memories" not in msg
    assert "favorite color" not in msg.lower()
    assert "tool `" not in msg.lower()
    assert "Telemetry" not in msg


def test_search_fly_tying_hides_strategies(mem_ctx):
    result = MemoryEngine.memory_search(
        mem_ctx,
        {"query": "fly tying"},
        "Search memory for fly tying.",
    )
    assert result["ok"]
    msg = result["message"]
    assert "CDC" in msg or "fly tying" in msg.lower()
    assert "tool `" not in msg.lower()
    assert "Telemetry" not in msg


def test_forget_coffee_keeps_unrelated(mem_ctx):
    result = MemoryEngine.memory_forget(
        mem_ctx,
        {"query": "my coffee preference"},
        "Forget my coffee preference.",
    )
    assert result["ok"]
    assert "coffee" in result["message"].lower()
    remaining = [e for e in mem_ctx.memory.list_entries()]
    contents = [e["content"].lower() for e in remaining]
    assert not any("favorite coffee" in c for c in contents)
    assert any("favorite color is blue" in c for c in contents)
    assert any("zeus" in c for c in contents)


def test_forget_targets_precise():
    entries = [
        {
            "id": "1",
            "type": "preference",
            "content": "My favorite coffee is medium roast.",
            "tags": [],
        },
        {"id": "2", "type": "fact", "content": "My favorite color is blue.", "tags": []},
        {"id": "3", "type": "strategy", "content": "Tool coffee", "tags": ["tool-outcome"]},
    ]
    targets = select_forget_targets(entries, "coffee preference")
    assert len(targets) == 1
    assert targets[0]["id"] == "1"


def test_format_recall_answer_second_person():
    assert (
        format_recall_answer({"content": "My favorite coffee is medium roast."})
        == "Your favorite coffee is medium roast."
    )


def test_update_then_recall(mem_ctx):
    MemoryEngine.memory_correct(
        mem_ctx,
        {"new_fact": "My favorite coffee is dark roast.", "search_hint": "favorite coffee"},
        "Update my favorite coffee to dark roast.",
    )
    result = MemoryEngine.memory_search(
        mem_ctx,
        {"query": "What is my favorite coffee?"},
        "What is my favorite coffee?",
    )
    assert "dark roast" in result["message"].lower()
    remaining = [
        e["content"]
        for e in mem_ctx.memory.list_entries()
        if "coffee" in e["content"].lower() and "superseded" not in (e.get("tags") or [])
    ]
    assert any("dark roast" in c.lower() for c in remaining)
    assert not any("medium roast" in c.lower() for c in remaining)
    # Unrelated preference still present
    assert any("color is blue" in e["content"] for e in mem_ctx.memory.list_entries())
