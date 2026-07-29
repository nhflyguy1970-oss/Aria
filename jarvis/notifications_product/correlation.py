"""Correlation heuristics — related failures without inventing incidents."""

from __future__ import annotations

import time
from typing import Any

from jarvis.notifications_product.pipeline import recent


def correlate(*, window_seconds: int = 1800) -> dict[str, Any]:
    now = time.time()
    items = [
        e
        for e in recent(limit=80)
        if str(e.get("severity") or "") in ("critical", "error", "warning")
        and (now - float(e.get("timestamp") or now)) <= window_seconds
    ]
    buckets: dict[str, list[dict[str, Any]]] = {
        "inference": [],
        "jobs": [],
        "home": [],
        "automation": [],
        "planner": [],
        "calendar": [],
        "other": [],
    }
    for e in items:
        blob = f"{e.get('source')} {e.get('category')} {e.get('title')} {e.get('summary')}".lower()
        if any(x in blob for x in ("ollama", "provider", "inference", "model", "vram")):
            buckets["inference"].append(e)
        elif any(x in blob for x in ("job", "comfy", "gallery", "video")):
            buckets["jobs"].append(e)
        elif any(x in blob for x in ("home assistant", "ha ", "device")):
            buckets["home"].append(e)
        elif "automation" in blob or "workflow" in blob:
            buckets["automation"].append(e)
        elif "planner" in blob or "alarm" in blob or "timer" in blob:
            buckets["planner"].append(e)
        elif "calendar" in blob or "missed" in blob:
            buckets["calendar"].append(e)
        else:
            buckets["other"].append(e)

    incidents = []
    for key, evts in buckets.items():
        if len(evts) < 2:
            continue
        incidents.append(
            {
                "id": f"corr_{key}",
                "label": key,
                "count": len(evts),
                "titles": [e.get("title") for e in evts[:4]],
                "severity": "error" if any(e.get("severity") == "critical" for e in evts) else "warning",
            }
        )
    return {"ok": True, "window_seconds": window_seconds, "incidents": incidents, "invented": False}


def experimental_incident_narrative(incident: dict[str, Any] | None = None) -> dict[str, Any]:
    """Template narrative — never LLM-required; never invents facts."""
    incident = incident or {}
    label = incident.get("label") or "related"
    count = incident.get("count") or 0
    titles = incident.get("titles") or []
    story = f"{count} related {label} failures in the last window."
    if titles:
        story += " Seen: " + "; ".join(str(t) for t in titles[:3]) + "."
    story += " Open Notifications to triage. Mission Control for infrastructure detail."
    return {"ok": True, "experimental": True, "narrative": story, "auto_apply": False}
