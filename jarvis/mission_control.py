"""Mission Control — delegates to AI Platform (source of truth), enriched for Aria operators."""

from __future__ import annotations

import time
from typing import Any, Literal

# Shared TTLs so health / health-brief / full console do not each re-run multi-second
# platform collect + product-panel enrich on every poll (Tier 3A / SYS-P01).
_RAW_CACHE: dict[str, Any] = {"at": 0.0, "value": None}
_LITE_CACHE: dict[str, Any] = {"at": 0.0, "value": None}
_FULL_CACHE: dict[str, Any] = {"at": 0.0, "value": None}
_RAW_TTL_S = 12.0
_LITE_TTL_S = 12.0
_FULL_TTL_S = 12.0

EnrichMode = Literal["lite", "full"]


def _cache_get(bucket: dict[str, Any], ttl: float) -> dict[str, Any] | None:
    cached = bucket.get("value")
    if not isinstance(cached, dict):
        return None
    age = time.monotonic() - float(bucket.get("at") or 0)
    if age >= ttl:
        return None
    out = dict(cached)
    out["cached"] = True
    out["cache_age_ms"] = int(age * 1000)
    return out


def _cache_put(bucket: dict[str, Any], value: dict[str, Any]) -> None:
    bucket["at"] = time.monotonic()
    bucket["value"] = value


def _platform_raw(*, record_metrics: bool, force: bool = False) -> dict[str, Any]:
    if not force:
        hit = _cache_get(_RAW_CACHE, _RAW_TTL_S)
        if hit is not None:
            return hit
    from aiplatform.mission_control.aggregator import collect_mission_control as platform_mc

    # UI paths never need metrics sampling on every poll; keep one shared raw snapshot.
    raw = platform_mc(record_metrics=bool(record_metrics))
    _cache_put(_RAW_CACHE, raw)
    return dict(raw)


def collect_mission_control(
    *,
    record_metrics: bool = False,
    force: bool = False,
    enrich: EnrichMode = "full",
) -> dict[str, Any]:
    """Collect Platform MC + Aria enrich.

    ``enrich="lite"`` — operator health brief without product-panel fan-out (polls).
    ``enrich="full"`` — full console including product bridges (Mission Room).
    """
    from jarvis.mission_control_ops.enrich import enrich_snapshot

    mode: EnrichMode = "full" if enrich == "full" else "lite"
    bucket = _FULL_CACHE if mode == "full" else _LITE_CACHE
    ttl = _FULL_TTL_S if mode == "full" else _LITE_TTL_S
    if not force:
        hit = _cache_get(bucket, ttl)
        if hit is not None:
            return hit

    raw = _platform_raw(record_metrics=record_metrics, force=force)
    snap = enrich_snapshot(raw, mode=mode)
    _cache_put(bucket, snap)
    out = dict(snap)
    out["cached"] = False
    out["enrich_mode"] = mode
    return out


def get_tab(tab: str) -> dict[str, Any]:
    key = (tab or "").strip().lower()
    # Aria-local surface (not an AI-Platform MC tab name).
    if key == "connection":
        from jarvis.platform_runtime import runtime_connection_status

        return {"ok": True, "tab": "connection", "data": runtime_connection_status()}

    from aiplatform.mission_control.aggregator import get_tab as platform_tab

    return platform_tab(tab)


def format_overview_markdown() -> str:
    from aiplatform.mission_control.aggregator import format_overview_markdown as platform_md

    return platform_md()


def export_activity_csv(*, limit: int = 200) -> str:
    from aiplatform.mission_control.activity import export_csv

    return export_csv(limit=limit)


def health_summary(*, force: bool = False) -> dict[str, Any]:
    """Compact health for Automation / voice / status bar.

    Uses the shared lite Mission Control snapshot — never a second full platform collect.
    """
    from jarvis.mission_control_ops.health_brief import build_health_brief

    snap = collect_mission_control(record_metrics=False, force=force, enrich="lite")
    brief = snap.get("health_brief") or build_health_brief(snap)
    overall = str(brief.get("overall") or "unknown")
    severity = str(brief.get("severity") or "ok")
    unhealthy = overall in ("degraded", "critical") or severity in ("error", "critical")
    return {
        "ok": not unhealthy,
        "overall": overall,
        "severity": severity,
        "reason": brief.get("headline") or overall,
        "critical_issues": list(brief.get("critical_issues") or [])[:5],
        "dangerous": overall == "critical" or severity == "critical",
        "source": "mission_control",
        "cached": bool(snap.get("cached")),
    }


def invalidate_mission_control_cache() -> None:
    """Test / explicit refresh helper."""
    for bucket in (_RAW_CACHE, _LITE_CACHE, _FULL_CACHE):
        bucket["at"] = 0.0
        bucket["value"] = None
