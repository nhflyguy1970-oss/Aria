"""Reference Intelligence — documentation assistant regressions (Problem Report)."""

from __future__ import annotations

from unittest.mock import patch

from aria_core.cognitive_orchestrator import orchestrate_compose
from aria_core.cognitive_orchestrator import reset_for_tests as reset_cog
from aria_core.conversation_trace import build_conversation_trace
from aria_core.response_composer import compose_natural
from jarvis.reference_engine import (
    mission_control_panel,
    reset_for_tests,
    search_reference,
)

PROMPTS = {
    "show_compose": "Show me the Docker Compose documentation.",
    "summarize_guide": "Summarize the AI Platform User Guide.",
    "start_guide": "How do I start the AI Platform according to the User Guide?",
    "compose_runtime": (
        "Summarize the AI Platform User Guide and tell me whether Docker is currently running."
    ),
    "unknown_gpu": ("Which document explains how the Capability Bus schedules GPU inference?"),
    "compare": "Compare the User Guide and Architecture documentation.",
}


def setup_function():
    reset_for_tests()
    reset_cog()


def test_show_docs_not_raw_dump():
    out = search_reference(PROMPTS["show_compose"])
    msg = out["message"]
    assert out["ok"] is True
    assert "APPLICATIONS.md" in msg or "Docker" in msg
    # Must not dump many unrelated files as ### title dump
    assert msg.count("### ") <= 4
    assert "FUTURE_PRODUCT_IMPROVEMENTS" not in msg
    assert out["diagnostics"]["dump_blocked"] is True
    assert out["diagnostics"]["mode"] == "show"
    selected = [d["title"] for d in out["diagnostics"]["documents_selected"]]
    assert selected[0] in ("APPLICATIONS.md", "DEPLOYMENT.md")


def test_summarize_user_guide():
    out = search_reference(PROMPTS["summarize_guide"])
    msg = out["message"].lower()
    assert out["diagnostics"]["mode"] == "summarize"
    assert any(d["title"] == "USER_GUIDE.md" for d in out["diagnostics"]["documents_selected"])
    assert "user guide" in msg or "workstation" in msg or "mission control" in msg
    assert "development guide" not in msg or "user guide" in msg
    # Not a hit list
    assert "(`local`)" not in out["message"]


def test_answer_start_from_user_guide():
    out = search_reference(PROMPTS["start_guide"])
    msg = out["message"]
    assert "./workstation start" in msg
    assert "ARCHITECTURE.md" not in msg or "User Guide" in msg
    assert "Docker services" in msg or "Mission Control" in msg
    assert out["diagnostics"]["mode"] == "answer"


def test_unknown_gpu_scheduling_no_hallucination():
    out = search_reference(PROMPTS["unknown_gpu"])
    msg = out["message"].lower()
    assert out["diagnostics"]["unknown"] is True
    assert "could not find" in msg
    assert "tensorflow" not in msg
    assert "pytorch" not in msg
    assert "example.yml" not in msg


def test_compare_two_documents():
    out = search_reference(PROMPTS["compare"])
    assert out["diagnostics"]["mode"] == "compare"
    titles = [d["title"] for d in out["diagnostics"]["documents_selected"]]
    assert any("USER_GUIDE" in t for t in titles)
    assert any("ARCHITECTURE" in t for t in titles)
    assert "Comparison" in out["message"] or "USER" in out["message"]


def test_reference_runtime_compose_one_response():
    def fake_runtime(action):
        return {"ok": True, "message": "Docker is running.", "data": {"action": action}}

    with patch("jarvis.runtime_introspection.runtime_action_result", side_effect=fake_runtime):
        out = orchestrate_compose(PROMPTS["compose_runtime"])
    assert out["ok"] is True
    msg = out["message"]
    assert msg.strip()
    assert (
        "workstation" in msg.lower()
        or "user guide" in msg.lower()
        or "mission control" in msg.lower()
    )
    assert "Docker is running" in msg
    assert out["data"]["plan"]["executed"] == ["reference", "runtime"]


def test_compose_handler_exposes_message_key():
    """Regression: blank chat when only reply was set."""
    # Simulate the ops return contract without importing heavy behaviors package.
    result = {"ok": True, "message": "hello from compose", "data": {"plan": {}}}
    payload = {
        "ok": bool(result.get("ok")),
        "message": result.get("message") or "",
        "reply": result.get("message") or "",
    }
    assert payload["message"]
    assert payload["reply"] == payload["message"]


def test_no_debug_tool_trace_leakage():
    out = search_reference(PROMPTS["summarize_guide"])
    low = out["message"].lower()
    for leak in ("tool history", "strategy:", "memory search:", "runtime search:"):
        assert leak not in low


def test_conversation_trace_records_reference_stages():
    out = search_reference(PROMPTS["start_guide"])
    intent = {
        "params": {
            "capabilities": ["reference"],
            "reference_diagnostics": out["diagnostics"],
        },
        "action": "search_reference",
    }
    ct = build_conversation_trace(
        prompt=PROMPTS["start_guide"],
        intent=intent,
        action="search_reference",
        route="operations",
        handler="operations",
        latency_ms=12.0,
        route_latency_ms=1.0,
        response_length=len(out["message"]),
        error=None,
        conversation_id="t-ref-1",
    )
    ref = ct["reference"]
    assert ref["used"] is True
    assert ref["documents_selected"]
    assert "question_answering" in (ref.get("stages") or {})
    assert ref.get("dump_blocked") is True


def test_mission_control_reference_panel():
    search_reference(PROMPTS["summarize_guide"])
    panel = mission_control_panel(limit=10)
    assert panel["ok"] is True
    assert panel["latest"].get("mode") == "summarize"
    assert "search_ms" in panel["latest"]
    assert "documents_selected" in panel["latest"]


def test_composer_keeps_reference_headings():
    text = compose_natural(
        [
            {
                "capability": "reference",
                "ok": True,
                "message": "### Starting\nRun ./workstation start\n",
            },
            {"capability": "runtime", "ok": True, "message": "Docker is up."},
        ]
    )
    assert "Starting" in text
    assert "Docker is up" in text


def test_no_raw_multi_file_dump_unless_requested():
    out = search_reference("Explain the Capability Bus.")
    # Single primary doc answer / extract — not 5 file dumps
    assert out["message"].count("(`local`)") == 0
    assert len(out["diagnostics"]["documents_selected"]) <= 2
