"""Certification product — evidence store + gate (no live server required for unit bits)."""

from __future__ import annotations

from jarvis.certification_product import store
from jarvis.certification_product.runner import evaluate_gate, mutation_check, CertContext


def test_store_create_and_assert_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "CERT_ROOT", tmp_path / "certification")
    monkeypatch.setattr(store, "RUNS_DIR", tmp_path / "certification" / "runs")
    monkeypatch.setattr(store, "INDEX_FILE", tmp_path / "certification" / "index.json")
    monkeypatch.setattr(store, "LATEST_FILE", tmp_path / "certification" / "latest_run.json")

    man = store.create_run(label="unit")
    run_id = man["id"]
    ctx = CertContext(run_id, base="http://127.0.0.1:9")
    ctx.set_feature("demo", "Demo")
    assert ctx.assert_("equal", 1, 1) is True
    assert ctx.assert_("unequal", 1, 2) is False
    rows = store.list_assertions(run_id)
    assert len(rows) == 2
    assert rows[0]["result"] == "PASS"
    assert rows[1]["result"] == "FAIL"
    files = store.list_evidence_files(run_id)
    assert any(f["path"].endswith("assertions.jsonl") for f in files)


def test_mutation_check_detects_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "CERT_ROOT", tmp_path / "certification")
    monkeypatch.setattr(store, "RUNS_DIR", tmp_path / "certification" / "runs")
    monkeypatch.setattr(store, "INDEX_FILE", tmp_path / "certification" / "index.json")
    monkeypatch.setattr(store, "LATEST_FILE", tmp_path / "certification" / "latest_run.json")

    man = store.create_run(label="mutation")
    ctx = CertContext(man["id"], base="http://127.0.0.1:9")
    out = mutation_check(ctx)
    assert out["harness_ok"] is True
    assert ctx.features["mutation_check"]["status"] == "PASS"
    fails = [a for a in store.list_assertions(man["id"]) if a["result"] == "FAIL"]
    assert fails, "mutation must record a FAIL assertion"


def test_gate_blocks_on_untested_required(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "CERT_ROOT", tmp_path / "certification")
    monkeypatch.setattr(store, "RUNS_DIR", tmp_path / "certification" / "runs")
    monkeypatch.setattr(store, "INDEX_FILE", tmp_path / "certification" / "index.json")
    monkeypatch.setattr(store, "LATEST_FILE", tmp_path / "certification" / "latest_run.json")

    man = store.create_run(label="gate")
    ctx = CertContext(man["id"], base="http://127.0.0.1:9")
    ctx.set_feature("chat_clear", "Chat")
    ctx.finish_feature("chat_clear", True)
    ctx.assert_("ok", True, True)
    store.update_manifest(man["id"], {"counts": {"assertions": 1, "pass": 1, "fail": 0, "api_calls": 2}})
    coverage = {
        "feature_coverage_pct": 100.0,
        "untested_required": ["planner_calendar"],
    }
    gate = evaluate_gate(ctx, coverage, skip_image=True, selected_suites=["chat_clear"])
    assert gate["gate"] in ("DO_NOT_SHIP", "SMOKE_PASS")
    assert gate["gate"] != "READY_TO_SHIP"
    assert any("incomplete" in b.lower() or "image_lifecycle" in b.lower() for b in gate["blockers"])


def test_skip_image_cannot_ready_to_ship(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "CERT_ROOT", tmp_path / "certification")
    monkeypatch.setattr(store, "RUNS_DIR", tmp_path / "certification" / "runs")
    monkeypatch.setattr(store, "INDEX_FILE", tmp_path / "certification" / "index.json")
    monkeypatch.setattr(store, "LATEST_FILE", tmp_path / "certification" / "latest_run.json")

    man = store.create_run(label="no-image")
    ctx = CertContext(man["id"], base="http://127.0.0.1:9")
    for fid in (
        "chat_clear",
        "planner_calendar",
        "journal_calendar",
        "search_federated",
        "settings_appearance",
        "projects_archive",
    ):
        ctx.set_feature(fid, fid)
        ctx.finish_feature(fid, True)
    ctx.assert_("ok", True, True)
    store.update_manifest(man["id"], {"counts": {"assertions": 1, "pass": 1, "fail": 0, "api_calls": 2}})
    coverage = {"feature_coverage_pct": 100.0, "untested_required": []}
    gate = evaluate_gate(ctx, coverage, skip_image=True)
    assert gate["gate"] != "READY_TO_SHIP"
    assert any("image_lifecycle" in b for b in gate["blockers"])


def test_ready_history_invalidated_without_image_lifecycle_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "CERT_ROOT", tmp_path / "certification")
    monkeypatch.setattr(store, "RUNS_DIR", tmp_path / "certification" / "runs")
    monkeypatch.setattr(store, "INDEX_FILE", tmp_path / "certification" / "index.json")
    monkeypatch.setattr(store, "LATEST_FILE", tmp_path / "certification" / "latest_run.json")

    man = store.create_run(label="stale-ready")
    run_id = man["id"]
    store.update_manifest(
        run_id,
        {
            "status": "complete",
            "gate": "READY_TO_SHIP",
            "features": {"image_lifecycle": {"status": "PASS"}},
        },
    )

    latest = store.latest_run()
    history = store.list_runs()
    assert latest["gate"] == "DO_NOT_SHIP"
    assert latest["invalidated_gate"] == "READY_TO_SHIP"
    assert history[0]["gate"] == "DO_NOT_SHIP"
    assert any("image_lifecycle" in b for b in latest["blockers"])


def test_ready_history_kept_with_generated_image_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "CERT_ROOT", tmp_path / "certification")
    monkeypatch.setattr(store, "RUNS_DIR", tmp_path / "certification" / "runs")
    monkeypatch.setattr(store, "INDEX_FILE", tmp_path / "certification" / "index.json")
    monkeypatch.setattr(store, "LATEST_FILE", tmp_path / "certification" / "latest_run.json")

    man = store.create_run(label="real-ready")
    run_id = man["id"]
    store.write_text(run_id, "screenshots/IMAGE_FILE_EVIDENCE.txt", "generated asset\n")
    store.write_bytes(run_id, "screenshots/generated.png", b"real image bytes")
    store.update_manifest(
        run_id,
        {
            "status": "complete",
            "gate": "READY_TO_SHIP",
            "features": {"image_lifecycle": {"status": "PASS"}},
        },
    )

    latest = store.latest_run()
    assert latest["gate"] == "READY_TO_SHIP"
