"""Phase 4 — Event Bus publish/subscribe without behavior change."""

from __future__ import annotations

from pathlib import Path

from aria_core.event_bus import get_bus, mission_control_panel, recent_events, subscribe
from aria_core.event_contracts import validate_contracts
from aria_core.event_types import ALL_EVENT_TYPES, LearningAccepted, LearningProposed
from aria_core.ownership import OWNERSHIP


def setup_function():
    get_bus().reset_for_tests()


def test_event_contracts_complete():
    assert validate_contracts() == []
    assert len(ALL_EVENT_TYPES) >= 30


def test_events_module_owned():
    assert "events" in OWNERSHIP
    assert OWNERSHIP["events"]["owner"] == "aria_core.events"


def test_publish_subscribe_and_ring():
    seen: list[str] = []

    def handler(event):
        seen.append(event.name)

    subscribe("*", handler)
    from jarvis.learning_governor import commit, propose

    commit(propose(kind="phase4", payload={"a": 1}, source="test"), lambda: {"ok": True})
    assert LearningProposed in seen
    assert LearningAccepted in seen
    names = [e["name"] for e in recent_events(limit=20)]
    assert LearningProposed in names
    assert LearningAccepted in names


def test_capability_bus_publishes_reference():
    from aria_core.capability_bus import plan, reference

    reference("phase4 event bus")
    plan(action="status")
    names = {e["name"] for e in recent_events(limit=50)}
    assert "ReferenceLookup" in names
    assert "PlanStarted" in names
    assert "PlanCompleted" in names


def test_mission_control_panel_shape():
    panel = mission_control_panel(limit=10)
    assert panel["title"] == "Aria Core Event Bus"
    assert "live_events" in panel
    assert "subscribers" in panel
    assert "rates" in panel
    assert "replay" in panel


def test_handler_failure_does_not_break_publish():
    def bad(_event):
        raise RuntimeError("boom")

    subscribe("*", bad)
    from aria_core.event_bus import safe_publish

    safe_publish("MemoryUpdated", source="test", entry_id="x")
    assert any(e["name"] == "MemoryUpdated" for e in recent_events(limit=5))


def test_phase4_docs_exist():
    root = Path(__file__).resolve().parents[1] / "docs" / "aria_core"
    for name in ("PHASE4.md", "EVENT_BUS.md", "EVENT_CONTRACTS.md"):
        assert (root / name).is_file(), name
