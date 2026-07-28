"""Chat assistant smoke — branch surface without heavy fixture spin-up."""

from __future__ import annotations

from pathlib import Path


def test_branch_manager_create(tmp_path, monkeypatch):
    from jarvis import branches as br

    monkeypatch.setattr(br, "BRANCHES_FILE", tmp_path / "chat_branches.json")
    monkeypatch.setattr(br, "DATA_DIR", tmp_path)
    mgr = br.BranchManager()
    bid = mgr.create_branch("chat-os-test")
    assert isinstance(bid, str) and bid
    listed = mgr.list_branches()
    ids = [b["id"] for b in listed]
    assert bid in ids


def test_create_branch_api_on_assistant_class():
    # Import only the class attribute surface — avoid constructing full assistant in unit tests
    src = Path("jarvis/assistant.py").read_text(encoding="utf-8")
    assert "def create_branch" in src
