"""Aria Core Learning Contracts (Phase 5)."""

from __future__ import annotations

from typing import Any

CONTRACT_VERSION = "2.0-phase5"

PROPOSAL_FIELDS: tuple[str, ...] = (
    "origin",
    "capability",
    "application",
    "timestamp",
    "reason",
    "confidence",
    "memory_targets",
    "knowledge_targets",
    "expected_impact",
    "decision",
    "duration",
    "events_published",
)

LEARNING_API: dict[str, dict[str, Any]] = {
    "propose_learning": {
        "purpose": "Create a learning proposal",
        "inputs": {
            "kind": "str",
            "payload": "dict?",
            "source": "str?",
            "contract fields": "optional",
        },
        "outputs": {"Proposal": "frozen dataclass"},
        "side_effects": "LearningProposed event + pending history row",
        "version": CONTRACT_VERSION,
    },
    "approve_learning": {
        "purpose": "Approve and immediately commit (Phase 5 = commit)",
        "inputs": {"proposal": "Proposal", "apply": "callable"},
        "outputs": {"apply result": "Any"},
        "side_effects": "writer apply + LearningAccepted + LearningCommitted",
        "version": CONTRACT_VERSION,
    },
    "reject_learning": {
        "purpose": "Reject without applying writer",
        "inputs": {"proposal": "Proposal", "reason": "str?"},
        "outputs": {"ok": "bool", "record": "dict"},
        "side_effects": "LearningRejected event + history",
        "version": CONTRACT_VERSION,
    },
    "commit_learning": {
        "purpose": "Immediate commit via apply()",
        "inputs": {"proposal": "Proposal", "apply": "callable"},
        "outputs": {"apply result": "Any"},
        "side_effects": "identical to Phase 1/4 commit path",
        "version": CONTRACT_VERSION,
    },
    "replay_learning": {
        "purpose": "Re-surface a history record (no organ rewrite)",
        "inputs": {"proposal_id": "str"},
        "outputs": {"record": "dict"},
        "side_effects": "LearningReplayed event",
        "version": CONTRACT_VERSION,
    },
    "learning_history": {
        "purpose": "List Core learning history",
        "inputs": {"limit": "int", "decision": "str?"},
        "outputs": {"records": "list[dict]"},
        "side_effects": "none",
        "version": CONTRACT_VERSION,
    },
    "learning_statistics": {
        "purpose": "Aggregate learning stats for MC",
        "inputs": {},
        "outputs": {"stats": "dict"},
        "side_effects": "none",
        "version": CONTRACT_VERSION,
    },
}


def validate_history_record(rec: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in PROPOSAL_FIELDS:
        # duration stored as duration_ms; timestamp as timestamp
        key = "duration_ms" if field == "duration" else field
        if key not in rec and field != "duration":
            errors.append(f"missing {field}")
        if field == "duration" and "duration_ms" not in rec:
            errors.append("missing duration_ms")
    return errors
