"""Phase 1 foundation: production isolation, cancellation classification, activity channels."""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.integrity_product.tags import looks_like_dev_label
from jarvis.production_guard import (
    ProductionIsolationError,
    assert_environment_consistent,
    assert_owner_write_allowed,
    is_production_workspace,
    looks_like_test_payload,
    reject_live_test_request,
)


def test_dev_labels_catch_harness_tokens():
    for text in (
        "ARIA-REPAIR-E2E-PLAN-1786468681142",
        "ARIA-FINAL-PLAN-1786473674",
        "AUDIT-ROOM-1786504544420",
        "ARIA-REPAIR-E2E-JRN-1786468686109",
        "oc-cert-project-596282",
        "P64TestMed",
        "P64Verify",
        "cert-mood",
        "wf_probe",
        "Phase 7 residency — buy tippet 5X",
        "FNACCEPT DOC 1786464952056",
        "xyzzyqqq999nope",
    ):
        assert looks_like_dev_label(text), text
        assert looks_like_test_payload(text), text


def test_owner_labels_are_not_test_payloads():
    for text in (
        "pick up wool yarn for fly tying",
        "Vitamin D3",
        "Buy milk",
        "Tie an Adams",
        "Jeff prefers evening fly tying",
    ):
        assert not looks_like_dev_label(text), text


def test_isolated_data_dir_is_not_production(monkeypatch, tmp_path):
    import jarvis.config as config
    import jarvis.production_guard as guard

    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setenv("JARVIS_ENVIRONMENT", "qa")
    assert is_production_workspace() is False
    assert_environment_consistent()
    assert_owner_write_allowed("ARIA-REPAIR-E2E-PLAN-1", store="planner")


def test_test_environment_cannot_use_live_data(monkeypatch):
    import jarvis.config as config
    import jarvis.production_guard as guard

    monkeypatch.setattr(config, "DATA_DIR", guard.LIVE_DATA_ROOT)
    monkeypatch.setenv("JARVIS_ENVIRONMENT", "certification")
    with pytest.raises(ProductionIsolationError):
        assert_environment_consistent()


def test_production_rejects_test_shaped_writes(monkeypatch):
    import jarvis.config as config
    import jarvis.production_guard as guard
    from jarvis.live_data_guard import disable_test_guard, enable_test_guard

    monkeypatch.setattr(config, "DATA_DIR", guard.LIVE_DATA_ROOT)
    monkeypatch.setenv("JARVIS_ENVIRONMENT", "production")
    disable_test_guard()
    try:
        with pytest.raises(ProductionIsolationError):
            assert_owner_write_allowed("ARIA-REPAIR-E2E-PLAN-1786468681142", store="planner")
        assert_owner_write_allowed("Tie an Adams dry fly", store="planner")
    finally:
        enable_test_guard()


def test_qa_headers_rejected_on_live_workspace(monkeypatch):
    import jarvis.config as config
    import jarvis.production_guard as guard

    monkeypatch.setattr(config, "DATA_DIR", guard.LIVE_DATA_ROOT)
    monkeypatch.delenv("JARVIS_ENVIRONMENT", raising=False)
    msg = reject_live_test_request("POST", {"X-Aria-QA-Run": "e2e"})
    assert msg
    assert reject_live_test_request("GET", {"X-Aria-QA-Run": "e2e"}) is None
    assert reject_live_test_request("POST", {}) is None


def test_activity_classifies_cancellation_and_engineering():
    from jarvis.activity_inbox import classify_channel, is_cancellation_event

    assert is_cancellation_event("Failed to load memes — aria-room-leave", "")
    assert is_cancellation_event("", "The operation was aborted")
    assert classify_channel("Failed to load memes — aria-room-leave", "", "toast") == "cancelled"
    assert classify_channel("Could not load audio status.", "", "toast") == "engineering"
    assert classify_channel("Mission Control · critical health", "degraded", "mission") == "engineering"
    assert classify_channel("ARIA-REPAIR-E2E-PLAN-1 created", "", "planner") == "development"
    assert is_cancellation_event("", "Could not reach cancel API — stream aborted locally")
    assert classify_channel("Could not reach cancel API — stream aborted locally", "", "toast") == "cancelled"
    assert classify_channel("Voice settings save failed", "", "toast") == "engineering"
    assert classify_channel("Chat failure", "Another request is still finishing. Stop it or wait a moment.", "chat") == "engineering"
    assert classify_channel("Kasa unavailable", "", "toast") == "owner"
    assert classify_channel("Missed: Work", "Scheduled 08:30", "calendar") == "owner"
    assert classify_channel("Not Found", "Not Found", "toast") == "engineering"


def test_live_projects_root_rejects_qa_create(monkeypatch, tmp_path):
    from jarvis.production_guard import LIVE_DATA_ROOT, ProductionIsolationError
    import jarvis.project_registry as pr

    monkeypatch.setattr(pr, "PROJECTS_ROOT", LIVE_DATA_ROOT / "projects")
    with pytest.raises(ProductionIsolationError):
        pr.create_project("oc-cert-project-999")


def test_activity_publish_drops_cancellations(tmp_path, monkeypatch):
    import jarvis.activity_inbox as inbox

    monkeypatch.setattr(inbox, "INBOX_DIR", tmp_path)
    monkeypatch.setattr(inbox, "INBOX_FILE", tmp_path / "inbox.jsonl")
    out = inbox.publish(kind="error", title="Failed to load memes — aria-room-leave", source="toast")
    assert out.get("rejected") is True
    assert out.get("reason") == "cancelled"
    listed = inbox.list_items()
    assert listed["items"] == []
    assert listed["unread"] == 0


def test_activity_owner_list_hides_engineering(tmp_path, monkeypatch):
    import jarvis.activity_inbox as inbox

    monkeypatch.setattr(inbox, "INBOX_DIR", tmp_path)
    monkeypatch.setattr(inbox, "INBOX_FILE", tmp_path / "inbox.jsonl")
    inbox.publish(kind="error", title="Could not load audio status.", source="toast")
    inbox.publish(kind="info", title="Planner item created", body="Tie an Adams", source="planner")
    owner = inbox.list_items()
    assert [i["title"] for i in owner["items"]] == ["Planner item created"]
    eng = inbox.list_items(channel="engineering")
    assert any("audio" in i["title"].lower() for i in eng["items"])


def test_aria_net_classifies_room_leave():
    host = Path("jarvis/gui/static/workspace/rooms/house_host.js").read_text(encoding="utf-8")
    assert 'err.kind = "room-leave"' in host
    assert "err.ownerVisible = false" in host
    assert 'new DOMException("", "AbortError")' in host
    center = Path("jarvis/gui/static/activity_center.js").read_text(encoding="utf-8")
    assert "isRoomAbort" in center
    assert "return orig.apply" in center
    # Cancellation must not surface as a toast.
    assert "if (window.AriaNet?.isRoomAbort?.(msg) ||" in center or "AriaNet?.isRoomAbort" in center
    meme = Path("jarvis/gui/static/meme_studio.js").read_text(encoding="utf-8")
    assert "isRoomAbort" in meme
    conn = Path("jarvis/gui/static/connections.js").read_text(encoding="utf-8")
    assert "isRoomAbort" in conn


def test_owner_snapshot_does_not_include_qa_by_default():
    src = Path("jarvis/planner_store.py").read_text(encoding="utf-8")
    snap = src.split("def planner_snapshot")[1].split("def format_planner_lines")[0]
    assert "tasks\": list_tasks(include_qa=False)" in snap.replace(" ", "") or 'list_tasks(include_qa=False)' in snap
    assert "list_tasks(include_qa=True)" not in "".join(
        line for line in snap.splitlines() if "scans use" not in line
    )
    routes = Path("jarvis/gui/extra_routes.py").read_text(encoding="utf-8")
    assert "include_qa=True" not in routes.split("def journal_daily")[1].split("def journal_daily_add")[0]
