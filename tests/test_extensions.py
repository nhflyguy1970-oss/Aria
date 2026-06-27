"""Phase 1 extension framework tests."""

from __future__ import annotations

import subprocess

import pytest


def test_extensions_discover_git():
    from jarvis.extensibility.loader import load_extensions

    exts = load_extensions(force=True)
    names = {e.meta.name for e in exts}
    assert "git" in names


def test_git_extension_registers_all_actions():
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import get_spec, has_action

    ensure_handlers_loaded()
    for action in (
        "git_status",
        "git_diff",
        "git_commit",
        "git_branch",
        "git_summarize",
        "git_pr",
    ):
        assert has_action(action), action
        spec = get_spec(action)
        assert spec and spec.extension == "git"


def test_git_extension_routes():
    from jarvis.router_table import match_router_table
    from jarvis.session import SessionContext

    session = SessionContext()
    assert match_router_table("git status", session)["action"] == "git_status"
    assert match_router_table("git diff", session)["action"] == "git_diff"
    hit = match_router_table("commit: fix typo", session)
    assert hit["action"] == "git_commit"
    assert hit["params"]["message"] == "fix typo"
    hit = match_router_table("create branch feature/widgets", session)
    assert hit["action"] == "git_branch"
    assert hit["params"]["name"] == "feature/widgets"


def test_git_status_handler_in_repo(assistant, tmp_path, monkeypatch):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    monkeypatch.setattr(assistant.coding, "_base", lambda: tmp_path)
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    out = call_action(assistant, "git_status", {}, "git status")
    assert out["ok"] is True
    assert "main" in out["message"].lower() or "master" in out["message"].lower()


def test_extensions_api_route(chat_app):
    from jarvis.handlers import ensure_handlers_loaded

    ensure_handlers_loaded()
    res = chat_app.get("/api/registry/extensions")
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert any(e["name"] == "git" for e in body["extensions"])


def test_git_api_routes(chat_app):
    from jarvis.handlers import ensure_handlers_loaded

    ensure_handlers_loaded()
    res = chat_app.get("/api/git/status")
    assert res.status_code == 200
    assert "status" in res.json()
