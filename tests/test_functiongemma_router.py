"""FunctionGemma router tests (P1 #23)."""

from __future__ import annotations


def test_parse_function_call_timer():
    from jarvis.functiongemma_router import parse_function_call

    raw = "<start_function_call>call:planner_set_timer{duration: 10 minutes}<end_function_call>"
    data = parse_function_call(raw)
    assert data is not None
    assert data["action"] == "planner_set_timer"
    assert data["params"].get("duration") == "10 minutes"


def test_parse_function_call_thinking():
    from jarvis.functiongemma_router import parse_function_call

    data = parse_function_call("<start_function_call>call:thinking{}<end_function_call>")
    assert data["action"] == "chat"
    assert data["params"].get("thinking_mode") == "deep"


def test_build_tool_schemas():
    from jarvis.functiongemma_router import build_tool_schemas

    schemas = build_tool_schemas(limit=20)
    names = {s["function"]["name"] for s in schemas}
    assert "planner_set_timer" in names
    assert "chat" in names


def test_try_functiongemma_route_mock(monkeypatch):
    from jarvis.functiongemma_router import try_functiongemma_route
    from jarvis.session import SessionContext

    monkeypatch.setenv("JARVIS_LOCAL_ROUTER", "1")
    monkeypatch.setattr(
        "jarvis.functiongemma_router._load_hf",
        lambda: True,
    )
    monkeypatch.setattr(
        "jarvis.functiongemma_router._generate_hf",
        lambda _msg, _tools: "<start_function_call>call:planner_today{}<end_function_call>",
    )

    hit = try_functiongemma_route("what's on my planner today", SessionContext())
    assert hit is not None
    assert hit["action"] == "planner_today"
    assert hit["router"] == "functiongemma"


def test_local_router_auto_fallback(monkeypatch):
    from jarvis.local_router import try_local_route
    from jarvis.session import SessionContext

    monkeypatch.setenv("JARVIS_LOCAL_ROUTER", "1")
    monkeypatch.setenv("JARVIS_ROUTER_BACKEND", "auto")
    monkeypatch.setattr(
        "jarvis.functiongemma_router.try_functiongemma_route",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        "jarvis.llm.ask_with_system",
        lambda *_a, **_k: '{"action":"chat","params":{},"thinking":"chat"}',
    )

    hit = try_local_route("hello", SessionContext())
    assert hit is not None
    assert hit["router"] == "local"


def test_export_functiongemma_jsonl(tmp_path, monkeypatch):
    out = tmp_path / "fg.jsonl"
    monkeypatch.setattr("jarvis.router_training.FG_OUT", out)
    from jarvis.router_training import export_functiongemma_jsonl

    path = export_functiongemma_jsonl()
    assert path.exists()
    assert path.read_text(encoding="utf-8").strip()
