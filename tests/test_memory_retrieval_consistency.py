"""Regression: memory retrieval consistency — update/supersede, journal demotion, summaries."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from jarvis.behaviors.conversation import _sanitize_user_error
from jarvis.behaviors.memory.engine import MemoryEngine
from jarvis.memory.retrieval_diagnostics import rank_for_query
from jarvis.modules.memory import create_memory_store
from jarvis.session import SessionContext
from jarvis.trust_memory import correct_memory


@pytest.fixture()
def mem_ctx(tmp_path: Path):
    store = create_memory_store(tmp_path / "mem.json")
    store.add(
        "preference",
        "My favorite coffee is dark roast.",
        tags=["layer:long_term"],
        namespace="default",
    )
    store.add(
        "fact",
        "My favorite color is black.",
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
        "preference",
        "I prefer concise documentation with examples.",
        tags=["layer:long_term"],
        namespace="default",
    )
    store.add(
        "note",
        "From bullet journal (2026-07-10): fly tying workshop; coffee with Sam; check warranty on laptop.",
        tags=["journal"],
        namespace="default",
    )
    store.add(
        "note",
        "Fly tying tip: use CDC for dry flies.",
        tags=["layer:long_term"],
        namespace="default",
    )
    store.add(
        "fact",
        "Laptop warranty expires December 2027.",
        tags=["layer:long_term"],
        namespace="default",
    )
    store.add(
        "fact",
        "User profile interests: hiking, reading.",
        tags=["summary"],
        namespace="profile",
    )

    class Ctx:
        memory = store
        session = SessionContext()
        conversation = SimpleNamespace(messages=[])

        def refresh_system_prompt(self):
            pass

    return Ctx()


def test_update_coffee_supersedes_dark(mem_ctx):
    removed, entry, _ = correct_memory(
        mem_ctx.memory,
        "my favorite coffee is medium roast now",
        search_hint="",
    )
    assert removed >= 1
    assert "medium" in entry["content"].lower()
    result = MemoryEngine.memory_search(
        mem_ctx,
        {"query": "What is my favorite coffee?"},
        "What is my favorite coffee?",
    )
    assert "medium roast" in result["message"].lower()
    assert "dark roast" not in result["message"].lower()


def test_recall_color_not_journal(mem_ctx):
    result = MemoryEngine.memory_search(
        mem_ctx,
        {"query": "What is my favorite color?"},
        "What is my favorite color?",
    )
    assert "black" in result["message"].lower()
    assert "bullet journal" not in result["message"].lower()


def test_preference_summary_includes_learned(mem_ctx):
    result = MemoryEngine.memory_about_user(
        mem_ctx,
        {"question": "What preferences do you know about me?"},
        "What preferences do you know about me?",
    )
    assert "concise documentation" in result["message"].lower()
    assert "coffee" in result["message"].lower()


def test_user_summary_evolves_beyond_onboarding(mem_ctx):
    result = MemoryEngine.memory_about_user(
        mem_ctx,
        {"question": "What do you know about me?"},
        "What do you know about me?",
    )
    msg = result["message"].lower()
    assert "hiking" in msg or "reading" in msg
    assert "concise" in msg or "coffee" in msg or "zeus" in msg


def test_search_queries_are_distinct(mem_ctx):
    coffee = MemoryEngine.memory_search(mem_ctx, {"query": "coffee"}, "Search memory for coffee")
    flies = MemoryEngine.memory_search(mem_ctx, {"query": "fly tying"}, "Search memory for fly tying")
    warranty = MemoryEngine.memory_search(mem_ctx, {"query": "warranty"}, "Search memory for warranty")
    assert "coffee" in coffee["message"].lower()
    assert "fly tying" in flies["message"].lower() or "cdc" in flies["message"].lower()
    assert "warranty" in warranty["message"].lower()
    # Dedicated facts should beat the identical journal megablob as sole/identical result.
    assert coffee["message"] != flies["message"]
    assert flies["message"] != warranty["message"]


def test_zeus_fact_answer(mem_ctx):
    result = MemoryEngine.memory_search(
        mem_ctx,
        {"query": "What do you know about Zeus?"},
        "What do you know about Zeus?",
    )
    assert "zeus" in result["message"].lower()
    assert "Found these memories" not in result["message"]


def test_forget_coffee_keeps_color(mem_ctx):
    MemoryEngine.memory_forget(mem_ctx, {"query": "coffee preference"}, "Forget my coffee preference")
    # Active coffee preference gone (superseded or deleted); color remains.
    active = [
        e
        for e in mem_ctx.memory.list_entries()
        if "superseded" not in (e.get("tags") or [])
        and "coffee" in e["content"].lower()
        and e.get("type") in ("fact", "preference")
    ]
    assert not active
    assert any("color is black" in e["content"].lower() for e in mem_ctx.memory.list_entries())


def test_ranking_diagnostics_recorded(mem_ctx):
    hits, decision = rank_for_query(
        mem_ctx.memory.list_entries(),
        "What is my favorite coffee?",
        intent="memory_search",
        fact_mode=True,
    )
    assert hits
    assert decision["selected_id"]
    assert "keyword_score" in (decision.get("selected_scores") or {})
    assert decision["candidate_count"] >= 1


def test_backend_empty_sanitized():
    msg = _sanitize_user_error("Model `qwen2.5:7b` returned empty. Try: ollama pull qwen2.5:7b")
    assert "qwen" not in msg.lower()
    assert "ollama" not in msg.lower()
    assert "try again" in msg.lower()
