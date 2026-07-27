"""Document learning tests."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from jarvis.document_learning import (
    DOCUMENT_LEARN_TAG,
    LEARNING_NAMESPACE,
    extract_document_learnings,
    ingest_file,
    ingest_text,
    is_learn_from_document,
    learn_from_text,
    list_document_learnings,
    parse_url_from_message,
)
from jarvis.document_pipeline import html_to_text, parse_text_content
from jarvis.modules.memory import MemoryStore


@pytest.fixture
def store(data_dir, monkeypatch):
    monkeypatch.delenv("JARVIS_GRAPH_BACKEND", raising=False)
    monkeypatch.delenv("JARVIS_VECTOR_BACKEND", raising=False)
    monkeypatch.setattr("jarvis.llm.embed_available", lambda: False)
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [0.1, 0.2] if t else [])
    return MemoryStore(path=data_dir / "memory.json")


def test_html_to_text():
    html = "<html><head><title>Guide</title></head><body><p>Hello <b>world</b></p></body></html>"
    text = html_to_text(html)
    assert "Hello" in text and "world" in text


def test_parse_text_content():
    doc = parse_text_content("Line one.\nLine two.", title="Test doc", source="ocr")
    assert doc.char_count > 0
    assert doc.title == "Test doc"
    assert "Line one" in doc.full_text


def test_is_learn_from_document():
    assert is_learn_from_document("learn from this PDF please")
    assert is_learn_from_document("study the attached warranty doc")
    assert not is_learn_from_document("learn about Python")


def test_parse_url():
    assert parse_url_from_message("learn from https://example.com/guide.html") == "https://example.com/guide.html"


def test_ingest_text_and_file(data_dir, monkeypatch, tmp_path):
    monkeypatch.setattr("jarvis.document_learning.DOCUMENTS_DIR", data_dir / "documents")
    monkeypatch.setattr("jarvis.document_pipeline.DOCUMENTS_DIR", data_dir / "documents")
    monkeypatch.setattr("jarvis.document_pipeline.CACHE_DIR", data_dir / "documents" / ".cache")
    monkeypatch.setattr("jarvis.documents_rag.DOCUMENTS_DIR", data_dir / "documents")
    monkeypatch.setattr("jarvis.documents_rag.INDEX_FILE", data_dir / "documents_index.json")
    monkeypatch.setattr("jarvis.document_learning.REGISTRY_FILE", data_dir / "document_learning.json")
    monkeypatch.setattr("jarvis.llm.embed_available", lambda: False)
    from jarvis import documents_rag

    monkeypatch.setattr(documents_rag.llm, "embed_available", lambda: False)
    monkeypatch.setattr(
        "jarvis.documents_rag.build_index",
        lambda *, force=False: documents_rag._build_index_impl(force=force),
    )

    result = ingest_text("Important warranty covers labor for 12 months.", title="warranty-notes")
    assert result.ok
    assert Path(result.path).is_file()

    # Must live under document library roots for path confinement
    src = data_dir / "documents" / "manual.txt"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("Chapter 1: Setup instructions.", encoding="utf-8")
    ing = ingest_file(src)
    assert ing.ok


def test_extract_and_learn(monkeypatch, store, data_dir):
    monkeypatch.setattr("jarvis.document_learning.DOCUMENTS_DIR", data_dir / "documents")
    monkeypatch.setattr("jarvis.document_pipeline.DOCUMENTS_DIR", data_dir / "documents")
    monkeypatch.setattr("jarvis.document_pipeline.CACHE_DIR", data_dir / "documents" / ".cache")
    monkeypatch.setattr("jarvis.documents_rag.DOCUMENTS_DIR", data_dir / "documents")
    monkeypatch.setattr("jarvis.documents_rag.INDEX_FILE", data_dir / "documents_index.json")
    monkeypatch.setattr("jarvis.document_learning.REGISTRY_FILE", data_dir / "document_learning.json")
    monkeypatch.setattr("jarvis.memory_services.CANDIDATES_FILE", data_dir / "memory_candidates.json")
    from jarvis import documents_rag

    monkeypatch.setattr(
        "jarvis.documents_rag.build_index",
        lambda *, force=False: documents_rag._build_index_impl(force=force),
    )
    facts_json = '{"facts": ["The warranty covers parts for twelve months.", "Claims must be filed within 30 days."]}'
    monkeypatch.setattr("jarvis.llm.ask", lambda *a, **k: facts_json)
    monkeypatch.setattr("jarvis.document_learning.llm.ask", lambda *a, **k: facts_json)
    monkeypatch.setattr("jarvis.document_learning.llm.general_model", lambda: "test-model")
    monkeypatch.setattr(documents_rag.llm, "embed_available", lambda: False)
    monkeypatch.setattr(documents_rag.llm, "general_model", lambda: "test-model")

    facts = extract_document_learnings("Warranty text here.", title="Warranty")
    assert len(facts) == 2

    result = learn_from_text(
        store,
        "The server runs on port 8765. Backups run nightly at 2am.",
        title="ops-runbook",
    )
    assert result.ok
    assert len(result.lessons) >= 1
    assert "candidate" in result.message.lower()
    entries = list_document_learnings(store)
    assert entries == []

    from jarvis.document_pipeline import parse_text_content
    from jarvis.document_learning import learn_from_document
    from jarvis.explicit_teaching import TeachIntent

    def fake_teach(memory, intent, namespace="default", extra_tags=None):
        memory.add(
            "teaching",
            intent.content,
            tags=list(extra_tags or []),
            namespace=namespace,
        )
        return SimpleNamespace(content=intent.content)

    monkeypatch.setattr("jarvis.explicit_teaching.apply_explicit_teaching", fake_teach)
    monkeypatch.setattr("jarvis.trust_memory.is_trusted_memory_content", lambda c: True)

    doc = parse_text_content(
        "The server runs on port 8765. Backups run nightly at 2am.",
        title="ops-runbook-encoded",
        source="text",
    )
    encoded = learn_from_document(store, doc, source_type="text", encode=True)
    assert encoded.ok
    entries = list_document_learnings(store)
    assert entries
    assert entries[0]["namespace"] == LEARNING_NAMESPACE
    assert DOCUMENT_LEARN_TAG in entries[0]["tags"]
