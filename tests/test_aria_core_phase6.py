"""Phase 6 — Cognitive Orchestrator coordinates Cap Bus without organ moves."""

from __future__ import annotations

from pathlib import Path

from aria_core.capability_bus import plan, reference
from aria_core.cognition import (
    COGNITION_VERSION,
    mission_control_panel,
    participation_for,
    recent_pipelines,
)
from aria_core.cognitive_orchestrator import reset_for_tests
from aria_core.event_bus import get_bus, recent_events
from aria_core.event_contracts import validate_contracts
from aria_core.ownership import OWNERSHIP


def setup_function():
    reset_for_tests()
    get_bus().reset_for_tests()


def test_cognition_owned():
    assert OWNERSHIP["cognition"]["owner"] == "aria_core.cognition"
    assert "orchestrator" in OWNERSHIP["cognition"]["implementation"]


def test_participation_passthrough_policy():
    plan_part = participation_for("plan")
    assert plan_part["selected"] == ["planning"]
    assert "memory" in plan_part["skipped"]
    assert plan_part["request_event"] == "PlanningRequested"
    mem = participation_for("remember")
    assert mem["selected"] == ["memory"]
    assert mem["request_event"] == "MemoryRequested"


def test_cap_bus_goes_through_orchestrator():
    status = plan(action="status")
    assert status.get("ok") is True
    reference("phase6 cognition")
    pipes = recent_pipelines(limit=10)
    assert pipes
    caps = {p["capability"] for p in pipes}
    assert "plan" in caps
    assert "reference" in caps
    names = {e["name"] for e in recent_events(limit=80)}
    assert "CognitionStarted" in names
    assert "CognitionCompleted" in names
    assert "CapabilitySelected" in names
    assert "CapabilitySkipped" in names
    assert "PlanningRequested" in names
    assert "ReferenceRequested" in names


def test_orchestrator_preserves_plan_result():
    out = plan(action="status")
    assert "available" in out
    assert out.get("owner")


def test_mission_control_panel():
    plan(action="status")
    panel = mission_control_panel(limit=20)
    assert panel["title"] == "Aria Core Cognition"
    assert panel["version"] == COGNITION_VERSION
    assert "pipelines" in panel
    assert "statistics" in panel


def test_event_contracts_include_cognition():
    assert validate_contracts() == []


def test_phase6_docs_exist():
    root = Path(__file__).resolve().parents[1] / "docs" / "aria_core"
    for name in ("PHASE6.md", "COGNITION.md"):
        assert (root / name).is_file(), name
