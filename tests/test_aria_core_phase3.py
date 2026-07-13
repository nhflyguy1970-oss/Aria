"""Phase 3 — Capability Bus, registry, contracts (no organ moves)."""

from __future__ import annotations

from pathlib import Path

from aria_core.capabilities import capability_interface, list_bus_verbs
from aria_core.capability_bus import (
    BUS_VERSION,
    health,
    learn,
    mission_control_panel,
    plan,
    reference,
    schedule,
)
from aria_core.capability_contracts import validate_contracts
from aria_core.capability_registry import (
    all_capability_ids,
    required_fields,
    validate_registry,
)

EXPECTED_VERBS = {
    "remember",
    "recall",
    "learn",
    "reason",
    "plan",
    "reference",
    "search",
    "infer",
    "execute_tool",
    "schedule",
    "observe",
    "notify",
    "diagnose",
    "repair",
    "backup",
    "recover",
}


def test_registry_complete_and_valid():
    assert EXPECTED_VERBS <= set(all_capability_ids())
    assert validate_registry() == []
    for cid in all_capability_ids():
        from aria_core.capability_registry import get_capability

        rec = get_capability(cid)
        assert rec is not None
        assert set(required_fields()) <= set(rec.keys())


def test_contracts_cover_all_verbs():
    assert validate_contracts() == []


def test_bus_health_probes_without_side_effects():
    snap = health()
    assert snap["total"] == len(EXPECTED_VERBS)
    assert snap["version"] == BUS_VERSION
    assert isinstance(snap["capabilities"], list)


def test_learn_and_plan_and_reference_delegate():
    calls = []

    def apply():
        calls.append(1)
        return {"ok": True}

    out = learn(kind="phase3", payload={}, apply=apply)
    assert out == {"ok": True}
    assert calls == [1]

    status = plan(action="status")
    assert status.get("ok") is True
    assert "available" in status

    result = reference("Aria Core Capability Bus")
    assert isinstance(result, dict)


def test_schedule_status_is_observational():
    data = schedule(op="status")
    assert data.get("ok") is True
    assert "jobs" in data or "queues" in data


def test_mission_control_panel_shape():
    panel = mission_control_panel()
    assert panel.get("title")
    assert panel.get("dependency_graph")
    assert len(panel.get("capabilities") or []) >= len(EXPECTED_VERBS)
    ids = {c["id"] for c in panel["capabilities"]}
    assert EXPECTED_VERBS <= ids


def test_application_capability_interface_pointer():
    iface = capability_interface()
    assert iface["bus"] == "aria_core.capability_bus"
    assert set(list_bus_verbs()) == EXPECTED_VERBS


def test_phase3_docs_exist():
    root = Path(__file__).resolve().parents[1] / "docs" / "aria_core"
    for name in (
        "PHASE3.md",
        "CAPABILITY_BUS.md",
        "CAPABILITY_CONTRACTS.md",
        "ARIA_CORE_API.md",
    ):
        assert (root / name).is_file(), name
