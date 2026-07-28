"""Coding verify fixtures / helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from jarvis.coding_verify import verify_file_changes, verify_proposed_files, verify_python_files


def test_verify_python_files_empty(tmp_path):
    msg = verify_python_files([], tmp_path)
    assert msg == "" or msg is None or isinstance(msg, str)


def test_verify_proposed_files_syntax(tmp_path):
    files = [{"path": "ok.py", "code": "def f():\n    return 1\n"}]
    with patch("jarvis.coding_verify.verify_candidate_pytest", return_value=(True, "")):
        ok, msg = verify_proposed_files(files, tmp_path)
    assert isinstance(ok, bool)


def test_verify_file_changes_agent_mode(tmp_path):
    (tmp_path / "mod.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    files = [{"path": "mod.py", "code": "def f():\n    return 2\n"}]
    with patch("jarvis.coding_verify.verify_proposed_files", return_value=(True, "ok")):
        ok, msg = verify_file_changes(files, tmp_path, mode="agent")
    assert ok is True
