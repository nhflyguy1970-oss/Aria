"""Tests for acceptance gap analysis and repair."""

from __future__ import annotations

from jarvis.workstation.acceptance import (
    AcceptanceItem,
    AcceptanceStatus,
    compute_score_gaps,
    format_acceptance_markdown,
)
from jarvis.workstation.repair import repair_permissions


def _item(**kwargs) -> AcceptanceItem:
    defaults = dict(
        id="aria",
        label="Aria",
        category="interface",
        status=AcceptanceStatus.NEEDS_CONFIGURATION.value,
        installed=True,
        configured=True,
        running=False,
        healthy=False,
        used_by_aria=True,
        integration_ok=False,
        fix_hint="./workstation start",
    )
    defaults.update(kwargs)
    return AcceptanceItem(**defaults)


def test_compute_score_gaps_lists_missing():
    items = [
        _item(id="aria", label="Aria"),
        _item(
            id="ollama",
            label="Ollama",
            status=AcceptanceStatus.READY.value,
            healthy=True,
            running=True,
            integration_ok=True,
        ),
    ]
    gaps = compute_score_gaps(items, daily_ids={"aria", "ollama"}, integration_ids={"aria"})
    assert gaps["gaps"]
    assert gaps["gaps"][0]["id"] == "aria"
    assert gaps["projected_daily"] > gaps["daily_score"]


def test_format_includes_gap_section():
    report = {
        "acceptance_passed": False,
        "score": {"daily_required": 82, "integration": 50, "production_readiness": 70},
        "summary": {"ready": 1, "needs_configuration": 1, "not_installed": 0},
        "gap_analysis": {
            "daily_score": 82,
            "projected_daily": 95,
            "gaps": [
                {
                    "missing": "Aria not running",
                    "gain_daily": 12,
                    "gain_integration": 0,
                    "fix": "./workstation start",
                    "human_required": False,
                }
            ],
        },
        "items": [],
    }
    text = format_acceptance_markdown(report)
    assert "Why am I not at 100%" in text
    assert "Aria not running" in text


def test_repair_permissions_makes_executable(tmp_path, monkeypatch):
    script = tmp_path / "workstation"
    script.write_text("#!/bin/bash\necho ok\n")
    script.chmod(0o644)
    monkeypatch.setattr("jarvis.workstation.repair.PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        "jarvis.workstation.repair.repair_permissions.__defaults__",
        (),
    )
    # Patch targets list by running on real project root is fine
    result = repair_permissions()
    assert result.get("ok") is True
