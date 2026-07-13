"""Phase 1 — Learning Governor passthrough parity."""

from __future__ import annotations

import json


def test_governor_defaults_enabled(monkeypatch):
    monkeypatch.delenv("ARIA_LEARNING_GOVERNOR", raising=False)
    from importlib import reload

    import jarvis.learning_governor as lg

    reload(lg)
    assert lg.enabled() is True


def test_governor_passthrough_returns_apply_result(monkeypatch):
    monkeypatch.delenv("ARIA_LEARNING_GOVERNOR", raising=False)
    from importlib import reload

    import jarvis.learning_governor as lg

    reload(lg)
    calls = []

    def apply():
        calls.append(1)
        return {"wrote": True, "value": 42}

    out = lg.commit(lg.propose(kind="unit", payload={"a": 1}, source="test"), apply)
    assert out == {"wrote": True, "value": 42}
    assert calls == [1]


def test_governor_disabled_still_applies(monkeypatch):
    monkeypatch.setenv("ARIA_LEARNING_GOVERNOR", "0")
    from importlib import reload

    import jarvis.learning_governor as lg

    reload(lg)
    assert lg.enabled() is False
    assert lg.commit(lg.propose(kind="x"), lambda: "ok") == "ok"


def test_record_correction_via_governor(tmp_path, monkeypatch):
    monkeypatch.delenv("ARIA_LEARNING_GOVERNOR", raising=False)
    import jarvis.nlu.learning as learning

    monkeypatch.setattr(learning, "_CORRECTIONS", tmp_path / "nlu_corrections.jsonl")
    item = learning.record_correction(
        prompt="turn on the lamp",
        original_intent="chat",
        corrected_intent="lights_on",
    )
    assert item["corrected_intent"] == "lights_on"
    lines = learning._CORRECTIONS.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["corrected_intent"] == "lights_on"


def test_memory_add_via_governor(tmp_path, monkeypatch):
    monkeypatch.delenv("ARIA_LEARNING_GOVERNOR", raising=False)
    monkeypatch.setenv("JARVIS_MEMORY_COMPACT", "1")
    from jarvis.modules.memory import MemoryStore

    store = MemoryStore(path=tmp_path / "memory.json")
    monkeypatch.setattr("jarvis.modules.memory.llm.embed_text", lambda _t: None)
    entry = store.add("fact", "Jeff prefers barbless hooks for trout")
    assert "barbless" in entry["content"]
    assert any(e["id"] == entry["id"] for e in store.list_entries())
