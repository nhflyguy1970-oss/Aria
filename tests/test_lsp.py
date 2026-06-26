"""Tests for IDE-grade LSP bridge."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jarvis.lsp_protocol import LspProcess
from jarvis.lsp_servers import find_lsp_root, server_for_path
from jarvis.lsp_session import _apply_edits, _offset_at


def test_offset_at_and_apply_edits():
    text = "hello\nworld\n"
    assert _offset_at(text, 1, 2) == len("hello\n") + 2
    edited = _apply_edits("foo bar", [{"range": {"start": {"line": 0, "character": 4}, "end": {"line": 0, "character": 7}}, "newText": "baz"}])
    assert edited == "foo baz"


def test_server_for_python():
    with patch("jarvis.lsp_servers._which", return_value="/usr/bin/pylsp"):
        spec = server_for_path(Path("jarvis/lsp.py"))
        assert spec is not None
        assert spec.id == "python"


def test_find_lsp_root_uses_project(tmp_path, monkeypatch):
    from jarvis.config import PROJECT_ROOT

    monkeypatch.chdir(tmp_path)
    child = PROJECT_ROOT / "jarvis" / "lsp.py"
    root = find_lsp_root(child)
    assert root == PROJECT_ROOT


def test_lsp_diagnostics_integration(tmp_path):
    from jarvis.lsp_bridge import lsp_diagnostics

    py = tmp_path / "bad.py"
    py.write_text("def foo(\n  pass\n", encoding="utf-8")
    out = lsp_diagnostics(str(py), tmp_path, deep=False)
    assert out["ok"] is True
    assert "diagnostics" in out


@patch("jarvis.lsp_client.get_session")
def test_lsp_definition_mock(mock_get, tmp_path):
    from jarvis.lsp_bridge import lsp_definition

    f = tmp_path / "a.py"
    f.write_text("x = 1\n", encoding="utf-8")
    session = MagicMock()
    session.definition.return_value = [{"path": str(f), "line": 1, "column": 1}]
    mock_get.return_value = session
    out = lsp_definition(str(f), tmp_path, 1, 1)
    assert out["ok"] is True
    assert out["locations"][0]["line"] == 1


def test_lsp_send_message_roundtrip():
    import subprocess

    proc = subprocess.Popen(
        ["python3", "-c", """
import sys, json
while True:
    headers = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            raise SystemExit(0)
        line = line.decode().strip()
        if not line:
            break
        k, v = line.split(':', 1)
        headers[k.strip().lower()] = v.strip()
    n = int(headers['content-length'])
    body = json.loads(sys.stdin.buffer.read(n).decode())
    if 'id' in body:
        resp = {'jsonrpc':'2.0','id':body['id'],'result':{'ok':True}}
        data = json.dumps(resp).encode()
        sys.stdout.buffer.write(f'Content-Length: {len(data)}\\r\\n\\r\\n'.encode() + data)
        sys.stdout.buffer.flush()
"""],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        bufsize=0,
    )
    conn = LspProcess(proc=proc, cmd=["python3"])
    result = conn.request("initialize", {"rootUri": "file:///tmp"}, timeout=5)
    assert result == {"ok": True}
    conn.shutdown()


def test_tools_status_includes_lsp():
    from jarvis.lsp import tools_status

    tools = tools_status()
    assert "lsp" in tools
