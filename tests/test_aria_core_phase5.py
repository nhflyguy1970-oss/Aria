"""Phase 5 — Learning owned by Aria Core; passthrough unchanged."""

from __future__ import annotations

from pathlib import Path

from aria_core.event_bus import get_bus, recent_events
from aria_core.event_contracts import validate_contracts
from aria_core.learning import (
    approve_learning,
    commit_learning,
    learning_history,
    learning_statistics,
    mission_control_panel,
    propose_learning,
    reject_learning,
    replay_learning,
)
from aria_core.learning_contracts import PROPOSAL_FIELDS, validate_history_record
from aria_core.learning_manager import reset_for_tests
from aria_core.ownership import OWNERSHIP


def setup_function():
    reset_for_tests()
    get_bus().reset_for_tests()


def test_learning_owned_by_core():
    assert OWNERSHIP["learning"]["source_of_truth"] == "aria_core.learning_manager"
    assert "aria_core.learning_manager" in OWNERSHIP["learning"]["implementation"]


def test_shim_matches_core_passthrough():
    import jarvis.learning_governor as lg
    from aria_core import learning_manager as mgr

    assert lg.propose is mgr.propose
    assert lg.commit is mgr.commit
    calls = []
    out = lg.commit(
        lg.propose(kind="phase5", payload={"x": 1}, source="test"),
        lambda: calls.append(1) or {"ok": True},
    )
    assert out == {"ok": True}
    assert calls == [1]


def test_core_api_and_history_contract():
    p = propose_learning(
        kind="phase5", payload={"a": 1}, source="unit", reason="test", confidence=0.9
    )
    out = commit_learning(p, lambda: {"wrote": True})
    assert out == {"wrote": True}
    hist = learning_history(limit=10)
    assert hist
    assert hist[-1]["decision"] == "accepted"
    assert validate_history_record(hist[-1]) == []
    for field in ("origin", "capability", "decision", "events_published"):
        assert field in PROPOSAL_FIELDS
    stats = learning_statistics()
    assert stats["accepted"] >= 1
    names = {e["name"] for e in recent_events(limit=20)}
    assert "LearningProposed" in names
    assert "LearningAccepted" in names
    assert "LearningCommitted" in names


def test_approve_reject_replay():
    p = propose_learning(kind="reject-me", payload={}, source="unit")
    rejected = reject_learning(p, reason="nope")
    assert rejected["ok"] is True
    assert rejected["record"]["decision"] == "rejected"

    p2 = propose_learning(kind="approve-me", payload={}, source="unit")
    assert approve_learning(p2, lambda: "done") == "done"
    replay = replay_learning(p2.proposal_id)
    assert replay["ok"] is True
    assert replay["replayed"] is True
    names = {e["name"] for e in recent_events(limit=30)}
    assert "LearningRejected" in names
    assert "LearningReplayed" in names


def test_mission_control_panel():
    propose_learning(kind="mc", payload={}, source="panel")
    panel = mission_control_panel(limit=20)
    assert panel["owner"] == "aria_core.learning"
    assert "statistics" in panel
    assert "proposals" in panel
    assert "health" in panel


def test_event_contracts_include_new_learning_events():
    assert validate_contracts() == []


def test_phase5_docs_exist():
    root = Path(__file__).resolve().parents[1] / "docs" / "aria_core"
    for name in ("PHASE5.md", "LEARNING.md"):
        assert (root / name).is_file(), name
