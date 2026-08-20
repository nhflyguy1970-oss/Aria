"""Tool confirmation — the user's approval control, over HTTP and by voice."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from jarvis.handlers.registry import register_action
from jarvis.response import ok
from jarvis.tool_permissions import create_pending, execute_confirm, list_pending


@pytest.fixture
def confirm_app(data_dir):
    from jarvis.extensions.planner.api import register_routes

    app = FastAPI()
    register_routes(app, MagicMock())
    return TestClient(app)


@register_action("test_confirmed_tool", module="general", description="probe")
def _probe(assistant, params, message):
    return ok("ran", module="general", confirmed=bool(params.get("_confirmed")))


def _pending(data_dir) -> str:
    return create_pending("probe", "test_confirmed_tool", {"x": 1}, "run the probe")


def test_approving_a_tool_actually_runs_it(confirm_app, data_dir):
    """The route called assistant.dispatch(), which does not exist — approving
    a tool raised AttributeError instead of running it."""
    confirm_id = _pending(data_dir)
    r = confirm_app.post("/api/tool-confirm", json={"id": confirm_id, "approved": True})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True and body["approved"] is True
    assert body["result"]["ok"] is True
    assert body["result"]["confirmed"] is True, "the run was not marked as confirmed"


def test_declining_a_tool_does_not_run_it(confirm_app, data_dir):
    confirm_id = _pending(data_dir)
    body = confirm_app.post("/api/tool-confirm", json={"id": confirm_id, "approved": False}).json()
    assert body["ok"] is True and body["approved"] is False
    assert not list_pending(), "a declined confirmation must not stay pending"


def test_an_expired_confirmation_is_404(confirm_app, data_dir):
    r = confirm_app.post("/api/tool-confirm", json={"id": "nope", "approved": True})
    assert r.status_code == 404


def test_unknown_confirmed_action_is_reported_not_executed(confirm_app, data_dir):
    confirm_id = create_pending("probe", "no_such_action_at_all", {}, "x")
    body = confirm_app.post("/api/tool-confirm", json={"id": confirm_id, "approved": True}).json()
    assert body["ok"] is False
    assert "Unknown confirmed action" in body["message"]


def test_voice_and_web_share_one_implementation(data_dir):
    """Two copies of this logic is how the web one drifted into calling a
    method that does not exist."""
    from jarvis import voice_only

    confirm_id = _pending(data_dir)
    result = voice_only._execute_confirm(confirm_id, True, assistant=MagicMock())
    assert result["ok"] is True and result["confirmed"] is True

    source = __import__("pathlib").Path("jarvis/voice_only.py").read_text(encoding="utf-8")
    assert "execute_confirm" in source
    assert "pop_pending" not in source, "voice grew a second copy again"


def test_execute_confirm_envelope_states(data_dir):
    assert execute_confirm("missing", True, assistant=MagicMock())["status"] == "expired"
    confirm_id = _pending(data_dir)
    assert execute_confirm(confirm_id, False, assistant=MagicMock())["status"] == "declined"
