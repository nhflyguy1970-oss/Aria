"""Apply pipeline — validate + preview; chrome mutation is client-side."""

from __future__ import annotations

from typing import Any

from jarvis.layouts_product.catalog import get_builtin, list_builtins
from jarvis.layouts_product.schema import diff_snapshots, migrate_snapshot, validate_snapshot
from jarvis.layouts_product.store import (
    load_customs,
    load_settings,
    load_undo,
    push_history,
    save_settings,
    save_undo,
    upsert_custom,
)


def resolve_layout(layout_id: str) -> dict[str, Any] | None:
    lid = (layout_id or "").strip().lower()
    if not lid:
        return None
    builtin = get_builtin(lid)
    if builtin:
        return {
            "id": builtin["id"],
            "label": builtin["label"],
            "kind": builtin.get("kind") or "starter",
            "description": builtin.get("description") or "",
            "snapshot": builtin["snapshot"],
            "source": "builtin",
            "recommended_project": bool(builtin.get("recommended_project")),
        }
    customs = load_customs()
    if lid in customs:
        snap = customs[lid]
        return {
            "id": lid,
            "label": snap.get("label") or lid,
            "kind": "custom",
            "description": "Custom shell layout",
            "snapshot": snap,
            "source": "custom",
        }
    return None


def preview_apply(layout_id: str, *, current: dict[str, Any] | None = None) -> dict[str, Any]:
    layout = resolve_layout(layout_id)
    if not layout:
        return {"ok": False, "error": f"Unknown layout: {layout_id}"}
    snap = migrate_snapshot(layout["snapshot"])
    errs = validate_snapshot(snap)
    if errs:
        return {"ok": False, "error": "invalid_snapshot", "validation": errs}
    changes = diff_snapshots(current or {}, snap)
    return {
        "ok": True,
        "layout_id": layout["id"],
        "label": layout["label"],
        "kind": layout["kind"],
        "source": layout["source"],
        "snapshot": snap,
        "changes": changes,
        "change_count": len(changes),
        "recommended_project": layout.get("recommended_project"),
        "note": "Starter layouts are full frozen chrome snapshots — not partial overlays.",
    }


def commit_apply(
    layout_id: str,
    *,
    current: dict[str, Any] | None = None,
    client_ok: bool = True,
    detail: str = "",
) -> dict[str, Any]:
    preview = preview_apply(layout_id, current=current)
    if not preview.get("ok"):
        push_history(
            {
                "action": "apply",
                "layout_id": layout_id,
                "ok": False,
                "detail": preview.get("error") or "failed",
            }
        )
        return preview
    # Save undo = previous chrome snapshot from client
    if current:
        save_undo(
            {
                "layout_id": layout_id,
                "previous": migrate_snapshot(current),
                "label": preview.get("label"),
            }
        )
    settings = load_settings()
    settings["active_layout"] = preview["layout_id"]
    save_settings(settings)
    push_history(
        {
            "action": "apply",
            "layout_id": preview["layout_id"],
            "label": preview["label"],
            "ok": bool(client_ok),
            "detail": detail or f"Applied {preview['label']}",
            "changes": preview.get("changes") or [],
        }
    )
    return {**preview, "persisted": True, "active_layout": preview["layout_id"]}


def undo_last(*, current: dict[str, Any] | None = None) -> dict[str, Any]:
    undo = load_undo()
    if not undo or not undo.get("previous"):
        return {"ok": False, "error": "nothing_to_undo"}
    prev = migrate_snapshot(undo["previous"])
    errs = validate_snapshot(prev)
    if errs:
        return {"ok": False, "error": "corrupt_undo", "validation": errs}
    push_history(
        {
            "action": "undo",
            "layout_id": undo.get("layout_id") or "",
            "label": undo.get("label") or "previous",
            "ok": True,
            "detail": "Undo last layout apply",
            "changes": diff_snapshots(current or {}, prev),
        }
    )
    save_undo(None)
    return {"ok": True, "snapshot": prev, "label": "Previous layout", "action": "undo"}


def save_layout_from_client(name: str, snap: dict[str, Any], *, overwrite: bool = False) -> dict[str, Any]:
    lid = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in (name or "").strip().lower()).strip("-")[:40]
    if not lid:
        return {"ok": False, "error": "name_required"}
    customs = load_customs()
    settings = load_settings()
    if lid in customs and not overwrite and settings.get("confirm_overwrite", True):
        return {"ok": False, "error": "exists", "layout_id": lid, "needs_confirm": True}
    try:
        entry = upsert_custom(lid, snap, label=name.strip())
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    push_history({"action": "save", "layout_id": lid, "label": name.strip(), "ok": True})
    settings["active_layout"] = lid
    save_settings(settings)
    return {"ok": True, "layout": entry, "layout_id": lid}


def catalog_payload() -> dict[str, Any]:
    builtins = list_builtins()
    customs = load_customs()
    custom_list = []
    for cid, snap in customs.items():
        custom_list.append(
            {
                "id": cid,
                "label": snap.get("label") or cid,
                "kind": "custom",
                "description": "Custom shell layout",
                "snapshot": snap,
                "source": "custom",
            }
        )
    return {
        "builtins": [
            {
                "id": b["id"],
                "label": b["label"],
                "kind": b.get("kind") or "starter",
                "description": b.get("description") or "",
                "aliases": b.get("aliases") or [],
                "snapshot": b["snapshot"],
                "source": "builtin",
                "frozen": True,
                "honest_note": "Full frozen starter snapshot",
            }
            for b in builtins
        ],
        "customs": custom_list,
        "settings": load_settings(),
    }
