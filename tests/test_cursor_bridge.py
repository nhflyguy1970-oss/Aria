"""Cursor / IDE bridge coverage."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from jarvis.cursor_bridge import (
    build_code_index,
    check_syntax,
    get_file_context,
    list_project_files,
    propose_fix,
    search_codebase,
)


def test_check_syntax(tmp_path):
    (tmp_path / "a.py").write_text("a = 1\n", encoding="utf-8")
    out = check_syntax("a.py", tmp_path)
    assert out["path"] == "a.py"
    assert "ok" in out


def test_list_project_files(tmp_path):
    (tmp_path / "a.py").write_text("1\n", encoding="utf-8")
    files = list_project_files(tmp_path, limit=10)
    assert isinstance(files, list)


def test_search_codebase_mocked():
    with patch("jarvis.cursor_bridge.code_search", return_value=[{"path": "a.py", "score": 1}]):
        hits = search_codebase("hello", limit=3)
    assert hits and hits[0]["path"] == "a.py"


def test_get_file_context_mocked(tmp_path):
    with patch("jarvis.cursor_bridge.gather_context", return_value={"primary": "p", "related": [], "tests": []}):
        with patch("jarvis.cursor_bridge.format_context", return_value="fmt"):
            ctx = get_file_context("a.py", tmp_path)
    assert ctx["formatted"] == "fmt"


def test_propose_fix_delegates():
    assistant = MagicMock()
    assistant._coding_fix.return_value = {"ok": True, "proposal_id": "p1"}
    with patch("jarvis.cursor_bridge._assistant", return_value=assistant):
        out = propose_fix("a.py", "fix it", Path("."), mode="fix")
    assert out.get("proposal_id") == "p1" or out.get("ok") is True


def test_build_code_index_mocked(tmp_path):
    with patch("jarvis.cursor_bridge.invalidate_cache"):
        with patch("jarvis.cursor_bridge.build_index", return_value=[1, 2, 3]):
            out = build_code_index(tmp_path)
    assert out["ok"] is True
    assert out["chunks"] == 3
