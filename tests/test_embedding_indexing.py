"""Embedding lifecycle and incremental document indexing.

Two problems these tests pin down.

Cost: every embedding call passed keep_alive=0, so each one paid a cold model
load -- measured at 20.49 s per text against 3.4 ms inside a resident session.
A ~1,000-chunk document corpus was therefore a ~5.7 hour rebuild, which meant
in practice the index was never rebuilt and withdrawn documents kept being
served. keep_alive=0 is still right for a one-off call (OLLAMA_MAX_LOADED_
MODELS=1 means a resident embed runner evicts the chat model), so only a bulk
session opts into residency, and it hands the slot back on exit.

Truthfulness: a failed embedding used to become `embedding: []` on a stored
chunk -- an index entry that looks indexed and can never match anything. A
failure must stay a failure.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


# --------------------------------------------------------------------------
# embedding lifecycle
# --------------------------------------------------------------------------

def test_a_one_off_embed_does_not_hold_the_model(monkeypatch):
    """Chat owns the single runner slot; a stray embed must not squat on it."""
    from jarvis import llm

    seen = {}

    def fake_embed(*, model, input, keep_alive):
        seen["keep_alive"] = keep_alive
        return {"embeddings": [[0.1, 0.2]]}

    monkeypatch.setattr(llm, "_embed_client", lambda: type("C", (), {"embed": staticmethod(fake_embed)})())
    llm.embed_batch(["one text"])
    assert seen["keep_alive"] == 0


def test_a_session_keeps_the_model_resident(monkeypatch):
    from jarvis import llm

    seen = []

    def fake_embed(*, model, input, keep_alive):
        seen.append(keep_alive)
        return {"embeddings": [[0.1]] * len(input)}

    monkeypatch.setattr(llm, "_embed_client", lambda: type("C", (), {"embed": staticmethod(fake_embed)})())
    monkeypatch.setattr("jarvis.ollama_runtime.unload_model", lambda *a, **k: True)
    with llm.embed_session(keep_alive="5m"):
        llm.embed_batch(["a"])
        llm.embed_batch(["b"])
    llm.embed_batch(["c"])
    assert seen == ["5m", "5m", 0], "residency leaked past the session"


def test_a_session_returns_the_slot_on_exit(monkeypatch):
    """Leaving the embed model loaded would cost chat a cold reload."""
    from jarvis import llm

    unloaded = []
    monkeypatch.setattr(
        llm, "_embed_client",
        lambda: type("C", (), {"embed": staticmethod(
            lambda **kw: {"embeddings": [[0.1]]})})(),
    )
    monkeypatch.setattr("jarvis.ollama_runtime.unload_model",
                        lambda model, **k: unloaded.append(model) or True)
    with llm.embed_session():
        llm.embed_batch(["a"])
    assert unloaded, "the embedding model was never unloaded"


def test_a_session_returns_the_slot_even_when_the_body_raises(monkeypatch):
    from jarvis import llm

    unloaded = []
    monkeypatch.setattr(
        llm, "_embed_client",
        lambda: type("C", (), {"embed": staticmethod(
            lambda **kw: {"embeddings": [[0.1]]})})(),
    )
    monkeypatch.setattr("jarvis.ollama_runtime.unload_model",
                        lambda model, **k: unloaded.append(model) or True)
    with pytest.raises(ValueError):
        with llm.embed_session():
            llm.embed_batch(["a"])
            raise ValueError("boom")
    assert unloaded, "a failure inside the session leaked model residency"


def test_a_session_that_embeds_nothing_does_not_unload(monkeypatch):
    """search_pool opens a session per memory search and usually finds every
    embedding cached. Unloading anyway would cost a blocking round trip on
    each chat turn and could evict a model another process is mid-batch on."""
    from jarvis import llm

    unloaded = []
    monkeypatch.setattr("jarvis.ollama_runtime.unload_model",
                        lambda model, **k: unloaded.append(model) or True)
    with llm.embed_session():
        pass
    assert not unloaded, "unloaded a slot the session never took"


def test_nested_sessions_release_once(monkeypatch):
    from jarvis import llm

    unloaded = []
    monkeypatch.setattr(
        llm, "_embed_client",
        lambda: type("C", (), {"embed": staticmethod(
            lambda **kw: {"embeddings": [[0.1]]})})(),
    )
    monkeypatch.setattr("jarvis.ollama_runtime.unload_model",
                        lambda model, **k: unloaded.append(model) or True)
    with llm.embed_session():
        with llm.embed_session():
            llm.embed_batch(["a"])
        assert not unloaded, "the inner session released the outer one's model"
    assert len(unloaded) == 1


def test_every_embedding_call_is_bounded(monkeypatch):
    """There was no timeout at all: a stalled runner blocked forever."""
    from jarvis import llm

    captured = {}

    class _Client:
        def __init__(self, timeout):
            captured["timeout"] = timeout

        def embed(self, **kw):
            return {"embeddings": [[0.1]]}

    monkeypatch.setattr("ollama.Client", _Client)
    llm.embed_batch(["x"])
    assert captured["timeout"] == llm.embed_timeout()
    assert captured["timeout"] > 0


def test_the_timeout_is_configurable_and_has_a_floor(monkeypatch):
    from jarvis import llm

    monkeypatch.setenv("JARVIS_EMBED_TIMEOUT", "12")
    assert llm.embed_timeout() == 12.0
    monkeypatch.setenv("JARVIS_EMBED_TIMEOUT", "0.1")
    assert llm.embed_timeout() >= 5.0, "a floor keeps a cold load from timing out"
    monkeypatch.setenv("JARVIS_EMBED_TIMEOUT", "not-a-number")
    assert llm.embed_timeout() == 90.0


def test_a_failed_batch_raises_rather_than_returning_empty(monkeypatch):
    """Returning [] is how a failure became a valid-looking index entry."""
    from jarvis import llm

    def boom(**kw):
        raise TimeoutError("runner stalled")

    monkeypatch.setattr(
        llm, "_embed_client",
        lambda: type("C", (), {"embed": staticmethod(boom)})())
    with pytest.raises(llm.EmbeddingError) as exc:
        llm.embed_batch(["x"])
    assert "TimeoutError" in str(exc.value)


def test_a_short_batch_response_is_a_failure(monkeypatch):
    """Silently zipping mismatched lists would misalign every later vector."""
    from jarvis import llm

    monkeypatch.setattr(
        llm, "_embed_client",
        lambda: type("C", (), {"embed": staticmethod(
            lambda **kw: {"embeddings": [[0.1]]})})())
    with pytest.raises(llm.EmbeddingError):
        llm.embed_batch(["a", "b", "c"])


def test_embed_text_still_degrades_quietly(monkeypatch):
    """Retrieval callers want "no vector", not an exception."""
    from jarvis import llm

    monkeypatch.setattr(
        llm, "_embed_client",
        lambda: type("C", (), {"embed": staticmethod(
            lambda **kw: (_ for _ in ()).throw(OSError("down")))})())
    assert llm.embed_text("x") == []


# --------------------------------------------------------------------------
# incremental document indexing
# --------------------------------------------------------------------------

@pytest.fixture
def corpus(tmp_path, monkeypatch):
    from jarvis import documents_rag as dr

    docs = tmp_path / "documents"
    docs.mkdir()
    index_file = tmp_path / "documents_index.json"
    monkeypatch.setattr(dr, "DOCUMENTS_DIR", docs)
    monkeypatch.setattr(dr, "INDEX_FILE", index_file)
    monkeypatch.setattr(dr, "_INDEX_MEM", {"mtime": None, "chunks": None})
    monkeypatch.setattr(dr.llm, "embed_available", lambda: True)
    monkeypatch.setattr("jarvis.live_data_guard.assert_live_write_allowed",
                        lambda p: None)

    calls: list[list[str]] = []

    def fake_batch(texts):
        calls.append(list(texts))
        return [[float(len(t)), 0.5] for t in texts]

    monkeypatch.setattr(dr.llm, "embed_batch", fake_batch)

    class _NullSession:
        def __enter__(self): return None
        def __exit__(self, *a): return False

    monkeypatch.setattr(dr.llm, "embed_session", lambda **kw: _NullSession())
    return {"docs": docs, "index": index_file, "calls": calls, "dr": dr}


def _embedded_texts(calls):
    return [t for batch in calls for t in batch]


def test_a_new_document_is_embedded_once(corpus):
    dr = corpus["dr"]
    (corpus["docs"] / "a.md").write_text("# A\nAdams dry fly pattern.\n", encoding="utf-8")
    chunks = dr._build_index_impl(force=True)
    assert len(chunks) == 1
    assert chunks[0]["embedding"]
    assert len(_embedded_texts(corpus["calls"])) == 1


def test_an_unchanged_corpus_embeds_nothing(corpus):
    """The whole point: a rebuild must not re-pay for work already done."""
    dr = corpus["dr"]
    (corpus["docs"] / "a.md").write_text("# A\nAdams dry fly.\n", encoding="utf-8")
    (corpus["docs"] / "b.md").write_text("# B\nElk hair caddis.\n", encoding="utf-8")
    dr._build_index_impl(force=True)
    corpus["calls"].clear()
    chunks = dr._build_index_impl(force=True)
    assert len(chunks) == 2
    assert corpus["calls"] == [], "unchanged documents were re-embedded"


def test_only_the_changed_document_is_re_embedded(corpus):
    dr = corpus["dr"]
    (corpus["docs"] / "a.md").write_text("# A\nAdams dry fly.\n", encoding="utf-8")
    (corpus["docs"] / "b.md").write_text("# B\nElk hair caddis.\n", encoding="utf-8")
    dr._build_index_impl(force=True)
    corpus["calls"].clear()
    (corpus["docs"] / "b.md").write_text("# B\nElk hair caddis, tan, size 14.\n",
                                         encoding="utf-8")
    chunks = dr._build_index_impl(force=True)
    embedded = _embedded_texts(corpus["calls"])
    assert len(embedded) == 1
    assert "size 14" in embedded[0]
    assert len(chunks) == 2


def test_a_deleted_document_leaves_the_index(corpus):
    """A withdrawn document has to stop being retrievable."""
    dr = corpus["dr"]
    (corpus["docs"] / "keep.md").write_text("# Keep\nReal pattern.\n", encoding="utf-8")
    (corpus["docs"] / "drop.md").write_text("# Drop\nFabricated pattern.\n", encoding="utf-8")
    dr._build_index_impl(force=True)
    (corpus["docs"] / "drop.md").unlink()
    corpus["calls"].clear()
    chunks = dr._build_index_impl(force=True)
    assert {c["source"] for c in chunks} == {"keep.md"}
    assert corpus["calls"] == [], "removing a document re-embedded the survivors"


def test_a_model_change_invalidates_the_vectors(corpus, monkeypatch):
    """Vectors from another model are not comparable and must not be reused."""
    dr = corpus["dr"]
    (corpus["docs"] / "a.md").write_text("# A\nAdams dry fly.\n", encoding="utf-8")
    dr._build_index_impl(force=True)
    corpus["calls"].clear()
    monkeypatch.setattr(dr, "model_for", lambda kind: "some-other-embed-model")
    chunks = dr._build_index_impl(force=True)
    assert len(_embedded_texts(corpus["calls"])) == 1
    assert chunks[0]["embed_model"] == "some-other-embed-model"


def test_a_failed_batch_is_never_claimed_as_embedded(corpus, monkeypatch):
    """A failure must not look like a vector, but must not lose the text.

    Semantic scoring skips chunks with no vector and the search falls back to
    keyword, so the text is still worth indexing -- what must never happen is
    the chunk claiming to carry an embedding it does not have.
    """
    dr = corpus["dr"]
    (corpus["docs"] / "a.md").write_text("# A\nAdams dry fly.\n", encoding="utf-8")

    def boom(texts):
        raise dr.llm.EmbeddingError("runner stalled")

    monkeypatch.setattr(dr.llm, "embed_batch", boom)
    chunks = dr._build_index_impl(force=True)
    assert len(chunks) == 1
    assert chunks[0]["embedding"] == []
    assert chunks[0]["embed_pending"] is True
    written = json.loads(corpus["index"].read_text(encoding="utf-8"))
    assert all(not c["embedding"] for c in written)


def test_a_failed_chunk_is_retried_on_the_next_build(corpus, monkeypatch):
    """`embed_pending` has to actually mean "try again", not "give up"."""
    dr = corpus["dr"]
    (corpus["docs"] / "a.md").write_text("# A\nAdams dry fly.\n", encoding="utf-8")
    monkeypatch.setattr(dr.llm, "embed_batch",
                        lambda t: (_ for _ in ()).throw(dr.llm.EmbeddingError("x")))
    dr._build_index_impl(force=True)

    real_calls: list[list[str]] = []

    def ok(texts):
        real_calls.append(list(texts))
        return [[1.0, 2.0] for _ in texts]

    monkeypatch.setattr(dr.llm, "embed_batch", ok)
    chunks = dr._build_index_impl(force=True)
    assert len(real_calls) == 1, "the failed chunk was not retried"
    assert chunks[0]["embedding"] == [1.0, 2.0]
    assert "embed_pending" not in chunks[0]


def test_an_offline_model_still_allows_keyword_retrieval(corpus, monkeypatch):
    """Losing semantic search must not also lose keyword search."""
    dr = corpus["dr"]
    (corpus["docs"] / "a.md").write_text(
        "# A\nReplace the air filter every ninety days.\n", encoding="utf-8")
    monkeypatch.setattr(dr.llm, "embed_available", lambda: False)
    chunks = dr._build_index_impl(force=True)
    assert len(chunks) == 1
    assert chunks[0]["embedding"] == []
    assert chunks[0]["embed_pending"] is True
    hits = dr._search_impl("air filter", limit=3)
    assert hits, "keyword retrieval was lost when embeddings were unavailable"


def test_an_interrupted_rebuild_resumes_without_redoing_work(corpus, monkeypatch):
    """A crash halfway must not throw away the vectors already paid for."""
    dr = corpus["dr"]
    for i in range(6):
        (corpus["docs"] / f"d{i}.md").write_text(
            f"# D{i}\nPattern number {i} with hook and thread.\n", encoding="utf-8")

    monkeypatch.setenv("JARVIS_EMBED_BATCH", "2")
    real = dr.llm.embed_batch
    state = {"n": 0}

    def fail_after_two(texts):
        state["n"] += 1
        if state["n"] > 2:
            raise KeyboardInterrupt("simulated crash")
        return real(texts)

    monkeypatch.setattr(dr.llm, "embed_batch", fail_after_two)
    with pytest.raises(KeyboardInterrupt):
        dr._build_index_impl(force=True)

    # The checkpoint written before the crash holds the completed vectors.
    partial = json.loads(corpus["index"].read_text(encoding="utf-8"))
    assert 0 < len(partial) < 6
    assert all(c["embedding"] for c in partial)

    corpus["calls"].clear()
    monkeypatch.setattr(dr.llm, "embed_batch", real)
    chunks = dr._build_index_impl(force=True)
    assert len(chunks) == 6
    redone = len(_embedded_texts(corpus["calls"]))
    assert redone == 6 - len(partial), (
        f"resume re-embedded {redone} chunks; only {6 - len(partial)} were outstanding")
