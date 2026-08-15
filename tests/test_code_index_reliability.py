"""Reliability regressions for code index request paths."""

from __future__ import annotations


def test_search_does_not_build_missing_index(tmp_path, monkeypatch):
    from jarvis import code_index

    monkeypatch.setattr(code_index, "CODE_INDEX", tmp_path / "missing_index.json")
    code_index.invalidate_cache()
    monkeypatch.setattr(
        code_index,
        "build_index",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("built on search path")),
    )

    assert code_index.search("hello", limit=3) == []


def test_gather_context_skips_semantic_search_without_index(tmp_path, monkeypatch):
    from jarvis import code_index
    from jarvis.code_context import gather_context

    source = tmp_path / "sample.py"
    source.write_text("print('hello')\n", encoding="utf-8")
    monkeypatch.setattr(code_index, "CODE_INDEX", tmp_path / "missing_index.json")
    code_index.invalidate_cache()
    monkeypatch.setattr(
        code_index,
        "search",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("semantic search ran")),
    )

    ctx = gather_context("sample.py", tmp_path, task="find hello")

    assert ctx["primary"] == "print('hello')\n"
    assert ctx["semantic"] == []
