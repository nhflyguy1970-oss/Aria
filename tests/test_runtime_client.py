"""Tests for RuntimeClient and platform runtime attachment."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

SAMPLE_MC = {
    "ok": True,
    "ts": "2026-07-09T12:00:00",
    "owner": "aiplatform",
    "overview": {
        "platform_status": "healthy",
        "execution_mode": "platform-attached",
        "phase": {"phase": "production"},
        "acceptance_overall": 95,
        "production_readiness": 90,
        "current_model": "llama3",
        "inference_provider": "ollama",
        "memory_provider": "platform",
        "knowledge_provider": "platform",
        "gpu": "RTX 4090",
        "active_jobs": 1,
        "needs_attention": [],
    },
    "applications": [{"id": "aria", "label": "Aria", "running": True, "healthy": True}],
    "services": [{"id": "ollama", "name": "ollama", "running": True}],
    "databases": [{"id": "postgres", "name": "postgres", "running": True}],
    "services_ready": True,
    "inference": {"current_model": "llama3", "provider": "ollama"},
    "hardware": {"gpu_name": "RTX 4090"},
    "jobs": {"active_count": 1},
    "recovery": {"health": {"ok": True}},
}


def _mock_client(snapshot=None, *, connection_mode="in_process"):
    client = MagicMock()
    client.snapshot.return_value = snapshot or SAMPLE_MC
    client.connection_report.return_value = {
        "ok": True,
        "platform_discovered": True,
        "mission_control_reachable": True,
        "application_host_connected": True,
        "application_registered": True,
        "runtime_synced": True,
        "connection_mode": connection_mode,
        "issues": [],
    }
    client.connect.return_value = client.connection_report.return_value
    return client


@patch("jarvis.runtime_introspection.get_runtime_client")
def test_collect_runtime_status_uses_mission_control(mock_get_client):
    mock_get_client.return_value = _mock_client()
    from jarvis.runtime_introspection import collect_runtime_status

    data = collect_runtime_status()
    assert data.get("source") == "mission_control"
    assert data.get("execution_mode") == "platform-attached"
    assert data["models"]["current_model"] == "llama3"


@patch("jarvis.runtime_introspection.get_runtime_client")
def test_collect_runtime_services_from_mission_control(mock_get_client):
    mock_get_client.return_value = _mock_client()
    from jarvis.runtime_introspection import collect_runtime_services

    data = collect_runtime_services()
    assert data.get("source") == "mission_control"
    assert data.get("ready") is True
    assert any(s.get("id") == "ollama" for s in data.get("services", []))


@patch("jarvis.runtime_introspection.get_runtime_client")
def test_runtime_action_result_marks_source(mock_get_client):
    mock_get_client.return_value = _mock_client()
    from jarvis.runtime_introspection import runtime_action_result

    result = runtime_action_result("runtime_models")
    assert result["ok"] is True
    assert result.get("source") == "mission_control"
    assert "Mission Control" in result["message"]


@patch("jarvis.runtime_client.get_runtime_client")
def test_validate_runtime_startup_checks(mock_get_client):
    mock_get_client.return_value = _mock_client()
    from jarvis.platform_runtime import validate_runtime_startup

    report = validate_runtime_startup()
    assert report.get("checks", {}).get("snapshot_ok") is True
    assert report.get("runtime_synced") is True


@patch("jarvis.runtime_introspection.get_runtime_client")
def test_runtime_unavailable_returns_warning_not_local(mock_get_client):
    from jarvis.runtime_client import RuntimeClientError

    client = MagicMock()
    client.snapshot.side_effect = RuntimeClientError("Mission Control API not reachable")
    mock_get_client.return_value = client

    from jarvis.runtime_introspection import collect_runtime, runtime_action_result

    result = collect_runtime("runtime_services")
    assert result["ok"] is False
    assert "Mission Control" in result["message"]

    action = runtime_action_result("runtime_health")
    assert action["ok"] is False
    assert action.get("source") == "none"


@patch("jarvis.runtime_introspection.get_runtime_client")
def test_validation_prompts_use_mission_control(mock_get_client):
    mock_get_client.return_value = _mock_client()
    from jarvis.router import route
    from jarvis.session import SessionContext

    session = SessionContext()
    prompts = [
        "Status",
        "What services are running?",
        "What model are you using?",
        "Am I attached to AI Platform?",
        "What databases are connected?",
        "What GPU are you using?",
        "What applications are running?",
        "What jobs are active?",
        "What phase is the workstation in?",
        "What needs attention?",
    ]
    for prompt in prompts:
        intent = route(prompt, session, None)
        action = intent.get("action")
        assert action != "web_search", prompt
        assert action.startswith("runtime_") or action == "status_summary", prompt
