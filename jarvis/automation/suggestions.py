"""Learned workflow suggestions — never auto-enable."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

from jarvis.automation.paths import SUGGESTIONS_FILE, ensure_dirs


def _load() -> list[dict[str, Any]]:
    ensure_dirs()
    if not SUGGESTIONS_FILE.is_file():
        return []
    try:
        data = json.loads(SUGGESTIONS_FILE.read_text(encoding="utf-8"))
        return list(data.get("suggestions") or [])
    except Exception:
        return []


def _save(items: list[dict[str, Any]]) -> None:
    ensure_dirs()
    try:
        from jarvis.live_data_guard import assert_live_write_allowed

        assert_live_write_allowed(SUGGESTIONS_FILE)
    except Exception:
        pass
    SUGGESTIONS_FILE.write_text(json.dumps({"suggestions": items[:100]}, indent=2), encoding="utf-8")


def list_suggestions(*, include_dismissed: bool = False) -> list[dict[str, Any]]:
    items = _load()
    if include_dismissed:
        return items
    return [s for s in items if not s.get("dismissed") and not s.get("enabled")]


def propose_from_scan(workflows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Turn scan results into suggestions requiring user approval."""
    existing = _load()
    by_slug = {s.get("slug"): s for s in existing}
    created = []
    for w in workflows or []:
        slug = w.get("slug") or ""
        if not slug:
            continue
        if slug in by_slug and not by_slug[slug].get("dismissed"):
            continue
        sug = {
            "id": f"sug_{uuid.uuid4().hex[:10]}",
            "slug": slug,
            "title": f"Automate: {w.get('name') or slug}",
            "explanation": (
                f"Seen {w.get('count', 1)}× with {len(w.get('steps') or [])} steps. "
                "Review, dry-run, then enable — never auto-enabled."
            ),
            "workflow": w,
            "created_at": time.time(),
            "dismissed": False,
            "enabled": False,
            "status": "suggested",
        }
        existing.insert(0, sug)
        created.append(sug)
    _save(existing)
    return created


def dismiss(suggestion_id: str) -> dict[str, Any]:
    items = _load()
    for s in items:
        if s.get("id") == suggestion_id:
            s["dismissed"] = True
            s["status"] = "dismissed"
            _save(items)
            return {"ok": True, "suggestion": s}
    return {"ok": False, "error": "not_found"}


def mark_promoted(suggestion_id: str) -> dict[str, Any]:
    items = _load()
    for s in items:
        if s.get("id") == suggestion_id:
            s["enabled"] = True
            s["status"] = "promoted"
            _save(items)
            return {"ok": True, "suggestion": s}
    return {"ok": False, "error": "not_found"}
