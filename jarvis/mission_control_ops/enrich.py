"""Enrich Platform Mission Control snapshots with Aria operator surfaces."""

from __future__ import annotations

import time
from typing import Any, Literal

EnrichMode = Literal["lite", "full"]

_platform_link_cache: dict[str, Any] = {"at": 0.0, "value": None}
_PRODUCT_PANEL_CACHE: dict[str, Any] = {"at": 0.0, "value": None}
_PRODUCT_PANEL_TTL_S = 30.0
_RESOURCE_ALIGN_CACHE: dict[str, Any] = {"at": 0.0, "value": None}
_RESOURCE_ALIGN_TTL_S = 8.0


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


def _align_runtime_resources(snap: dict[str, Any]) -> None:
    """Cheap-ish GPU/RAM alignment with a short TTL (resource_snapshot is ~0.3–0.4s)."""
    now = time.monotonic()
    cached = _RESOURCE_ALIGN_CACHE.get("value")
    if (
        isinstance(cached, dict)
        and now - float(_RESOURCE_ALIGN_CACHE.get("at") or 0) < _RESOURCE_ALIGN_TTL_S
    ):
        payload = cached
    else:
        try:
            from jarvis.resource_router import ollama_loaded_models, snapshot as resource_snapshot

            payload = {
                "loaded": ollama_loaded_models() or [],
                "res": resource_snapshot() or {},
            }
            try:
                from jarvis.gpu import detect_gpu

                payload["gpu"] = detect_gpu() or {}
            except Exception:
                payload["gpu"] = {}
            _RESOURCE_ALIGN_CACHE["at"] = now
            _RESOURCE_ALIGN_CACHE["value"] = payload
        except Exception:
            return

    loaded = payload.get("loaded") or []
    res = payload.get("res") or {}
    gpu = payload.get("gpu") or {}
    inf = dict(snap.get("inference") or {})
    if not inf.get("loaded_models"):
        inf["loaded_models"] = loaded
    inf["loaded_count"] = len(loaded)
    inf["models_home"] = "models"
    inf["switch_note"] = "Switch uses Models registry (role_default). Warm/unload are health ops only."
    snap["inference"] = inf
    hw = dict(snap.get("hardware") or {})
    ov = dict(snap.get("overview") or {})
    if res.get("vram_mb") is not None:
        hw["vram_mb"] = res.get("vram_mb")
        ov["vram_mb"] = res.get("vram_mb")
    if res.get("free_vram_mb") is not None:
        hw["free_vram_mb"] = res.get("free_vram_mb")
        ov["free_vram_mb"] = res.get("free_vram_mb")
    if res.get("ram_available_gb") is not None:
        hw["ram_available_gb"] = res.get("ram_available_gb")
        ov["ram_available_gb"] = res.get("ram_available_gb")
    if res.get("ram_total_gb") is not None:
        hw["ram_total_gb"] = res.get("ram_total_gb")
    if gpu.get("name"):
        hw["gpu_name"] = gpu.get("compute_gpu") or gpu.get("name")
        ov["gpu"] = hw["gpu_name"]
    hw["display_vendor"] = gpu.get("display_vendor")
    hw["compute_vendor"] = gpu.get("compute_vendor") or gpu.get("vendor")
    hw["ollama_using_gpu"] = gpu.get("ollama_using_gpu")
    snap["hardware"] = hw
    snap["overview"] = ov


def _attach_product_panels(snap: dict[str, Any]) -> None:
    """Full Mission console product bridges — cached so polls do not re-fan-out."""
    now = time.monotonic()
    cached = _PRODUCT_PANEL_CACHE.get("value")
    if (
        isinstance(cached, dict)
        and now - float(_PRODUCT_PANEL_CACHE.get("at") or 0) < _PRODUCT_PANEL_TTL_S
    ):
        snap.update(cached)
        return

    panels: dict[str, Any] = {}
    try:
        from jarvis.voice_product.mission_bridge import voice_mission_panel

        panels["voice"] = voice_mission_panel()
    except Exception:
        panels["voice"] = {"product": "Voice", "state": "unknown"}
    try:
        from jarvis.vision_product.mission_bridge import vision_mission_panel

        panels["vision"] = vision_mission_panel()
    except Exception:
        panels["vision"] = {"product": "Vision", "state": "unknown"}
    try:
        from jarvis.flytying_product.mission_bridge import flytying_mission_panel

        panels["flytying"] = flytying_mission_panel()
    except Exception:
        panels["flytying"] = {"product": "Fly Tying", "state": "unknown"}
    try:
        from jarvis.health_product.mission_bridge import health_mission_panel

        panels["health"] = health_mission_panel()
    except Exception:
        panels["health"] = {"product": "Health", "state": "unknown"}
    try:
        from jarvis.home_assistant_product.mission_bridge import smarthome_mission_panel

        panel = smarthome_mission_panel()
        panels["smarthome"] = panel
        panels["home_assistant"] = panel
    except Exception:
        panels["smarthome"] = {"product": "Smart Home", "state": "unknown"}
        panels["home_assistant"] = {"product": "Smart Home", "state": "unknown"}
    try:
        from jarvis.capabilities_product.mission_bridge import capabilities_mission_panel

        panels["capabilities"] = capabilities_mission_panel()
    except Exception:
        panels["capabilities"] = {"product": "Capabilities", "state": "unknown"}
    try:
        from jarvis.integrations_product.mission_bridge import integrations_mission_panel

        panels["integrations"] = integrations_mission_panel()
    except Exception:
        panels["integrations"] = {"product": "Integrations", "state": "unknown"}
    try:
        from jarvis.search_product.mission_bridge import search_mission_panel

        panels["search"] = search_mission_panel()
    except Exception:
        panels["search"] = {"product": "Search", "state": "unknown"}
    try:
        from jarvis.settings_product.mission_bridge import settings_mission_panel

        panels["settings_product"] = settings_mission_panel()
    except Exception:
        panels["settings_product"] = {"product": "Settings", "state": "unknown"}
    try:
        from jarvis.dashboard_product.mission_bridge import dashboard_mission_panel

        panels["dashboard"] = dashboard_mission_panel()
    except Exception:
        panels["dashboard"] = {"product": "Dashboard", "state": "unknown"}
    try:
        from jarvis.layouts_product.mission_bridge import layouts_mission_panel

        panels["layouts"] = layouts_mission_panel()
    except Exception:
        panels["layouts"] = {"product": "Layouts", "state": "unknown"}
    try:
        from jarvis.notifications_product.mission_bridge import notifications_mission_panel

        panels["notifications"] = notifications_mission_panel()
    except Exception:
        panels["notifications"] = {"product": "Notifications", "state": "unknown"}
    try:
        from jarvis.provider_health.mission_bridge import mission_panel as provider_health_mission_panel

        panels["provider_health"] = provider_health_mission_panel()
    except Exception:
        panels["provider_health"] = {"product": "Provider Health", "state": "unknown"}
    try:
        from jarvis.repair_product.mission_bridge import repair_mission_panel

        panels["guided_repair"] = repair_mission_panel()
    except Exception:
        panels["guided_repair"] = {"product": "Guided Repair", "state": "unknown"}
    try:
        from jarvis.integrity_product.mission_bridge import integrity_mission_panel

        panels["integrity"] = integrity_mission_panel()
    except Exception:
        panels["integrity"] = {"product": "Production Integrity", "state": "unknown"}
    try:
        from jarvis.latency_observability.mission_bridge import mission_panel as latency_mission_panel

        panels["latency"] = latency_mission_panel()
    except Exception:
        panels["latency"] = {"product": "Latency", "state": "unknown"}
    try:
        from jarvis.calendar_bridges import mission_status as calendar_mission_status

        panels["calendar"] = calendar_mission_status()
    except Exception:
        panels["calendar"] = {"product": "Calendar", "state": "unknown"}
    try:
        from jarvis.image_generation.mission_bridge import engine_health as image_engine_health

        panels["image_generation"] = {"product": "Image Generation", **(image_engine_health() or {})}
    except Exception:
        panels["image_generation"] = {"product": "Image Generation", "state": "unknown"}
    try:
        from jarvis.video_generation.mission_bridge import engine_health as video_engine_health

        panels["video_generation"] = {"product": "Video Generation", **(video_engine_health() or {})}
    except Exception:
        panels["video_generation"] = {"product": "Video Generation", "state": "unknown"}

    _PRODUCT_PANEL_CACHE["at"] = now
    _PRODUCT_PANEL_CACHE["value"] = panels
    snap.update(panels)


def enrich_snapshot(data: dict[str, Any] | None, *, mode: EnrichMode = "full") -> dict[str, Any]:
    """Attach Aria operator fields without mutating Platform ownership.

    ``mode="lite"`` builds health_brief + operator fields without the product-panel
    fan-out (SYS-P01). ``mode="full"`` attaches product bridges with a short TTL cache.
    """
    snap = dict(data or {})
    from jarvis.mission_control_ops.activity_bridge import correlate_critical_health
    from jarvis.mission_control_ops.health_brief import build_health_brief
    from jarvis.mission_control_ops.predictive import build_predictive_warnings

    snap["title"] = "Mission Control"
    snap["product"] = "mission_control"
    snap["enrich_mode"] = mode
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
            "model_registry",
            "role_assignments",
        ],
    }
    _align_runtime_resources(snap)
    snap["health_brief"] = build_health_brief(snap)
    snap["advisor_actions"] = advisor_action_cards(snap)
    snap["predictive_warnings"] = build_predictive_warnings(snap)
    snap["platform_link"] = platform_mission_control_link()
    try:
        snap["activity_correlation"] = correlate_critical_health(snap)
    except Exception:
        snap["activity_correlation"] = []
    hw = snap.get("hardware") or {}
    ov = snap.get("overview") or {}
    snap["perf_series"] = {
        "cpu": _series_stub("cpu", hw.get("cpu_load") or ov.get("cpu_load")),
        "ram": _series_stub("ram", hw.get("ram_available_gb") or ov.get("ram_available_gb")),
        "gpu": _series_stub("gpu", 1 if (hw.get("gpu_name") or ov.get("gpu")) else 0),
        "vram": _series_stub("vram", hw.get("free_vram_mb") or ov.get("free_vram_mb")),
        "latency": _series_stub("latency", (snap.get("routing_stats") or {}).get("average_latency_ms")),
        "queue_depth": _series_stub(
            "queue",
            (snap.get("overview") or {}).get("active_jobs") or (snap.get("jobs") or {}).get("active_count"),
        ),
    }
    if mode == "full":
        _attach_product_panels(snap)
        voice = snap.get("voice") or {}
        vq = (voice.get("queue") or {}).get("pending")
        snap["perf_series"]["voice_queue"] = _series_stub("voice_queue", vq)
        latency = snap.get("latency") or {}
        ft = ((latency.get("first_token") or {}).get("avg_ms"))
        snap["perf_series"]["first_token"] = _series_stub("first_token", ft)
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
