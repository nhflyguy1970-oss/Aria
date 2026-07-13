"""Phase 1 — Behavioral Compatibility Contract completeness."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "aria_core" / "BEHAVIORAL_CONTRACT.json"
INVENTORY = ROOT / "docs" / "aria_core" / "CAPABILITY_INVENTORY.md"

REQUIRED = {
    "id",
    "layer",
    "name",
    "user_visible_behavior",
    "expected_inputs",
    "expected_outputs",
    "external_apis",
    "cli_behavior",
    "gui_behavior",
    "runtime_behavior",
    "failure_behavior",
    "recovery_behavior",
    "existing_regression_tests",
    "smoke_coverage",
    "owner",
    "jeff_would_notice",
    "protected",
}

MUST_EXIST = {
    "chat-assistant",
    "aria-uncensored",
    "nlu-routing",
    "memory-hierarchy",
    "knowledge-rag",
    "learning-sources",
    "gui-8765",
    "mc-server",
    "mc-desktop",
    "cli-aria-workstation",
    "backup-restore-repair-aria",
    "mc-production-smoke",
}


def test_contract_file_exists():
    assert CONTRACT.is_file()
    assert INVENTORY.is_file()


def test_contract_profiles_and_fields():
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert "standard" in data["profiles"]
    assert "uncensored" in data["profiles"]
    caps = data["capabilities"]
    assert data["capability_count"] == len(caps) >= 90
    ids = []
    inv = INVENTORY.read_text(encoding="utf-8")
    for cap in caps:
        ids.append(cap["id"])
        assert REQUIRED <= set(cap.keys()), cap.get("id")
        assert isinstance(cap["jeff_would_notice"], bool)
        assert isinstance(cap["protected"], bool)
        if cap["protected"]:
            assert f"`{cap['id']}`" in inv
    assert len(ids) == len(set(ids))
    for required in MUST_EXIST:
        assert required in ids


def test_inventory_mentions_uncensored_profile():
    text = INVENTORY.read_text(encoding="utf-8").lower()
    assert "uncensored" in text
