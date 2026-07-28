"""Enrich Platform Mission Control snapshots with Aria operator surfaces."""

from __future__ import annotations

from typing import Any


_platform_link_cache: dict[str, Any] = {"at": 0.0, "value": None}


def platform_mission_control_link() -> dict[str, Any]:
    """Honest pointer when advanced tabs exist only on Platform MC."""
    import time

    now = time.time()
    if _platform_link_cache["value"] is not None and now - float(_platform_link_cache["at"]) < 30:
        return dict(_platform_link_cache["value"])

    port = "8780"
    url = ""
    available = False
    try:
        import os

        port = str(os.environ.get("MISSION_CONTROL_PORT") or os.environ.get("AIPLATFORM_MC_PORT") or "8780")
        url = f"http://127.0.0.1:{port}/"
        # Soft probe — do not fail enrichment if down
        import urllib.request

        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=0.25) as resp:
            available = 200 <= getattr(resp, "status", 200) < 500
    except Exception:
        available = False
    value = {
        "label": "Open Platform Mission Control",
        "url": url or f"http://127.0.0.1:{port}/",
        "port": port,
        "available": available,
        "why": (
            "Advanced cognitive and laboratory tabs (endurance, sessions, diagnostics lab) "
            "live in the AI Platform Mission Control aggregator. Aria Mission Control is the "
            "infrastructure health console; Platform MC remains the full lab surface."
        ),
        "experimental_tabs": [
            "sessions",
            "diagnostics",
            "endurance",
            "startup",
            "performance-lab",
        ],
    }
    _platform_link_cache["at"] = now
    _platform_link_cache["value"] = value
    return dict(value)


def advisor_action_cards(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    """Map advisor recommendations to confirmable approved actions."""
    ov = snapshot.get("overview") or {}
    advisor = ov.get("operational_advisor") or snapshot.get("operational_advisor") or {}
    cards: list[dict[str, Any]] = []
    for rec in advisor.get("recommendations") or []:
        title = str((rec or {}).get("title") or "Recommendation")
        action_text = str((rec or {}).get("action") or "").lower()
        blob = f"{title} {action_text} {(rec or {}).get('reason') or ''}".lower()
        actions: list[dict[str, Any]] = []
        if any(k in blob for k in ("warm", "load model", "preload")):
            actions.append({"id": "warm_model", "label": "Warm Model", "confirm": True, "kind": "inference"})
        if any(k in blob for k in ("recover", "repair", "heal")):
            actions.append({"id": "recover_runtime", "label": "Recover Runtime", "confirm": True, "kind": "recovery"})
        if any(k in blob for k in ("reconnect", "connection", "runtime connect")):
            actions.append({"id": "reconnect_platform", "label": "Reconnect Platform", "confirm": True, "kind": "connection"})
        if any(k in blob for k in ("inference", "ollama", "provider", "model")):
            actions.append({"id": "open_inference", "label": "Open Inference", "confirm": False, "kind": "nav"})
        if any(k in blob for k in ("recover", "repair", "backup")):
            actions.append({"id": "open_recovery", "label": "Open Recovery", "confirm": False, "kind": "nav"})
        if any(k in blob for k in ("job", "queue")):
            actions.append({"id": "open_job_center", "label": "Open Job Center", "confirm": False, "kind": "nav"})
        if any(k in blob for k in ("activity", "event", "alert")):
            actions.append({"id": "open_activity", "label": "Open Activity", "confirm": False, "kind": "nav"})
            actions.append({"id": "create_activity_alert", "label": "Create Activity Alert", "confirm": True, "kind": "activity"})
        if not actions:
            actions = [
                {"id": "open_recovery", "label": "Open Recovery", "confirm": False, "kind": "nav"},
                {"id": "open_activity", "label": "Open Activity", "confirm": False, "kind": "nav"},
            ]
        # Dedupe by id
        seen: set[str] = set()
        uniq = []
        for a in actions:
            if a["id"] in seen:
                continue
            seen.add(a["id"])
            uniq.append(a)
        cards.append(
            {
                "title": title,
                "reason": (rec or {}).get("reason"),
                "impact": (rec or {}).get("impact"),
                "severity": (rec or {}).get("severity") or "info",
                "duration_estimate": (rec or {}).get("duration_estimate"),
                "actions": uniq,
            }
        )
    return cards


def enrich_snapshot(data: dict[str, Any] | None) -> dict[str, Any]:
    """Attach Aria operator fields without mutating Platform ownership."""
    snap = dict(data or {})
    from jarvis.mission_control_ops.health_brief import build_health_brief
    from jarvis.mission_control_ops.predictive import build_predictive_warnings
    from jarvis.mission_control_ops.activity_bridge import correlate_critical_health

    snap["title"] = "Mission Control"
    snap["product"] = "mission_control"
    snap["product_boundary"] = {
        "owns": [
            "infrastructure_health",
            "provider_health",
            "runtime_status",
            "hardware",
            "recovery",
            "routing",
            "performance",
            "connection_diagnostics",
            "operational_guidance",
        ],
        "does_not_own": [
            "execution",
            "scheduling",
            "durable_events",
            "chat",
            "automation",
        ],
    }
    snap["health_brief"] = build_health_brief(snap)
    snap["advisor_actions"] = advisor_action_cards(snap)
    snap["predictive_warnings"] = build_predictive_warnings(snap)
    snap["platform_link"] = platform_mission_control_link()
    try:
        snap["activity_correlation"] = correlate_critical_health(snap)
    except Exception:
        snap["activity_correlation"] = []
    # Sparkline-friendly samples from hardware/overview
    hw = snap.get("hardware") or {}
    ov = snap.get("overview") or {}
    snap["perf_series"] = {
        "cpu": _series_stub("cpu", hw.get("cpu_load") or ov.get("cpu_load")),
        "ram": _series_stub("ram", hw.get("ram_available_gb") or ov.get("ram_available_gb")),
        "gpu": _series_stub("gpu", 1 if (hw.get("gpu_name") or ov.get("gpu")) else 0),
        "vram": _series_stub("vram", hw.get("free_vram_mb") or ov.get("free_vram_mb")),
        "latency": _series_stub("latency", (snap.get("routing_stats") or {}).get("average_latency_ms")),
        "queue_depth": _series_stub("queue", (snap.get("overview") or {}).get("active_jobs") or (snap.get("jobs") or {}).get("active_count")),
    }
    return snap


def _series_stub(name: str, latest: Any) -> dict[str, Any]:
    """Maintain a small rolling series in DATA_DIR for sparklines."""
    import json
    from pathlib import Path

    from jarvis.config import DATA_DIR

    path = DATA_DIR / "mission_control" / "series" / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    points: list[float] = []
    try:
        if path.is_file():
            points = list(json.loads(path.read_text(encoding="utf-8")).get("points") or [])
    except Exception:
        points = []
    try:
        if latest is not None:
            points.append(float(latest))
    except (TypeError, ValueError):
        pass
    points = points[-24:]
    try:
        path.write_text(json.dumps({"points": points}), encoding="utf-8")
    except Exception:
        pass
    return {"points": points, "latest": latest}
