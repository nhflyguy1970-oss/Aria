"""Documents & RAG workspace identity / product surface tests."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def docs_env(tmp_path, monkeypatch):
    docs = tmp_path / "documents"
    docs.mkdir()
    monkeypatch.setattr("jarvis.document_pipeline.DOCUMENTS_DIR", docs)
    monkeypatch.setattr("jarvis.document_pipeline.CACHE_DIR", docs / ".cache")
    monkeypatch.setattr("jarvis.documents_rag.DOCUMENTS_DIR", docs)
    monkeypatch.setattr("jarvis.documents_rag.INDEX_FILE", tmp_path / "documents_index.json")
    monkeypatch.setattr("jarvis.document_services.DOCUMENTS_DIR", docs)
    monkeypatch.setattr("jarvis.document_services.DATA_DIR", tmp_path)
    monkeypatch.setattr("jarvis.document_services.IMPORTS_FILE", tmp_path / "document_imports.json")
    monkeypatch.setattr("jarvis.document_services.RECENT_SEARCHES_FILE", tmp_path / "document_recent_searches.json")
    monkeypatch.setattr("jarvis.document_services.INDEX_JOB_FILE", tmp_path / "document_index_job.json")
    monkeypatch.setattr("jarvis.memory_services.CANDIDATES_FILE", tmp_path / "memory_candidates.json")
    monkeypatch.setattr("jarvis.document_learning.DOCUMENTS_DIR", docs)
    monkeypatch.setattr("jarvis.document_learning.REGISTRY_FILE", tmp_path / "document_learning.json")
    monkeypatch.setattr("jarvis.llm.embed_available", lambda: False)
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [])
    monkeypatch.setenv("JARVIS_DISABLE_PLATFORM_KNOWLEDGE_RETRIEVAL", "1")

    from jarvis import documents_rag

    monkeypatch.setattr(documents_rag.llm, "embed_available", lambda: False)
    monkeypatch.setattr(documents_rag.llm, "embed_text", lambda t: [])
    monkeypatch.setattr(documents_rag.llm, "general_model", lambda: "test-model")
    monkeypatch.setattr(documents_rag.llm, "document_model", lambda: "test-model")
    monkeypatch.setattr(documents_rag.llm, "ask", lambda *a, **k: '{"facts": []}')
    monkeypatch.setattr(documents_rag.llm, "ask_with_system", lambda *a, **k: "ok")
    monkeypatch.setattr(
        "jarvis.documents_rag.build_index",
        lambda *, force=False: documents_rag._build_index_impl(force=force),
    )
    monkeypatch.setattr(
        "jarvis.documents_rag.search",
        lambda query, limit=5: documents_rag._search_impl(query, limit=limit),
    )
    return SimpleNamespace(docs=docs, tmp=tmp_path)


def test_index_health_and_rebuild(docs_env):
    from jarvis.document_services import index_health, rebuild_search_index, save_upload

    (docs_env.docs / "note.txt").write_text("Warranty covers parts for twelve months.", encoding="utf-8")
    health = index_health()
    assert health["ok"] is True
    assert "chunk_count" in health

    result = rebuild_search_index(force=True)
    assert result["ok"] is True
    assert result["chunks"] >= 1

    up = save_upload("manual.md", b"# Manual\n\nSetup instructions for the device.")
    assert up["ok"] is True
    assert Path(up["path"]).is_file()
    assert up["suggestion"]["suggested_type"]


def test_search_with_citations(docs_env):
    from jarvis.document_services import rebuild_search_index, search_library

    (docs_env.docs / "warranty.txt").write_text(
        "The furnace warranty covers heat exchanger failure for ten years.",
        encoding="utf-8",
    )
    rebuild_search_index(force=True)
    result = search_library("furnace warranty", limit=5)
    assert result["ok"]
    assert result["citations"]
    assert result["citations"][0]["id"].startswith("doc-")
    assert "Sources" in result["markdown"]


def test_learn_stages_candidates_only(docs_env, monkeypatch):
    from jarvis.document_services import stage_learn_candidates
    from jarvis.memory_services import list_candidates
    from jarvis.modules.memory import MemoryStore

    path = docs_env.docs / "runbook.txt"
    path.write_text("Backups run nightly at 2am. Port 8765 serves the API.", encoding="utf-8")
    monkeypatch.setattr(
        "jarvis.llm.ask",
        lambda *a, **k: '{"facts": ["Backups run nightly at 2am.", "API listens on port 8765."]}',
    )
    monkeypatch.setattr(
        "jarvis.document_learning.llm.ask",
        lambda *a, **k: '{"facts": ["Backups run nightly at 2am.", "API listens on port 8765."]}',
    )
    monkeypatch.setattr("jarvis.document_learning.llm.general_model", lambda: "test-model")
    store = MemoryStore(path=docs_env.tmp / "memory.json")
    monkeypatch.setattr("jarvis.assistant_instance.get_assistant", lambda: SimpleNamespace(memory=store))

    result = stage_learn_candidates(str(path))
    assert result["ok"]
    assert result["count"] >= 1
    assert "candidate" in result["message"].lower()
    cands = list_candidates(status="pending")["candidates"]
    assert any("document-learn" in (c.get("tags") or []) or c.get("source") == "document" for c in cands)


def test_documents_home_and_project_pack(docs_env, monkeypatch):
    from jarvis.document_services import documents_home, project_retrieval_pack

    monkeypatch.setattr("jarvis.active_project.get_active_slug", lambda: "")
    home = documents_home()
    assert home["ok"]
    assert "personal document" in (home.get("philosophy") or "").lower()
    assert home["health"]["ok"] is True
    assert any(a["id"] == "rebuild" for a in home["quick_actions"])

    pack = project_retrieval_pack("")
    assert pack["ok"]


def test_context_for_query_returns_citations(docs_env):
    from jarvis.documents_rag import build_index, context_for_query

    (docs_env.docs / "guide.txt").write_text("Replace the air filter every ninety days.", encoding="utf-8")
    build_index(force=True)
    ctx, warnings, citations = context_for_query("air filter")
    assert citations
    assert citations[0]["id"] == "doc-1"
    assert "[doc-1]" in ctx


def test_classify_smart_import():
    from jarvis.document_services import classify_document

    sug = classify_document("home-warranty.pdf", "This warranty covers labor and parts.")
    assert sug["suggested_type"] == "warranty"
    assert sug["stage_candidates"] is True


def test_format_hits_include_sources():
    from jarvis.documents_rag import format_hits_markdown

    md = format_hits_markdown(
        "test",
        [{"title": "A", "source": "a.txt", "text": "hello world excerpt for search"}],
    )
    assert "**Sources**" in md
    assert "[doc-1]" in md
