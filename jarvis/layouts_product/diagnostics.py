"""Layouts diagnostics + experimental coaches."""

from __future__ import annotations

from typing import Any

from jarvis.layouts_product.catalog import list_builtins
from jarvis.layouts_product.schema import SCHEMA_VERSION
from jarvis.layouts_product.store import load_customs, load_history, load_settings, load_undo
from jarvis.layouts_product.terminology import TERMINOLOGY


def health_summary() -> dict[str, Any]:
    customs = load_customs()
    settings = load_settings()
    hist = load_history(limit=10)
    failures = [h for h in hist if not h.get("ok")]
    return {
        "product": TERMINOLOGY["product"],
        "healthy": len(failures) == 0,
        "schema_version": SCHEMA_VERSION,
        "builtin_count": len(list_builtins()),
        "custom_count": len(customs),
        "active_layout": settings.get("active_layout") or "",
        "restore_on_boot": bool(settings.get("restore_on_boot")),
        "recent_failures": failures[-5:],
        "undo_available": load_undo() is not None,
        "version": "1.0.0",
    }


def project_layout_suggestion(*, project_slug: str = "", hints: dict[str, Any] | None = None) -> dict[str, Any]:
    """Non-forcing recommendation — Projects remain authoritative."""
    hints = hints or {}
    slug = (project_slug or "").lower()
    codingish = any(x in slug for x in ("code", "dev", "app", "api", "jarvis", "aria")) or hints.get("coding")
    if codingish:
        return {
            "ok": True,
            "experimental": False,
            "recommend": "coding",
            "layout_id": "coding",
            "layout_name": "Coding",
            "message": "This project may work well with the Coding layout.",
            "force": False,
            "note": "Operator chooses — Layouts never auto-switch Projects or layouts.",
        }
    return {
        "ok": True,
        "recommend": None,
        "layout_id": None,
        "layout_name": None,
        "message": "",
        "force": False,
    }


def intent_coach(query: str = "") -> dict[str, Any]:
    q = (query or "").lower()
    mapping = [
        (("code", "pr", "git", "lsp"), "coding"),
        (("write", "journal", "draft"), "writing"),
        (("research", "browse", "web"), "research"),
        (("plan", "task", "calendar"), "planning"),
        (("image", "gallery", "video"), "media"),
        (("fly", "hackle"), "flytying"),
        (("home", "brief", "dashboard"), "home"),
        (("ops", "mission", "provider"), "role-operations"),
    ]
    for keys, layout_id in mapping:
        if any(k in q for k in keys):
            return {
                "ok": True,
                "experimental": True,
                "suggest": layout_id,
                "message": f"Consider the {layout_id} layout.",
                "auto_apply": False,
            }
    return {"ok": True, "experimental": True, "suggest": None, "auto_apply": False}


def voice_switch_script(layout_id: str) -> dict[str, Any]:
    from jarvis.layouts_product.apply import resolve_layout

    layout = resolve_layout(layout_id)
    if not layout:
        return {"ok": False, "experimental": True, "error": "unknown_layout"}
    return {
        "ok": True,
        "experimental": True,
        "script": f"Switching to the {layout['label']} layout.",
        "layout_id": layout["id"],
        "note": "Voice owns TTS; Layouts provides the apply target. Never auto-spoken without operator intent.",
    }
