"""Mission Control ops — health brief, gates, actions, correlation."""

from __future__ import annotations

from unittest.mock import patch

from jarvis.mission_control_ops.health_brief import build_health_brief
from jarvis.mission_control_ops.predictive import build_predictive_warnings
from jarvis.mission_control_ops.automation_gate import evaluate_health_gate
from jarvis.mission_control_ops.inference_actions import run_inference_action, ALLOWED
from jarvis.mission_control_ops.activity_bridge import correlate_critical_health
from jarvis.mission_control_ops.enrich import enrich_snapshot, advisor_action_cards
from jarvis.mission_control_ops.verification import verify_after_repair


def test_health_brief_healthy():
    brief = build_health_brief(
        {
            "overview": {
                "platform_status": "healthy",
                "needs_attention": [],
                "operational_advisor": {"healthy": True, "headline": "All clear", "recommendations": []},
            },
            "recovery": {"health": {"ok": True}},
        }
    )
    assert brief["overall"] == "healthy"
    assert brief["healthy"] is True
    assert brief["primary_cta"]["action"]


def test_health_brief_critical():
    brief = build_health_brief(
        {
            "overview": {
                "platform_status": "critical",
                "needs_attention": ["Ollama down"],
                "operational_advisor": {
                    "healthy": False,
                    "headline": "Inference down",
                    "recommendations": [
                        {
                            "title": "Warm model",
                            "severity": "error",
                            "action": "Recover runtime",
                            "impact": "High",
                        }
                    ],
                },
            },
            "recovery": {"health": {"ok": False}},
        }
    )
    assert brief["overall"] in ("critical", "degraded")
    assert brief["severity"] in ("critical", "error", "warning")
    assert brief["critical_issues"]
    assert brief["primary_cta"]["label"]


def test_health_brief_strips_all_clear_sentinel():
    """BUG-006: 'All clear' must never sit beside real degraded issues."""
    brief = build_health_brief(
        {
            "overview": {
                "platform_status": "degraded",
                "needs_attention": ["All clear", "Long-run stability warning"],
                "operational_advisor": {
                    "healthy": False,
                    "headline": "Needs attention",
                    "recommendations": [
                        {
                            "title": "Long-run stability warning",
                            "severity": "warning",
                            "action": "Review long-run stability",
                        }
                    ],
                },
            },
            "recovery": {"health": {"ok": True}},
        }
    )
    assert "All clear" not in brief["critical_issues"]
    assert any("stability" in str(x).lower() for x in brief["critical_issues"])
    assert brief["overall"] == "degraded"


def test_predictive_warnings_disk():
    warns = build_predictive_warnings({"hardware": {"disk_free_gb": 3, "ram_available_gb": 1, "ram_total_gb": 32}})
    ids = {w["id"] for w in warns}
    assert "storage_exhaustion" in ids
    assert "ram_exhaustion" in ids


def test_advisor_action_cards():
    cards = advisor_action_cards(
        {
            "overview": {
                "operational_advisor": {
                    "recommendations": [
                        {"title": "Warm model", "severity": "warning", "action": "Warm the model", "reason": "cold start"}
                    ]
                }
            }
        }
    )
    assert cards
    ids = {a["id"] for a in cards[0]["actions"]}
    assert "warm_model" in ids or "open_inference" in ids


def test_inference_requires_confirmation():
    out = run_inference_action("warm_model", confirmed=False, model="llama3")
    assert out["ok"] is False
    assert out["error"] == "confirmation_required"
    assert "warm_model" in ALLOWED


def test_inference_unsupported():
    out = run_inference_action("explode", confirmed=True)
    assert out["ok"] is False


def test_automation_gate_skip_when_critical():
    with patch(
        "jarvis.mission_control_ops.automation_gate.get_infrastructure_health",
        return_value={
            "ok": False,
            "overall": "critical",
            "severity": "critical",
            "dangerous": True,
            "reason": "down",
        },
    ):
        gate = evaluate_health_gate(mode="auto", rule_name="nightly")
        assert gate["ok"] is False
        assert gate["action"] == "skip"


def test_automation_gate_warn_when_degraded():
    with patch(
        "jarvis.mission_control_ops.automation_gate.get_infrastructure_health",
        return_value={
            "ok": False,
            "overall": "degraded",
            "severity": "warning",
            "dangerous": False,
            "reason": "vram",
        },
    ):
        gate = evaluate_health_gate(mode="auto")
        assert gate["action"] == "warn"
        assert gate["ok"] is True


def test_automation_gate_off():
    gate = evaluate_health_gate(mode="off")
    assert gate["action"] == "allow"


def test_enrich_snapshot_fields():
    snap = enrich_snapshot(
        {
            "ok": True,
            "title": "AI Platform Mission Control",
            "overview": {"platform_status": "healthy", "needs_attention": [], "operational_advisor": {"healthy": True}},
            "recovery": {"health": {"ok": True}},
            "hardware": {"cpu_load": 0.5, "ram_available_gb": 20, "ram_total_gb": 32},
            "jobs": {"active_count": 0},
            "activity": {"events": []},
        }
    )
    assert snap["title"] == "Mission Control"
    assert snap["product"] == "mission_control"
    assert "health_brief" in snap
    assert "platform_link" in snap
    assert "perf_series" in snap
    assert "owns" in snap["product_boundary"]


def test_activity_correlation_dedup(tmp_path, monkeypatch):
    import jarvis.mission_control_ops.activity_bridge as ab

    monkeypatch.setattr(ab, "_STATE", tmp_path / "corr.json")
    snap = {
        "health_brief": {
            "severity": "critical",
            "overall": "critical",
            "critical_issues": ["Provider offline"],
            "recommended_action": "Open Inference",
            "headline": "down",
        }
    }
    first = correlate_critical_health(snap)
    second = correlate_critical_health(snap)
    assert first
    assert second == []


@patch("jarvis.mission_control_ops.verification.collect_mission_control", create=True)
def test_verify_after_repair_shape(mock_collect):
    # Patch where used
    with patch("jarvis.mission_control.collect_mission_control") as mc, patch(
        "jarvis.mission_control.get_tab"
    ) as gt:
        mc.return_value = {
            "health_brief": {"healthy": True, "headline": "ok"},
            "recovery": {"health": {"ok": True}},
            "inference": {"ollama_running": True, "provider": "ollama", "current_model": "x"},
            "routing_stats": {"error_pct": 0},
            "hardware": {},
        }
        gt.return_value = {"ok": True, "data": {"ok": True, "status": "connected"}}
        out = verify_after_repair()
        assert out["verified"] is True
        assert "checks" in out
        assert out["activity"]["category"] == "mission"
