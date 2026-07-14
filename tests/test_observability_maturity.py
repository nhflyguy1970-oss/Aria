"""Observability maturity — metadata only, no behavior changes."""

from __future__ import annotations

from unittest.mock import patch

from aria_core.cognitive_orchestrator import orchestrate_compose, reset_for_tests
from aria_core.observability import (
    capability_health_snapshot,
    capability_plan_view,
    cross_capability_analytics,
    mission_control_panel,
    section_confidence,
    section_provenance,
)


def setup_function():
    reset_for_tests()


def test_capability_plan_waterfall_and_stages():
    view = capability_plan_view(
        {
            "selected": ["reference", "runtime"],
            "executed": ["reference", "runtime"],
            "skipped": ["memory"],
            "failed": [],
            "combine": True,
        },
        action="cognitive_compose",
    )
    assert "Capability Plan" in view["waterfall"]
    assert "✓ Reference" in view["waterfall"]
    assert "✗ Memory" in view["waterfall"]
    assert view["stages"]["composer"] == "completed"
    assert view["composition_stage"] is True


def test_provenance_and_confidence_defaults():
    p = section_provenance("runtime", ok=True)
    assert p["source"] == "runtime"
    assert section_confidence("runtime") == 1.0
    assert section_confidence("memory") == 0.94
    assert section_confidence("inference") == 0.98
    assert section_confidence("runtime", ok=False) == 0.0


def test_compose_attaches_provenance_confidence():
    def fake_ref(query, subject=""):
        return {"ok": True, "message": "REF", "data": {}}

    def fake_runtime(action):
        return {"ok": True, "message": "RUN", "data": {}}

    with (
        patch("jarvis.reference_engine.search_reference", side_effect=fake_ref),
        patch("jarvis.runtime_introspection.runtime_action_result", side_effect=fake_runtime),
    ):
        out = orchestrate_compose(
            "Show me the Docker Compose documentation and tell me whether Docker is currently running."
        )
    plan = out["data"]["plan"]
    assert plan["provenance"]
    assert "reference" in plan["section_confidence"]
    assert plan["plan_view"]["final_response_latency_ms"] == out["data"]["duration_ms"]


def test_health_and_analytics_panels_shape():
    health = capability_health_snapshot()
    assert health["ok"] is True
    ids = {c["id"] for c in health["capabilities"]}
    assert "memory" in ids and "capability_bus" in ids and "conversation_trace" in ids
    assert {"consumers", "avg_latency_ms", "error_rate", "last_success_ts"} <= set(
        health["capabilities"][0]
    )
    analytics = cross_capability_analytics(limit=10)
    assert analytics["ok"] is True
    assert "combinations" in analytics
    panel = mission_control_panel()
    assert panel["capability_health"]["ok"] is True
    assert panel["cross_capability"]["ok"] is True
