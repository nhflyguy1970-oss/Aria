"""Correlate critical Mission Control health into Activity Center-shaped events."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

_STATE = DATA_DIR / "mission_control" / "activity_correlation.json"


def _load_state() -> dict[str, Any]:
    try:
        if _STATE.is_file():
            return json.loads(_STATE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"fingerprints": {}, "events": []}


def _save_state(state: dict[str, Any]) -> None:
    _STATE.parent.mkdir(parents=True, exist_ok=True)
    _STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _fp(*parts: str) -> str:
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def correlate_critical_health(snapshot: dict[str, Any] | None) -> list[dict[str, Any]]:
    """
    Promote critical infrastructure issues to Activity-shaped events.

    Returns new events only (deduped). Never remediates.
    """
    d = snapshot or {}
    brief = d.get("health_brief") or {}
    if not brief:
        from jarvis.mission_control_ops.health_brief import build_health_brief

        brief = build_health_brief(d)

    severity = str(brief.get("severity") or "ok").lower()
    if severity not in ("error", "critical", "warning"):
        return []
    if severity == "warning" and brief.get("overall") == "healthy":
        return []

    issues = list(brief.get("critical_issues") or [])
    if not issues and severity not in ("error", "critical"):
        return []
    if not issues:
        issues = [str(brief.get("headline") or "Infrastructure degraded")]

    state = _load_state()
    fps: dict[str, float] = dict(state.get("fingerprints") or {})
    now = time.time()
    # Expire fingerprints after 6 hours so re-issues can re-alert
    fps = {k: v for k, v in fps.items() if now - float(v) < 6 * 3600}

    new_events: list[dict[str, Any]] = []
    for issue in issues[:5]:
        key = _fp(severity, issue.strip().lower())
        if key in fps:
            continue
        fps[key] = now
        tab = "recovery"
        low = issue.lower()
        if "inference" in low or "ollama" in low or "model" in low:
            tab = "inference"
        elif "connect" in low or "runtime" in low:
            tab = "connection"
        elif "rout" in low:
            tab = "routing"
        elif "hardware" in low or "vram" in low or "ram" in low or "disk" in low:
            tab = "hardware"
        evt = {
            "id": f"mc-{key}",
            "timestamp": now,
            "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
            "category": "mission",
            "type": "critical_health",
            "severity": "critical" if severity == "critical" else ("error" if severity == "error" else "warning"),
            "title": "Mission Control · critical health",
            "message": issue,
            "subsystem": tab,
            "suggested_fix": brief.get("recommended_action") or "Open Mission Control Recovery",
            "resolution": None,
            "fix": f"mc:{tab}",
            "source": "mission_control",
            "product": "mission_control",
        }
        new_events.append(evt)

    if new_events:
        hist = list(state.get("events") or [])
        hist = (new_events + hist)[:100]
        _save_state({"fingerprints": fps, "events": hist})
    else:
        state["fingerprints"] = fps
        _save_state(state)

    return new_events


def list_correlated_events(*, limit: int = 50) -> list[dict[str, Any]]:
    state = _load_state()
    return list(state.get("events") or [])[:limit]


def mark_resolution(event_id: str, note: str = "") -> dict[str, Any]:
    state = _load_state()
    events = list(state.get("events") or [])
    found = False
    for ev in events:
        if ev.get("id") == event_id:
            ev["resolution"] = note or "Resolved by operator"
            ev["resolved_at"] = time.time()
            found = True
            break
    if found:
        _save_state({**state, "events": events})
    return {"ok": found, "id": event_id}
