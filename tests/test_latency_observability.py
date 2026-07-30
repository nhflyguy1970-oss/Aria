"""Latency observability — traces, budgets, search, exports."""

from __future__ import annotations

import json

from jarvis.latency_observability.budgets import evaluate_budgets
from jarvis.latency_observability.store import append_trace, search_traces
from jarvis.latency_observability.trace import (
    LatencyTrace,
    begin_trace,
    complete_trace,
    get_trace,
    live_traces,
)


def test_begin_complete_trace_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))  # avoid polluting real data if paths use HOME
    from jarvis import config

    monkeypatch.setattr(config, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(
        "jarvis.latency_observability.store.HISTORY_FILE",
        tmp_path / "data" / "latency_observability" / "traces.jsonl",
    )
    monkeypatch.setattr(
        "jarvis.provider_health.history.HISTORY_FILE",
        tmp_path / "data" / "provider_health" / "history.jsonl",
    )

    tr = begin_trace(request_id="req-1", prompt="Hello", conversation_id="main")
    assert tr.trace_id.startswith("lt-")
    tr.note_stage("routing", 2.5)
    tr.note_stage("context_assembly", 4.0)
    tr.set_context_inventory(
        {
            "lightweight": True,
            "prefix_characters": 100,
            "sources": {
                "memory": {"elapsed_ms": 0, "characters": 0, "required": False, "injected": False},
                "language": {"elapsed_ms": 1, "characters": 100, "required": True, "injected": True},
            },
        }
    )
    tr.note_stream(first_token_ms=510)
    tr.note_provider(provider="ollama", model="qwen2.5:7b")
    done = complete_trace(ok=True, action="chat")
    assert done is not None
    assert done.completed is True
    assert get_trace(tr.trace_id) is not None
    assert any(s["name"] == "routing" for s in done.to_dict()["stages"])
    assert done.context["sources"]["language"]["tokens_est"] == 25
    assert done.developer_overlay()
    assert done.waterfall()


def test_budgets_warn_only():
    tr = LatencyTrace(trace_id="lt-test")
    tr.note_stage("routing", 50)  # over 20ms
    tr.note_stream(first_token_ms=3000)  # over 2000ms
    warns = evaluate_budgets(tr)
    names = {w["budget"] for w in warns}
    assert "routing" in names
    assert "first_token" in names
    assert all(w["severity"] == "warn" for w in warns)


def test_search_and_export(tmp_path, monkeypatch):
    from jarvis import config
    from jarvis.latency_observability.export import export_csv, export_json, export_waterfall

    monkeypatch.setattr(config, "DATA_DIR", tmp_path / "data")
    hist = tmp_path / "data" / "latency_observability" / "traces.jsonl"
    monkeypatch.setattr("jarvis.latency_observability.store.HISTORY_FILE", hist)
    monkeypatch.setattr(
        "jarvis.provider_health.history.HISTORY_FILE",
        tmp_path / "data" / "provider_health" / "history.jsonl",
    )

    tr = begin_trace(request_id="r2", prompt="weather")
    tr.note_stage("routing", 1)
    tr.note_provider(provider="ollama", model="qwen2.5:7b")
    tr.note_stream(first_token_ms=12)
    complete_trace(ok=True, action="weather_forecast")

    hits = search_traces(tr.trace_id, limit=5)
    assert hits and hits[0]["trace_id"] == tr.trace_id
    assert export_json(tr.trace_id)["ok"] is True
    assert "routing" in export_csv(tr.trace_id)
    assert export_waterfall(tr.trace_id)["ok"] is True


def test_retrieve_latency_corpus(tmp_path, monkeypatch):
    from jarvis import config
    from jarvis.search_product.retrievers import retrieve_latency

    monkeypatch.setattr(config, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(
        "jarvis.latency_observability.store.HISTORY_FILE",
        tmp_path / "data" / "latency_observability" / "traces.jsonl",
    )
    monkeypatch.setattr(
        "jarvis.provider_health.history.HISTORY_FILE",
        tmp_path / "data" / "provider_health" / "history.jsonl",
    )
    tr = begin_trace(request_id="r3", prompt="Explain")
    tr.note_stream(first_token_ms=100)
    complete_trace(ok=True, action="chat")
    results = retrieve_latency(tr.trace_id, 5)
    assert results
    assert results[0]["source"] == "latency"


def test_mission_panel_shape():
    from jarvis.latency_observability.mission_bridge import mission_panel

    panel = mission_panel()
    assert panel["product"] == "Latency"
    assert "first_token" in panel
    assert "live" in panel
