"""LSP helper coverage."""

from __future__ import annotations

from pathlib import Path

from jarvis.lsp import check_any, check_python, tools_status


def test_tools_status_shape():
    status = tools_status()
    assert isinstance(status, dict)


def test_check_python_clean(tmp_path):
    p = tmp_path / "clean.py"
    p.write_text("def ok():\n    return 1\n", encoding="utf-8")
    diags = check_python(p)
    assert isinstance(diags, list)


def test_check_any_python(tmp_path):
    p = tmp_path / "x.py"
    p.write_text("x = 1\n", encoding="utf-8")
    diags = check_any(p, deep=False)
    assert isinstance(diags, list)
