"""Predictive health warnings — display only, never auto-remediate."""

from __future__ import annotations

from typing import Any


def build_predictive_warnings(snapshot: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Detect resource trends / repeated failures / latency growth / storage risk."""
    d = snapshot or {}
    warnings: list[dict[str, Any]] = []
    hw = d.get("hardware") or {}
    ov = d.get("overview") or {}
    routing = d.get("routing_stats") or {}
    perf = d.get("performance") or {}
    activity = (d.get("activity") or {}).get("events") or []

    ram_free = hw.get("ram_available_gb")
    ram_total = hw.get("ram_total_gb")
    try:
        if ram_free is not None and ram_total and float(ram_total) > 0:
            pct = float(ram_free) / float(ram_total)
            if pct < 0.12:
                warnings.append(
                    {
                        "id": "ram_exhaustion",
                        "severity": "warning",
                        "title": "RAM approaching exhaustion",
                        "detail": f"Only {ram_free} GB free of {ram_total} GB",
                        "suggested_fix": "Close unused models or free memory via Inference / Memory tabs",
                    }
                )
    except (TypeError, ValueError):
        pass

    disk = hw.get("disk_free_gb")
    try:
        if disk is not None and float(disk) < 10:
            warnings.append(
                {
                    "id": "storage_exhaustion",
                    "severity": "warning" if float(disk) >= 5 else "error",
                    "title": "Storage nearing exhaustion",
                    "detail": f"{disk} GB free on primary volume",
                    "suggested_fix": "Free disk space before long-running jobs",
                }
            )
    except (TypeError, ValueError):
        pass

    vram = hw.get("free_vram_mb")
    try:
        if vram is not None and float(vram) < 1024:
            warnings.append(
                {
                    "id": "vram_pressure",
                    "severity": "warning",
                    "title": "VRAM pressure",
                    "detail": f"{vram} MB VRAM free",
                    "suggested_fix": "Unload unused models (approved action)",
                }
            )
    except (TypeError, ValueError):
        pass

    err_pct = routing.get("error_pct")
    try:
        if err_pct is not None and float(err_pct) >= 15:
            warnings.append(
                {
                    "id": "routing_errors",
                    "severity": "warning",
                    "title": "Elevated routing errors",
                    "detail": f"Routing error rate {err_pct}%",
                    "suggested_fix": "Open Routing inspector and review recent failures",
                }
            )
    except (TypeError, ValueError):
        pass

    avg_lat = routing.get("average_latency_ms")
    try:
        if avg_lat is not None and float(avg_lat) >= 2500:
            warnings.append(
                {
                    "id": "latency_growth",
                    "severity": "warning",
                    "title": "Latency growth",
                    "detail": f"Average routing latency {avg_lat} ms",
                    "suggested_fix": "Check Inference provider and hardware load",
                }
            )
    except (TypeError, ValueError):
        pass

    # Repeated failures in recent MC activity stream
    fail_types: dict[str, int] = {}
    for ev in activity[-50:]:
        status = str((ev or {}).get("status") or "").lower()
        typ = str((ev or {}).get("type") or (ev or {}).get("component") or "event")
        if status in ("error", "failed", "down", "critical"):
            fail_types[typ] = fail_types.get(typ, 0) + 1
    for typ, count in fail_types.items():
        if count >= 3:
            warnings.append(
                {
                    "id": f"repeated_{typ}",
                    "severity": "warning",
                    "title": "Repeated failures",
                    "detail": f"{typ} failed {count} times in recent events",
                    "suggested_fix": "Open Operations Event Log and correlate with Recovery",
                }
            )

    # Performance trend: rising p50
    trends = perf.get("trends") or {}
    for key, label in (
        ("mission_control_ms", "Mission Control"),
        ("aria_ms", "Aria"),
        ("routing_write_ms", "Routing write"),
    ):
        block = trends.get(key) or {}
        latest = block.get("latest_p50_ms")
        prev = block.get("previous_p50_ms") or block.get("baseline_p50_ms")
        try:
            if latest is not None and prev is not None and float(prev) > 0:
                growth = (float(latest) - float(prev)) / float(prev)
                if growth >= 0.5:
                    warnings.append(
                        {
                            "id": f"perf_{key}",
                            "severity": "info",
                            "title": f"{label} latency trend up",
                            "detail": f"p50 {prev} → {latest} ms",
                            "suggested_fix": "Review Performance tab; do not auto-tune",
                        }
                    )
        except (TypeError, ValueError):
            pass

    cpu = hw.get("cpu_load") if hw.get("cpu_load") is not None else ov.get("cpu_load")
    try:
        if cpu is not None and float(cpu) >= 4.0:
            warnings.append(
                {
                    "id": "cpu_load",
                    "severity": "info",
                    "title": "High CPU load",
                    "detail": f"Load average {cpu}",
                    "suggested_fix": "Defer heavy automation until load drops",
                }
            )
    except (TypeError, ValueError):
        pass

    return warnings[:12]
