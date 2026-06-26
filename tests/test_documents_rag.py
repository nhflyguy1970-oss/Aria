"""Tests for documents_rag indexing and search."""

import json

import pytest

from jarvis.documents_rag import (
    INDEX_FILE,
    _keyword_search,
    build_index,
    index_needs_rebuild,
    search,
)


@pytest.fixture
def docs_env(data_dir, monkeypatch):
    doc_dir = data_dir / "documents"
    doc_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("jarvis.documents_rag.DOCUMENTS_DIR", doc_dir)
    monkeypatch.setattr("jarvis.documents_rag.INDEX_FILE", data_dir / "documents_index.json")
    monkeypatch.setattr("jarvis.documents_rag.DATA_DIR", data_dir)
    monkeypatch.setattr("jarvis.document_pipeline.DOCUMENTS_DIR", doc_dir)
    return doc_dir


def test_keyword_search_without_embed(docs_env, monkeypatch):
    monkeypatch.setattr("jarvis.documents_rag.llm.embed_available", lambda: False)
    chunks = [
        {"source": "warranty.pdf", "title": "Warranty", "text": "Coverage includes battery replacement for five years."},
        {"source": "manual.pdf", "title": "Manual", "text": "Press the power button to start the device."},
    ]
    hits = search("warranty battery", limit=3)
    # search loads empty index — test helper directly
    hits = _keyword_search("warranty battery", chunks, 3)
    assert hits
    assert "warranty" in hits[0]["source"].lower() or "Warranty" in hits[0]["title"]


def test_corrupt_index_rebuilds(docs_env, monkeypatch):
    monkeypatch.setattr("jarvis.documents_rag.llm.embed_available", lambda: False)
    monkeypatch.setattr("jarvis.documents_rag.llm.embed_text", lambda t: [])
    from jarvis import documents_rag

    documents_rag.INDEX_FILE.write_text("{not valid json", encoding="utf-8")
    (docs_env / "note.pdf").write_bytes(b"%PDF-1.4\n")
    monkeypatch.setattr(
        "jarvis.documents_rag.parse_document",
        lambda p: type("D", (), {"full_text": "Invoice total due April", "title": "Invoice", "page_count": 1})(),
    )
    chunks = build_index(force=True)
    assert isinstance(chunks, list)
    assert documents_rag.INDEX_FILE.is_file()
    data = json.loads(documents_rag.INDEX_FILE.read_text(encoding="utf-8"))
    assert isinstance(data, list)


def test_index_needs_rebuild_when_doc_newer(docs_env, monkeypatch):
    from jarvis import documents_rag

    monkeypatch.setattr("jarvis.documents_rag.llm.embed_available", lambda: False)
    documents_rag.INDEX_FILE.write_text("[]", encoding="utf-8")
    path = docs_env / "fresh.pdf"
    path.write_bytes(b"x")
    assert index_needs_rebuild() is True


def test_build_index_writes_file(docs_env, monkeypatch):
    from jarvis import documents_rag

    monkeypatch.setattr("jarvis.documents_rag.llm.embed_available", lambda: False)
    monkeypatch.setattr("jarvis.documents_rag.llm.embed_text", lambda t: [])
    (docs_env / "a.pdf").write_bytes(b"x")
    monkeypatch.setattr(
        "jarvis.documents_rag.parse_document",
        lambda p: type("D", (), {"full_text": "Hello document world", "title": "Hello", "page_count": 1})(),
    )
    chunks = build_index(force=True)
    assert len(chunks) >= 1
    assert documents_rag.INDEX_FILE.is_file()
