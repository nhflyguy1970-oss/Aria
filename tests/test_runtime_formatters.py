"""Intent formatters: concise runtime answers (not full report dumps)."""

from __future__ import annotations

from jarvis.runtime_formatters import (
    format_applications,
    format_databases,
    format_gpu,
    format_inference,
    format_jobs,
    format_memory,
    format_runtime_intent,
    format_services,
    format_status,
    operational_state,
)
from jarvis.runtime_introspection import classify_runtime_action, format_runtime_markdown

SAMPLE_SERVICES = [
    {"id": "ollama", "label": "Ollama", "running": True},
    {"id": "grafana", "label": "Grafana", "running": True},
    {"id": "n8n", "label": "n8n", "running": True},
]
SAMPLE_DBS = [
    {"id": "postgres", "label": "PostgreSQL", "running": True},
    {"id": "redis", "label": "Redis", "running": True},
    {"id": "mongo", "label": "MongoDB", "running": True},
    {"id": "qdrant", "label": "Qdrant", "running": True},
]
SAMPLE_APPS = [
    {"id": "aria", "label": "Aria", "running": True, "healthy": True},
    {"id": "flytying", "label": "FlyTying AI", "running": False, "stopped": True},
    {"id": "uncensored", "label": "Aria Uncensored", "running": False, "stopped": True},
]


def test_services_formatter_is_concise_list():
    text = format_services({"services": SAMPLE_SERVICES})
    assert "Running Services" in text
    assert "✓ Ollama" in text
    assert "3 services running" in text
    assert "No degraded services" in text
    assert "Aria Runtime Report" not in text


def test_applications_formatter_splits_running_stopped():
    text = format_applications({"applications": SAMPLE_APPS})
    assert "Running" in text and "✓ Aria" in text
    assert "Stopped" in text and "• FlyTying AI" in text


def test_jobs_idle():
    text = format_jobs({"active_jobs": 0, "jobs": {"any_busy": False}})
    assert "0 active" in text
    assert "idle" in text.lower()


def test_databases_formatter():
    text = format_databases({"databases": SAMPLE_DBS})
    assert "✓ PostgreSQL" in text
    assert "All healthy" in text


def test_gpu_formatter_uses_vram_not_ram():
    text = format_gpu(
        {
            "gpu": {"name": "NVIDIA RTX 3060", "free_vram_mb": 12161, "vram_mb": 12288},
            "ram_available_gb": 62.7,
        }
    )
    assert "NVIDIA RTX 3060" in text
    assert "Free VRAM" in text
    assert "11.9 GB" in text or "12.1 GB" in text or "11.8 GB" in text
    assert "System RAM" not in text


def test_memory_formatter_never_vram():
    text = format_memory(
        {
            "ram_available_gb": 62.7,
            "hardware": {"ram_total_gb": 64.0, "free_vram_mb": 12161},
        }
    )
    assert "System RAM" in text
    assert "62.7" in text
    assert "VRAM" in text  # disclaimer only
    assert "This is system RAM, not GPU VRAM" in text
    assert "Free VRAM" not in text


def test_model_formatter_when_mc_missing_model():
    text = format_inference({"provider": "ollama", "current_model": "", "inference": {}})
    assert "does not currently expose the active model" in text
    assert "Provider: ollama" in text
    assert "No live Mission Control fields matched" not in text


def test_model_formatter_with_model():
    text = format_inference(
        {
            "current_model": "coder-stable:latest",
            "provider": "ollama",
            "device": "nvidia",
            "context_length": 8192,
        }
    )
    assert "coder-stable:latest" in text
    assert "Provider: ollama" in text
    assert "Device: nvidia" in text


def test_stopped_phase_reads_as_idle_when_services_live():
    state, _ = operational_state(
        {
            "phase": {"phase": "STOPPED", "detail": "workstation stopped"},
            "platform_status": "healthy",
            "services": SAMPLE_SERVICES,
        }
    )
    assert state == "Idle"


def test_status_default_is_concise_not_full_dump():
    payload = {
        "execution_mode": "platform-attached",
        "phase": {"phase": "STOPPED"},
        "platform_status": "healthy",
        "services": {"services": SAMPLE_SERVICES, "databases": SAMPLE_DBS},
        "applications": SAMPLE_APPS,
        "active_jobs": 0,
        "needs_attention": ["All clear"],
        "gpu": {"name": "NVIDIA RTX 3060", "free_vram_mb": 12000},
        "current_model": "x",
    }
    concise = format_status(payload, full=False)
    assert "Operational State" in concise
    assert "Idle" in concise
    assert "full status" in concise.lower()
    assert "Running Services" not in concise

    full = format_status(payload, full=True)
    assert "Running Services" in full
    assert "Applications" in full


def test_never_emit_empty_match_stub():
    text = format_runtime_intent("runtime_models", {"ok": True, "provider": "ollama"})
    assert "No live Mission Control fields matched" not in text


def test_classify_intent_actions():
    assert classify_runtime_action("What services are running?") == "runtime_services"
    assert classify_runtime_action("What databases are connected?") == "runtime_databases"
    assert classify_runtime_action("What GPU are you using?") == "runtime_gpu"
    assert classify_runtime_action("How much RAM is available?") == "runtime_ram"
    assert classify_runtime_action("What model are you using?") == "runtime_models"
    assert classify_runtime_action("What jobs are active?") == "runtime_jobs"
    assert classify_runtime_action("What applications are running?") == "runtime_applications"
    assert classify_runtime_action("full status") == "runtime_report"
    assert classify_runtime_action("runtime report") == "runtime_report"


def test_format_runtime_markdown_services_with_list_payload():
    """Regression: dedicated services collector returns services as a list."""
    text = format_runtime_markdown(
        "runtime_services",
        {"ok": True, "services": SAMPLE_SERVICES, "databases": SAMPLE_DBS},
    )
    assert "✓ Ollama" in text
    assert "No live Mission Control fields matched" not in text
    assert "## Aria Runtime Report" not in text
