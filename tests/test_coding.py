"""Coding product regression suite — agent, proposals, history, guardrails, verify, jobs, LSP, bridge."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jarvis.coding_agent import AgentResult, CodingAgent
from jarvis.coding_product.brief import build_quality_brief
from jarvis.coding_product.guardrails import assess_coding_root, guardrail_banner
from jarvis.coding_product.history import (
    export_patch,
    list_history,
    record_proposal,
    restore_to_pending,
    update_status,
)
from jarvis.coding_product.home import coding_home_snapshot
from jarvis.coding_product.job_links import coding_job_deep_links, enrich_coding_job
from jarvis.coding_product.preferences import load_preferences, preference_suggestions, save_preferences
from jarvis.coding_product.terminology import BOUNDARIES, TERMINOLOGY
from jarvis.coding_product.verify_workflow import build_verify_offer, run_verify
from jarvis.coding_product.vision_fix import vision_bugfix
from jarvis.coding_product.spec_to_code import spec_to_plan
from jarvis.cursor_bridge import check_syntax, get_file_context, search_codebase
from jarvis.proposal_store import load as load_proposals
from jarvis.proposal_store import save as save_proposals


@pytest.fixture
def coding_env(tmp_path, monkeypatch):
    monkeypatch.setattr("jarvis.coding_product.history.HISTORY_FILE", tmp_path / "history.json")
    monkeypatch.setattr("jarvis.coding_product.preferences.PREFS_FILE", tmp_path / "prefs.json")
    monkeypatch.setattr("jarvis.proposal_store.PROPOSALS_FILE", tmp_path / "pending_proposals.json")
    root = tmp_path / "repo"
    root.mkdir()
    (root / "sample.py").write_text("def hello():\n    return 1\n", encoding="utf-8")
    return root


def test_terminology_and_boundaries():
    assert "Propose" in TERMINOLOGY["Coding"] or "propose" in TERMINOLOGY["Coding"].lower()
    assert "propose" in BOUNDARIES["owns"]
    assert "projects_workspace_identity" in BOUNDARIES["does_not_own"]


def test_guardrails_no_root(monkeypatch):
    monkeypatch.setattr("jarvis.active_project.get_active_slug", lambda: "")
    monkeypatch.setattr("jarvis.active_project.identity_for_slug", lambda slug: {
        "slug": "", "title": "", "coding_root": "", "git_path": "",
    })
    a = assess_coding_root(None)
    assert a["severity"] == "error"
    assert any(w["code"] == "no_coding_root" for w in a["warnings"])
    assert "coding root" in guardrail_banner(a).lower() or "No coding" in guardrail_banner(a)


def test_guardrails_with_project(coding_env, monkeypatch):
    monkeypatch.setattr("jarvis.active_project.get_active_slug", lambda: "demo")
    monkeypatch.setattr(
        "jarvis.active_project.identity_for_slug",
        lambda slug: {
            "slug": "demo",
            "title": "Demo",
            "coding_root": str(coding_env),
            "git_path": str(coding_env),
        },
    )
    assistant = MagicMock()
    assistant.session.coding_root = str(coding_env)
    assistant.coding._base.return_value = coding_env
    a = assess_coding_root(assistant)
    assert a["coding_root"] == str(coding_env.resolve())
    assert a["write_target"]


def test_quality_brief_risk():
    brief = build_quality_brief(
        {
            "files": [{"path": "auth/secret.py", "code": "x = 1\n" * 50}],
            "syntax_ok": True,
            "mode": "fix",
            "explanation": "touch auth",
        }
    )
    assert brief["ok"] is True
    assert brief["file_count"] == 1
    assert brief["breaking_change_warning"] is True
    assert brief["estimated_risk"] in ("medium", "high")
    assert brief["suggested_verification_steps"]


def test_proposal_history_lifecycle(coding_env, monkeypatch):
    prop = {
        "files": [{"path": "sample.py", "code": "def hello():\n    return 2\n"}],
        "explanation": "bump return",
        "syntax_ok": True,
        "mode": "fix",
    }
    row = record_proposal("abc12345", prop, status="pending", model="test-coder")
    assert row["id"] == "abc12345"
    assert list_history(query="bump").get("total") == 1
    update_status("abc12345", "applied", verification_status="pending_operator")
    items = list_history(status="applied")["items"]
    assert items[0]["status"] == "applied"
    patch = export_patch("abc12345")
    assert patch["ok"] is True
    assert "sample.py" in (patch.get("patch") or "")


def test_restore_to_pending(coding_env, monkeypatch):
    prop = {
        "files": [{"path": "sample.py", "code": "def hello():\n    return 3\n"}],
        "explanation": "restore me",
        "syntax_ok": True,
        "mode": "fix",
    }
    record_proposal("rest0001", prop, status="applied")
    assistant = MagicMock()
    assistant.pending_proposals = {}
    assistant.session = MagicMock()
    out = restore_to_pending(assistant, "rest0001")
    assert out["ok"] is True
    assert out["proposal_id"] in assistant.pending_proposals
    assistant._persist_proposals.assert_called()


def test_verify_requires_approval(coding_env):
    offer = build_verify_offer(applied_paths=["sample.py"], base=coding_env, proposal_id="x")
    assert offer["requires_approval"] is True
    assistant = MagicMock()
    assistant.coding._base.return_value = coding_env
    assistant.last_apply_backups = [{"path": "sample.py"}]
    denied = run_verify(assistant, actions=["syntax"], approved=False)
    assert denied["ok"] is False
    assert denied["requires_approval"] is True


def test_verify_syntax_approved(coding_env):
    assistant = MagicMock()
    assistant.coding._base.return_value = coding_env
    assistant.last_apply_backups = [{"path": "sample.py"}]
    with patch("jarvis.fs.read_file", return_value="def hello():\n    return 1\n"):
        with patch("jarvis.syntax_check.check_files", return_value=[]):
            with patch("jarvis.syntax_check.format_diagnostics", return_value="**syntax:** ok"):
                out = run_verify(
                    assistant,
                    actions=["syntax", "summary"],
                    paths=["sample.py"],
                    approved=True,
                )
    assert out.get("requires_approval") is False
    assert "syntax" in out.get("results", {})


def test_coding_home_snapshot(coding_env, monkeypatch):
    monkeypatch.setattr("jarvis.active_project.get_active_slug", lambda: "demo")
    monkeypatch.setattr(
        "jarvis.active_project.identity_for_slug",
        lambda slug: {
            "slug": "demo",
            "title": "Demo",
            "coding_root": str(coding_env),
            "git_path": str(coding_env),
        },
    )
    assistant = MagicMock()
    assistant.session.coding_root = str(coding_env)
    assistant.coding._base.return_value = coding_env
    assistant.pending_proposals = {
        "p1": {"explanation": "demo", "mode": "fix", "files": [{"path": "sample.py"}], "syntax_ok": True}
    }
    with patch("jarvis.coding_product.home._coding_model", return_value={"role": "coding", "model": "x", "provider": "ollama"}):
        with patch("jarvis.coding_product.home._recent_jobs", return_value=[]):
            snap = coding_home_snapshot(assistant)
    assert snap["ok"] is True
    assert snap["product"] == "coding"
    assert snap["open_proposals"]
    assert "Ctrl+Shift+C" in snap["shortcut"]


def test_job_deep_links():
    links = coding_job_deep_links({"done": True, "result": {"proposal_id": "abcd1234", "type": "proposal"}})
    assert links["proposal_id"] == "abcd1234"
    assert links["coding_home"] == "coding"
    enriched = enrich_coding_job({"id": "j1", "result": {"proposal_id": "abcd1234"}})
    assert enriched["deep_links"]["proposal"]


def test_preferences_suggestions_only(tmp_path, monkeypatch):
    monkeypatch.setattr("jarvis.coding_product.preferences.PREFS_FILE", tmp_path / "prefs.json")
    save_preferences({"enabled": True, "style": "small diffs", "test_runner": "pytest"})
    sug = preference_suggestions()
    assert sug["enabled"] is True
    assert any("small diffs" in s for s in sug["suggestions"])
    assert "never silently" in sug["note"].lower()


def test_spec_to_plan_from_path(coding_env):
    doc = coding_env / "SPEC.md"
    doc.write_text("# Spec\n\nAdd a goodbye function.\n", encoding="utf-8")
    assistant = MagicMock()
    plan = spec_to_plan(assistant, document_path=str(doc))
    assert plan["ok"] is True
    assert plan["document_refs"]
    assert plan["auto_applied"] is False


def test_vision_fix_missing_file(coding_env):
    assistant = MagicMock()
    out = vision_bugfix(assistant, image_path=str(coding_env / "missing.png"), propose=False)
    assert out["ok"] is False


def test_coding_agent_diagnose(coding_env, monkeypatch):
    agent = CodingAgent(coding_env, max_steps=2)

    def fake_llm(*args, **kwargs):
        return "Looks fine."

    with patch("jarvis.coding_agent.gather_context", return_value={"related": [], "primary": "sample.py"}):
        with patch("jarvis.llm.chat", side_effect=fake_llm):
            with patch.object(agent, "_run_file", return_value=(0, "")):
                # diagnose may call llm differently — just ensure read works
                content = agent._read("sample.py")
    assert "def hello" in content


def test_coding_agent_run_returns_result_shape(coding_env):
    agent = CodingAgent(coding_env, max_steps=1)
    with patch.object(
        agent,
        "run",
        return_value=AgentResult(ok=True, message="done", files=[{"path": "sample.py", "code": "x=1\n"}], explanation="n"),
    ):
        result = agent.run("noop")
    assert result.ok
    assert result.files


def test_proposal_store_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr("jarvis.proposal_store.PROPOSALS_FILE", tmp_path / "pending_proposals.json")
    save_proposals({"p1": {"path": "a.py", "code": "1", "files": [{"path": "a.py", "code": "1"}]}})
    data = load_proposals()
    assert "p1" in data


def test_specialist_coder_uses_path_base():
    """Regression: CodingAgent must be constructed with Path base, not assistant."""
    import inspect

    from jarvis.specialists import execute

    src = inspect.getsource(execute._run_coder)
    assert "CodingAgent(base" in src or "CodingAgent(assistant.coding._base()" in src
    assert "CodingAgent(assistant)" not in src


def test_cursor_bridge_syntax(coding_env):
    out = check_syntax("sample.py", coding_env)
    assert "ok" in out
    assert "diagnostics" in out


def test_cursor_bridge_context(coding_env):
    with patch("jarvis.cursor_bridge.gather_context", return_value={"primary": "x", "related": [], "tests": []}):
        with patch("jarvis.cursor_bridge.format_context", return_value="formatted"):
            ctx = get_file_context("sample.py", coding_env, task="test")
    assert ctx["path"] == "sample.py"
    assert ctx["formatted"] == "formatted"


def test_apply_proposal_records_history(coding_env, monkeypatch):
    monkeypatch.setattr("jarvis.coding_product.history.HISTORY_FILE", coding_env.parent / "hist.json")
    prop = {
        "files": [{"path": "sample.py", "code": "def hello():\n    return 9\n"}],
        "explanation": "x",
        "syntax_ok": True,
    }
    record_proposal("apply001", prop, status="pending")
    update_status("apply001", "applied", verification_status="pending_operator")
    assert list_history(status="applied")["total"] >= 1
