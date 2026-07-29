"""Restore engine — opt-in boot restore + safe fallback."""

from __future__ import annotations

from typing import Any

from jarvis.layouts_product.apply import preview_apply, resolve_layout
from jarvis.layouts_product.schema import migrate_snapshot, validate_snapshot
from jarvis.layouts_product.store import load_settings, load_undo


def restore_plan() -> dict[str, Any]:
    settings = load_settings()
    active = settings.get("active_layout") or settings.get("default_layout") or ""
    if not settings.get("restore_on_boot"):
        return {
            "ok": True,
            "should_restore": False,
            "reason": "restore_on_boot_disabled",
            "settings": settings,
        }
    if not active:
        return {
            "ok": True,
            "should_restore": False,
            "reason": "no_active_layout",
            "settings": settings,
        }
    layout = resolve_layout(str(active))
    if not layout:
        return {
            "ok": False,
            "should_restore": False,
            "reason": "active_layout_missing",
            "active_layout": active,
            "fallback": "skip",
            "coach": "Active layout missing — open Layouts and pick a starter.",
            "settings": settings,
        }
    snap = migrate_snapshot(layout["snapshot"])
    errs = validate_snapshot(snap)
    if errs:
        return {
            "ok": False,
            "should_restore": False,
            "reason": "corrupt_snapshot",
            "validation": errs,
            "fallback": "skip",
            "coach": "Layout snapshot failed validation — skipped boot restore.",
            "settings": settings,
        }
    return {
        "ok": True,
        "should_restore": True,
        "layout_id": layout["id"],
        "label": layout["label"],
        "snapshot": snap,
        "settings": settings,
    }


def manual_restore_target(layout_id: str = "") -> dict[str, Any]:
    settings = load_settings()
    target = (layout_id or settings.get("active_layout") or "").strip()
    if not target:
        return {"ok": False, "error": "no_target"}
    return preview_apply(target)


def recovery_status() -> dict[str, Any]:
    settings = load_settings()
    undo = load_undo()
    steps = [
        {"id": "schema", "label": "Schema v1", "done": True},
        {"id": "catalog", "label": "Starter catalog", "done": True},
        {"id": "restore_pref", "label": "Restore preference set", "done": "restore_on_boot" in settings},
        {"id": "undo_available", "label": "Undo buffer", "done": undo is not None},
    ]
    return {
        "ready": True,
        "hint": "Enable Restore last layout in Settings → Layouts behavior, or Layouts modal.",
        "steps": steps,
        "settings": settings,
    }
