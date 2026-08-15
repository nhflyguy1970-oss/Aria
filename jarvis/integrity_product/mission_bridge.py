"""Mission Control bridge — Production Integrity status card."""

from __future__ import annotations

import time
from typing import Any

from jarvis.integrity_product.terminology import DISCLAIMER, TERMINOLOGY

_PANEL_CACHE: dict[str, Any] = {"at": 0.0, "value": None}
_PANEL_TTL_S = 30.0


def integrity_mission_panel() -> dict[str, Any]:
    now = time.monotonic()
    cached = _PANEL_CACHE.get("value")
    if isinstance(cached, dict) and now - float(_PANEL_CACHE.get("at") or 0) < _PANEL_TTL_S:
        return dict(cached)

    from jarvis.integrity_product import store
    from jarvis.integrity_product.scanner import home_payload

    home = home_payload()
    last = home.get("last_scan") or store.load_last_scan() or {}
    status = home.get("status") or last.get("status") or "unknown"
    state_map = {"clean": "ready", "warning": "attention", "attention": "critical"}
    state = state_map.get(status, home.get("state") or "unknown")
    counts = (last.get("counts") or {})
    hist = home.get("history") or []
    last_repair = home.get("last_repair")
    score = home.get("score") or (last.get("score") or {})
    panel = {
        "product": TERMINOLOGY["product"],
        "operator_name": TERMINOLOGY["operator_name"],
        "state": state,
        "status": status,
        "score": score,
        "integrity_score": (score or {}).get("overall"),
        "detail": (
            f"Score {(score or {}).get('overall', '—')}/100 · {status} · "
            f"{counts.get('total', 0)} artifact(s) · last scan {_fmt_ts(last.get('scanned_at'))}"
        ),
        "artifacts_found": counts.get("total", 0),
        "by_category": counts.get("by_category") or {},
        "sections": (score or {}).get("sections") or {},
        "pending_issues": counts.get("total", 0),
        "last_scan_at": last.get("scanned_at"),
        "last_repair": last_repair,
        "last_successful_cleanup": home.get("last_successful_cleanup"),
        "history": hist[:8],
        "findings_preview": [
            {"title": f.get("title"), "category": f.get("category"), "confidence": f.get("confidence")}
            for f in (last.get("findings") or [])[:8]
        ],
        "deep_links": {
            "scan": "/api/integrity/scan",
            "home": "/api/integrity/home",
            "mission": "/api/integrity/mission",
            "score": "/api/integrity/score",
            "repair": "mc:recovery",
        },
        "disclaimer": DISCLAIMER,
        "note": "Scans never auto-delete. Score is informational and never hides problems.",
    }
    _PANEL_CACHE["at"] = now
    _PANEL_CACHE["value"] = panel
    return dict(panel)


def _fmt_ts(ts: Any) -> str:
    try:
        t = float(ts or 0)
        if t <= 0:
            return "never"
        age = int(time.time() - t)
        if age < 120:
            return "just now"
        if age < 3600:
            return f"{age // 60}m ago"
        if age < 86400:
            return f"{age // 3600}h ago"
        return f"{age // 86400}d ago"
    except Exception:
        return "unknown"
