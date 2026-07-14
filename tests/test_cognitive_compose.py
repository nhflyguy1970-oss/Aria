"""Multi-capability Cognitive Orchestrator composition regressions."""

from __future__ import annotations

from unittest.mock import patch

from aria_core.cognitive_orchestrator import (
    mission_control_panel,
    orchestrate_compose,
    recent_pipelines,
    reset_for_tests,
)
from aria_core.request_plan import build_request_plan
from aria_core.response_composer import compose_natural

PROMPTS = {
    "ref_runtime_docker": (
        "Show me the Docker Compose documentation and tell me whether Docker is currently running."
    ),
    "ref_runtime_mc": (
        "Explain the AI Platform architecture and tell me whether Mission Control is healthy."
    ),
    "ref_runtime_bus": ("Explain the Capability Bus and tell me if it is operating normally."),
    "ref_runtime_apps": (
        "Show me the User Guide and tell me what applications are currently running."
    ),
    "ref_memory": ("Show me the User Guide and tell me what you remember about me."),
    "runtime_memory": ("Tell me what services are running and what you remember about me."),
    "docs_advisor": ("Show me the documentation and tell me what needs attention."),
}


def setup_function():
    reset_for_tests()


def test_plans_select_multiple_capabilities():
    plan = build_request_plan(PROMPTS["ref_runtime_docker"])
    assert plan["combine"] is True
    assert plan["selected"] == ["reference", "runtime"]
    assert plan["execution_order"][-1] == "composer"
    assert plan["runtime_action"] == "runtime_services"

    plan2 = build_request_plan(PROMPTS["ref_runtime_apps"])
    assert "reference" in plan2["selected"] and "runtime" in plan2["selected"]
    assert plan2["runtime_action"] == "runtime_applications"

    plan3 = build_request_plan(PROMPTS["ref_runtime_bus"])
    assert plan3["architectural"] is True


def test_composer_keeps_success_when_one_fails():
    text = compose_natural(
        [
            {"capability": "reference", "ok": True, "message": "Docs about Compose."},
            {"capability": "runtime", "ok": False, "error": "Mission Control unavailable"},
        ]
    )
    assert "Docs about Compose" in text
    assert "could not be retrieved" in text
    assert "----------------" not in text


def test_orchestrate_compose_includes_all_outputs():
    def fake_ref(query, subject=""):
        return {"ok": True, "message": f"REFERENCE:{query}", "data": {}}

    def fake_runtime(action):
        return {"ok": True, "message": f"RUNTIME:{action}", "data": {}}

    with (
        patch("jarvis.reference_engine.search_reference", side_effect=fake_ref),
        patch("jarvis.runtime_introspection.runtime_action_result", side_effect=fake_runtime),
    ):
        out = orchestrate_compose(PROMPTS["ref_runtime_docker"])
    assert out["ok"] is True
    assert "REFERENCE:" in out["message"]
    assert "RUNTIME:runtime_services" in out["message"]
    plan = out["data"]["plan"]
    assert plan["executed"] == ["reference", "runtime"]
    assert "composer" in plan["execution_plan_display"]

    pipes = recent_pipelines(limit=5)
    assert pipes and pipes[-1]["capability"] == "compose"
    assert pipes[-1]["decision_metadata"]["combine"] is True


def test_architecture_plus_runtime_and_apps():
    def fake_ref(query, subject=""):
        return {"ok": True, "message": "ARCH_DOCS", "data": {}}

    def fake_runtime(action):
        return {"ok": True, "message": f"LIVE:{action}", "data": {}}

    with (
        patch("jarvis.reference_engine.search_reference", side_effect=fake_ref),
        patch("jarvis.runtime_introspection.runtime_action_result", side_effect=fake_runtime),
    ):
        mc = orchestrate_compose(PROMPTS["ref_runtime_mc"])
        apps = orchestrate_compose(PROMPTS["ref_runtime_apps"])
        bus = orchestrate_compose(PROMPTS["ref_runtime_bus"])

    assert "ARCH_DOCS" in mc["message"] and "LIVE:runtime_health" in mc["message"]
    assert "ARCH_DOCS" in apps["message"] and "LIVE:runtime_applications" in apps["message"]
    assert "ARCH_DOCS" in bus["message"]
    assert "architectural component" in bus["message"].lower()


def test_reference_memory_and_runtime_memory():
    def fake_ref(query, subject=""):
        return {"ok": True, "message": "GUIDE", "data": {}}

    def fake_runtime(action):
        return {"ok": True, "message": f"LIVE:{action}", "data": {}}

    def fake_mem(query, limit=5, namespace=None):
        return [{"text": "User likes concise answers"}]

    with (
        patch("jarvis.reference_engine.search_reference", side_effect=fake_ref),
        patch("jarvis.runtime_introspection.runtime_action_result", side_effect=fake_runtime),
        patch("aria_core.memory.search_memory", side_effect=fake_mem),
    ):
        ref_mem = orchestrate_compose(PROMPTS["ref_memory"])
        run_mem = orchestrate_compose(PROMPTS["runtime_memory"])
        adv = orchestrate_compose(PROMPTS["docs_advisor"])

    assert "GUIDE" in ref_mem["message"] and "concise answers" in ref_mem["message"]
    assert "LIVE:" in run_mem["message"] and "concise answers" in run_mem["message"]
    assert "GUIDE" in adv["message"] and "LIVE:runtime_attention" in adv["message"]


def test_router_routes_compound_to_cognitive_compose():
    from jarvis.router import route
    from jarvis.session import SessionContext

    session = SessionContext()
    for key in ("ref_runtime_docker", "ref_runtime_mc", "ref_runtime_bus", "ref_runtime_apps"):
        intent = route(PROMPTS[key], session, None)
        assert intent["action"] == "cognitive_compose", (key, intent.get("action"))
        assert intent.get("route_handler") == "CognitiveOrchestrator"
        caps = intent.get("params", {}).get("capabilities") or []
        assert "reference" in caps and "runtime" in caps


def test_mission_control_shows_execution_plan():
    def fake_ref(query, subject=""):
        return {"ok": True, "message": "DOC", "data": {}}

    def fake_runtime(action):
        return {"ok": True, "message": "RUN", "data": {}}

    with (
        patch("jarvis.reference_engine.search_reference", side_effect=fake_ref),
        patch("jarvis.runtime_introspection.runtime_action_result", side_effect=fake_runtime),
    ):
        orchestrate_compose(PROMPTS["ref_runtime_docker"])
    panel = mission_control_panel(limit=10)
    assert panel["latest_execution_plan"]
    assert "composer" in panel["latest_execution_plan"]
    assert panel["health"]["policy"] == "compose-when-multi"


def test_soft_failure_keeps_reference():
    def fake_ref(query, subject=""):
        return {"ok": True, "message": "STILL_HERE", "data": {}}

    def boom(action):
        raise RuntimeError("mc down")

    with (
        patch("jarvis.reference_engine.search_reference", side_effect=fake_ref),
        patch("jarvis.runtime_introspection.runtime_action_result", side_effect=boom),
    ):
        out = orchestrate_compose(PROMPTS["ref_runtime_docker"])
    assert out["ok"] is True
    assert "STILL_HERE" in out["message"]
    assert "could not be retrieved" in out["message"]
