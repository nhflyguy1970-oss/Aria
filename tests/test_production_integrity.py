"""Production Integrity platform safeguard tests."""

from __future__ import annotations

from types import SimpleNamespace

import pytest


@pytest.fixture
def projects_env(tmp_path, monkeypatch):
    root = tmp_path / "projects"
    active = tmp_path / "active_project.json"
    journal = tmp_path / "journal" / "projects"
    journal.mkdir(parents=True)
    monkeypatch.setattr("jarvis.project_registry.PROJECTS_ROOT", root)
    monkeypatch.setattr("jarvis.active_project.ACTIVE_FILE", active)
    monkeypatch.setattr("jarvis.active_project.DATA_DIR", tmp_path)
    monkeypatch.setattr("jarvis.project_journal.PROJECTS_DIR", journal)
    monkeypatch.setattr("jarvis.project_journal.INDEX_FILE", journal / "index.json")
    monkeypatch.setattr("jarvis.integrity_product.store.INTEGRITY_DIR", tmp_path / "integrity_product")
    monkeypatch.setattr(
        "jarvis.integrity_product.store.LAST_SCAN_FILE",
        tmp_path / "integrity_product" / "last_scan.json",
    )
    monkeypatch.setattr(
        "jarvis.integrity_product.store.HISTORY_FILE",
        tmp_path / "integrity_product" / "history.jsonl",
    )
    monkeypatch.setattr("jarvis.integrity_product.checks.DATA_DIR", tmp_path)
    monkeypatch.setattr("jarvis.integrity_product.remediate.DATA_DIR", tmp_path)
    return SimpleNamespace(root=root, active=active, journal=journal, tmp=tmp_path)


def test_scan_detects_qa_project_and_does_not_auto_delete(projects_env):
    from jarvis.integrity_product.scanner import invalidate_cache, run_scan
    from jarvis.project_registry import create_project, list_projects

    create_project("QA Workflow Project Probe", description="Lead QA workflow probe")
    create_project("Real Personal Notes")
    invalidate_cache()
    scan = run_scan(force=True, trigger="test")
    assert scan["ok"]
    assert not scan["clean"]
    assert scan["auto_delete"] is False
    titles = [f["title"] for f in scan["findings"]]
    assert any("QA" in t or "qa" in t.lower() for t in titles)
    assert any(p["slug"].startswith("qa-") for p in list_projects(include_qa=True))
    assert any(p["slug"] == "real-personal-notes" for p in list_projects())


def test_remediate_removes_only_qa_keeps_real(projects_env):
    from jarvis.integrity_product.remediate import apply_safe_remediations
    from jarvis.integrity_product.scanner import invalidate_cache
    from jarvis.project_registry import create_project, list_projects

    create_project("QA Workflow Project Probe", description="Lead QA workflow probe")
    create_project("Jeff Lab")
    invalidate_cache()
    result = apply_safe_remediations()
    assert result.get("remaining_artifacts") == 0
    prod = list_projects()
    assert any(p["slug"] == "jeff-lab" for p in prod)
    assert not any((p.get("slug") or "").startswith("qa-") for p in list_projects(include_qa=True))


def test_artifact_metadata_helper():
    from jarvis.integrity_product.tags import artifact_metadata, looks_like_dev_label

    meta = artifact_metadata(artifact_type="smoke", creation_reason="unit test", smoke_id="s1")
    assert meta["qa_artifact"] is True
    assert meta["artifact_type"] == "smoke"
    assert meta["smoke_id"] == "s1"
    assert looks_like_dev_label("QA Workflow Project")
    assert looks_like_dev_label("lorem ipsum dolor")
    assert not looks_like_dev_label("Blood pressure tracking")


def test_repair_module_detect_and_verify(projects_env):
    from jarvis.integrity_product.repair_module import ProductionIntegrityModule
    from jarvis.integrity_product.scanner import invalidate_cache
    from jarvis.project_registry import create_project

    create_project("Cert Proj 42", qa_artifact=True, origin="certification")
    invalidate_cache()
    mod = ProductionIntegrityModule()
    issues = mod.detect()
    assert issues
    plan = mod.repair_plan(issues[0], mod.diagnose(issues[0]))
    assert plan.approval_class
    assert "allow-listed" in plan.risk_why or "known-safe" in plan.risk_why
    out = mod.repair(issues[0], plan)
    assert out.executed
    v = mod.verify(issues[0])
    assert v.ok


def test_known_dev_path_detection(tmp_path, monkeypatch):
    monkeypatch.setattr("jarvis.integrity_product.checks.DATA_DIR", tmp_path)
    (tmp_path / "qa_ocr_sample.png").write_bytes(b"x")
    from jarvis.integrity_product.checks import check_known_dev_paths

    found = check_known_dev_paths()
    assert any("qa_ocr_sample" in f["title"] for f in found)


def test_integrity_score_never_hides_problems(projects_env):
    from jarvis.integrity_product.scanner import invalidate_cache, run_scan
    from jarvis.integrity_product.score import compute_score
    from jarvis.project_registry import create_project

    create_project("QA Workflow Project Probe", description="Lead QA workflow probe")
    invalidate_cache()
    dirty = run_scan(force=True, trigger="score_dirty")
    score = dirty.get("score") or compute_score(dirty)
    assert score["informational_only"] is True
    assert score["hides_problems"] is False
    assert score["overall"] < 100
    assert score["artifacts"] >= 1
    assert "health" in score["sections"]
    assert "projects" in score["sections"]


def test_qa_documents_detected(tmp_path, monkeypatch):
    monkeypatch.setattr("jarvis.integrity_product.checks.DATA_DIR", tmp_path)
    imports = tmp_path / "documents" / "imports"
    imports.mkdir(parents=True)
    (imports / "QA_Aria_Resume.txt").write_text("QA Resume content for Aria local FS test", encoding="utf-8")
    (imports / "Resume 2026.pdf").write_bytes(b"%PDF")
    from jarvis.integrity_product.checks import check_qa_documents

    found = check_qa_documents()
    assert any("QA_Aria_Resume" in f["title"] for f in found)
    assert not any("Resume 2026" in f["title"] for f in found)
