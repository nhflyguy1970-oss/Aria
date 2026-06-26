"""Phase 3 — platform & extensibility tests."""

import pytest


def test_action_registry_meta_handlers():
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import all_actions, get_spec, has_action

    ensure_handlers_loaded()
    assert has_action("greeting")
    assert has_action("git_status")
    assert has_action("generate_image")
    spec = get_spec("generate_image")
    assert spec and spec.queue == "media"
    names = {a["action"] for a in all_actions()}
    assert "journal_today" in names
    assert "clear" in names


def test_router_table_greeting():
    from jarvis.router_table import match_router_table
    from jarvis.session import SessionContext

    hit = match_router_table("hello", SessionContext())
    assert hit and hit["action"] == "greeting"


def test_router_table_clear():
    from jarvis.router_table import match_router_table
    from jarvis.session import SessionContext

    hit = match_router_table("clear", SessionContext())
    assert hit and hit["action"] == "clear"


def test_route_uses_table_before_legacy(assistant):
    from jarvis.router import route
    from jarvis.session import SessionContext

    intent = route("git status", SessionContext())
    assert intent["action"] == "git_status"


def test_registry_dispatch_greeting(assistant):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    out = call_action(assistant, "greeting", {}, "hi")
    assert out["ok"] is True
    assert out.get("type") == "info"


def test_job_framework_media_stats():
    from jarvis.job_framework import stats

    data = stats("media")
    assert "busy" in data
    assert "pending" in data


def test_event_bus():
    from jarvis.events import emit, on

    seen = []

    @on("test_phase3")
    def _handler(**kw):
        seen.append(kw.get("value"))

    emit("test_phase3", value=42)
    assert seen == [42]


def test_api_actions_route(chat_app):
    from jarvis.handlers import ensure_handlers_loaded

    ensure_handlers_loaded()
    res = chat_app.get("/api/registry/actions")
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert any(a["action"] == "capabilities" for a in body["actions"])


def test_api_router_rules_route(chat_app):
    res = chat_app.get("/api/registry/router/rules")
    assert res.status_code == 200
    rules = res.json()["rules"]
    assert any(r["action"] == "clear" for r in rules)
