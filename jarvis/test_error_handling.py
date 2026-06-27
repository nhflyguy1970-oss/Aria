"""Tests for error handling helpers."""

from __future__ import annotations

import logging

import pytest


def test_user_message_truncates_long_errors():
    from jarvis.error_handling import user_message

    exc = RuntimeError("x" * 400)
    msg = user_message(exc, fallback="Failed.")
    assert len(msg) < 320
    assert "Failed." in msg


def test_assistant_error_includes_reference_id(monkeypatch):
    monkeypatch.setattr("jarvis.error_handling.new_error_id", lambda: "deadbeef")
    from jarvis.error_handling import assistant_error

    result = assistant_error(RuntimeError("boom"), action="chat", message="hi")
    assert result["ok"] is False
    assert result["error_id"] == "deadbeef"
    assert "deadbeef" in result["message"]


def test_report_error_writes_action_log(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.error_handling.new_error_id", lambda: "cafebabe")
    from jarvis.action_log import list_actions
    from jarvis.error_handling import report_error

    log = logging.getLogger("jarvis.test.errors")
    eid = report_error(log, ValueError("bad value"), action="test", module="unit", detail="ctx")
    assert eid == "cafebabe"
    rows = list_actions(limit=5)
    assert any(r.get("event") == "error" and r.get("error_id") == "cafebabe" for r in rows)


def test_api_error_payload_debug_detail(monkeypatch):
    monkeypatch.setenv("JARVIS_DEBUG", "1")
    from jarvis.error_handling import api_error_payload

    payload = api_error_payload(RuntimeError("kaboom"), request_path="/api/foo", include_detail=True)
    assert payload["ok"] is False
    assert payload["error_id"]
    assert "detail" in payload
