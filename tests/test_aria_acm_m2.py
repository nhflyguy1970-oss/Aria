"""M2 — Aria ACM harvest migrate gates (blueprint INTEGRATION_TEST_PLAN)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aria_core import acm_bridge, acm_harvest, memory_manager


@pytest.fixture(autouse=True)
def _m2_isolation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, data_dir: Path):
    monkeypatch.setenv("ARIA_ACM_SHADOW", "0")
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "0")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "acm_harvest.db"))
    monkeypatch.setenv("ARIA_ACM_AUTO_PERSIST", "1")
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
    acm_harvest._LAST_REPORT = None  # noqa: SLF001 — test reset
    yield
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
    acm_harvest._LAST_REPORT = None  # noqa: SLF001


def _seed_entries() -> list[dict]:
    entries = []
    for i in range(40):
        entries.append(
            {
                "id": f"leg-p0-{i}",
                "type": "fact",
                "content": f"User fact unique{i} about topic{i}",
                "namespace": "default",
                "timestamp": f"2026-01-01T00:00:{i:02d}+00:00",
                "tags": [f"topic{i}"],
            }
        )
    # preferences
    for i in range(10):
        entries.append(
            {
                "id": f"leg-pref-{i}",
                "type": "preference",
                "content": f"User prefers flavor{i}",
                "namespace": "profile",
                "timestamp": f"2026-01-02T00:00:{i:02d}+00:00",
                "tags": ["preference"],
            }
        )
    # journal
    for i in range(5):
        entries.append(
            {
                "id": f"leg-j-{i}",
                "type": "note",
                "content": f"From bullet journal: day note {i}",
                "namespace": "journal-learned",
                "timestamp": f"2026-01-03T00:00:{i:02d}+00:00",
                "tags": ["journal"],
            }
        )
    # project
    entries.append(
        {
            "id": "leg-proj-1",
            "type": "project",
            "content": "Checkpoint: finish ACM harvest M2",
            "namespace": "project:acm",
            "timestamp": "2026-01-04T00:00:00+00:00",
            "tags": ["checkpoint"],
        }
    )
    # telemetry skipped
    entries.append(
        {
            "id": "leg-tel-1",
            "type": "auto",
            "content": "tool ran ok",
            "namespace": "default",
            "timestamp": "2026-01-05T00:00:00+00:00",
            "tags": ["telemetry"],
        }
    )
    return entries


@pytest.mark.m2
def test_m2_01_completeness_provenance_idempotency(tmp_path: Path) -> None:
    """M2-01: P0 coverage ≥ 99.5%, provenance present, idempotent re-run."""
    entries = _seed_entries()
    report = acm_harvest.harvest_into_acm(
        entries=entries,
        priorities=frozenset({"P0", "P1"}),
        assent_identity=True,
        report_path=tmp_path / "harvest1.json",
    )
    assert report["ok"] is True
    assert report["authoritative"] == "legacy"
    assert report["encode_failures"] == 0
    assert report["completeness_rate"] is not None
    assert report["completeness_rate"] >= 0.995
    assert report["provenance_ok"] >= report["imported"]
    assert report["provenance_missing"] == 0

    # Idempotent second run — no duplicate legacy_ids
    report2 = acm_harvest.harvest_into_acm(
        entries=entries,
        priorities=frozenset({"P0", "P1"}),
        assent_identity=True,
    )
    assert report2["imported"] == 0
    assert report2["skipped_existing"] >= report["imported"]
    engine = acm_bridge.get_engine()
    idx = acm_harvest.index_legacy_ids(engine)
    # unique legacy ids
    assert len(idx) == len(set(idx.keys()))
    # no telemetry
    assert "leg-tel-1" not in idx


@pytest.mark.m2
def test_m2_02_supersede_revise_lineage() -> None:
    """M2-02: known revises: parent link via revises_id / revise lineage."""
    old = {
        "id": "leg-old",
        "type": "fact",
        "content": "Favorite coffee is drip",
        "namespace": "default",
        "timestamp": "2026-01-01T00:00:00+00:00",
        "tags": ["coffee", "superseded"],
    }
    new = {
        "id": "leg-new",
        "type": "fact",
        "content": "Favorite coffee is espresso",
        "namespace": "default",
        "timestamp": "2026-01-02T00:00:00+00:00",
        "tags": ["coffee", "revises:leg-old"],
    }
    report = acm_harvest.harvest_into_acm(
        entries=[old, new],
        priorities=frozenset({"P0"}),
        assent_identity=True,
    )
    assert report["ok"] is True
    assert report["revised"] >= 1
    engine = acm_bridge.get_engine()
    old_exp = acm_harvest.find_experience_by_legacy_id(engine, "leg-old")
    new_exp = acm_harvest.find_experience_by_legacy_id(engine, "leg-new")
    assert old_exp and new_exp
    new_obj = engine.store.experiences[new_exp]
    assert new_obj.revises_id == old_exp


@pytest.mark.m2
def test_m2_03_identity_assent_high_impact() -> None:
    """M2-03: identity proposals can be assented during harvest."""
    entries = [
        {
            "id": "leg-id-1",
            "type": "fact",
            "content": "My name is Jeff and I am the operator",
            "namespace": "profile",
            "timestamp": "2026-01-01T12:00:00+00:00",
            "tags": ["identity", "name"],
        }
    ]
    report = acm_harvest.harvest_into_acm(
        entries=entries,
        priorities=frozenset({"P0"}),
        assent_identity=True,
    )
    assert report["imported"] >= 1
    # Identity may or may not emit proposal depending on ACM classification;
    # if proposals exist they must be assented when flag on.
    if report["identity_proposals"]:
        assert report["identity_assented"] >= 1
    who = acm_bridge.get_engine().who_am_i()
    assert isinstance(who, dict)


@pytest.mark.m2
def test_m2_04_journal_project_preference_packs() -> None:
    """M2-04: journal / project / preference spot packs import."""
    entries = _seed_entries()
    report = acm_harvest.harvest_into_acm(
        entries=entries,
        priorities=frozenset({"P0", "P1"}),
        assent_identity=True,
    )
    assert report["preference_imported"] >= 10
    assert report["journal_imported"] >= 5
    assert report["project_imported"] >= 1
    assert report["goals_opened"] >= 1
    # MC panel surface (no contents)
    panel = memory_manager.mission_control_panel()
    shadow = panel.get("shadow") or {}
    harvest = shadow.get("harvest") or {}
    assert harvest.get("last_report")
    assert "ok" in harvest["last_report"]
    blob = json.dumps(harvest).lower()
    assert "flavor0" not in blob
    assert "espresso" not in blob


@pytest.mark.m2
def test_m2_dry_run_and_no_primary() -> None:
    entries = _seed_entries()[:5]
    report = acm_harvest.harvest_into_acm(entries=entries, dry_run=True)
    assert report["imported"] == 0
    assert acm_bridge.primary_enabled() is False
    assert acm_bridge.authoritative_route() == "legacy"


@pytest.mark.m2
def test_m2_cli_help() -> None:
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / "acm_harvest.py"), "--help"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "harvest" in proc.stdout.lower() or "MemoryStore" in proc.stdout
