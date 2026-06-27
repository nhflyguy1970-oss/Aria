"""Correction learning tests."""

import pytest

from jarvis.correction_learning import (
    CORRECTION_NAMESPACE,
    CORRECTION_TAG,
    apply_correction,
    correction_context_for_chat,
    corrections_system_block,
    is_correction_message,
    parse_correction,
    CorrectionIntent,
)
from jarvis.modules.memory import MemoryStore


@pytest.fixture
def store(data_dir, monkeypatch):
    monkeypatch.delenv("JARVIS_GRAPH_BACKEND", raising=False)
    monkeypatch.delenv("JARVIS_VECTOR_BACKEND", raising=False)
    monkeypatch.setattr("jarvis.llm.embed_available", lambda: False)
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [0.1, 0.2] if t else [])
    monkeypatch.setattr("jarvis.correction_learning.REGISTRY_FILE", data_dir / "correction_learning.json")
    return MemoryStore(path=data_dir / "memory.json")


def test_parse_correction_variants():
    p = parse_correction("correct that mom's birthday is June 9")
    assert p and "June 9" in p.correction
    p = parse_correction("No, that's wrong — the port is 8765")
    assert p and "8765" in p.correction
    assert is_correction_message("you're wrong about the path")


def test_apply_correction_fact(store):
    result = apply_correction(
        store,
        CorrectionIntent(correction="Mom's birthday is June 9", wrong_hint="birthday", kind="fact"),
        assistant_msg="Her birthday is in July.",
    )
    assert result.ok
    assert result.wrong_claim
    entries = store.list_entries(namespace=CORRECTION_NAMESPACE)
    assert any(CORRECTION_TAG in (e.get("tags") or []) for e in entries)


def test_apply_correction_behavior(store):
    result = apply_correction(
        store,
        CorrectionIntent(correction="Never suggest cloud APIs", kind="behavior"),
        assistant_msg="You could use OpenAI API for that.",
    )
    assert result.ok
    assert store.list_entries(entry_type="strategy")


def test_correction_context(store):
    apply_correction(
        store,
        CorrectionIntent(correction="Jarvis listens on port 8765", kind="fact"),
        assistant_msg="The server is on port 8080.",
    )
    block = corrections_system_block(store)
    assert "8765" in block or "Correction" in block
    ctx = correction_context_for_chat(store, "what port does jarvis use")
    assert "8765" in ctx or not ctx
