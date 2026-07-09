"""Prometheus metrics export for workstation observability."""

from __future__ import annotations

from typing import Any


def collect_metrics() -> dict[str, float]:
    """Gather numeric metrics for Prometheus export."""
    out: dict[str, float] = {}
    try:
        from jarvis.metrics import snapshot

        snap = snapshot()
        out["jarvis_uptime_seconds"] = float(snap.get("uptime_sec") or 0)
        out["jarvis_watchdog_restarts_total"] = float(snap.get("watchdog_restarts") or 0)
        media = snap.get("media") or {}
        out["jarvis_media_queue_pending"] = float(media.get("pending") or 0)
        out["jarvis_media_jobs_completed"] = float(media.get("completed") or 0)
    except Exception:
        pass

    try:
        from jarvis.resource_router import snapshot as resource_snapshot

        res = resource_snapshot()
        out["jarvis_vram_free_mb"] = float(res.get("free_vram_mb") or 0)
        out["jarvis_ram_available_gb"] = float(res.get("ram_available_gb") or 0)
        out["jarvis_ollama_models_loaded"] = float(res.get("ollama_models_loaded") or 0)
    except Exception:
        pass

    try:
        from jarvis.workstation.registry import registry_snapshot

        ws = registry_snapshot()
        out["jarvis_workstation_components_total"] = float(ws.get("source_count") or 0)
        out["jarvis_workstation_components_running"] = float(
            sum(1 for c in ws.get("sources") or [] if c.get("running"))
        )
    except Exception:
        pass

    try:
        from jarvis.knowledge.registry import registry_snapshot as kr_snapshot

        kr = kr_snapshot()
        out["jarvis_knowledge_sources_total"] = float(kr.get("source_count") or 0)
        out["jarvis_knowledge_sources_searchable"] = float(kr.get("retrieval_count") or 0)
    except Exception:
        pass

    return out


def prometheus_text() -> str:
    """Render metrics in Prometheus exposition format."""
    lines: list[str] = []
    for name, value in sorted(collect_metrics().items()):
        lines.append(f"# TYPE {name} gauge")
        lines.append(f"{name} {value}")
    return "\n".join(lines) + "\n"


def prometheus_payload() -> dict[str, Any]:
    return {"format": "prometheus", "metrics": collect_metrics(), "text": prometheus_text()}
