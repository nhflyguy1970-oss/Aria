"""Inventory facade over user_store + low-stock heuristics + recent scans."""

from __future__ import annotations

from typing import Any


def inventory_summary() -> dict[str, Any]:
    from jarvis.flytying.user_store import list_inventory_items, list_materials, user_state

    items = list_inventory_items()
    materials = list_materials()
    low = low_stock_items(items)
    scans = recent_scans(limit=8)
    state = user_state()
    return {
        "ok": True,
        "count": len(items),
        "materials_count": len(materials),
        "items": items,
        "low_stock": low,
        "recent_scans": scans,
        "favorites": state.get("favorites") or [],
        "queue": state.get("queue") or [],
    }


def low_stock_items(items: list[dict[str, Any]] | None = None, *, threshold: int = 1) -> list[dict[str, Any]]:
    if items is None:
        from jarvis.flytying.user_store import list_inventory_items

        items = list_inventory_items()
    out: list[dict[str, Any]] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        qty = item.get("qty")
        if qty is None:
            # Heuristic: flagged notes or explicit low_stock
            notes = str(item.get("notes") or "").lower()
            if item.get("low_stock") or "low stock" in notes or "running low" in notes:
                out.append(dict(item))
            continue
        try:
            if int(qty) <= int(threshold):
                row = dict(item)
                row["low_stock"] = True
                out.append(row)
        except (TypeError, ValueError):
            continue
    return out


def recent_scans(*, limit: int = 10) -> list[dict[str, Any]]:
    """Recent barcode map learnings by learned_at timestamp when available."""
    from jarvis.flytying.barcode import list_barcode_mappings

    rows: list[dict[str, Any]] = []
    try:
        data = list_barcode_mappings()
    except Exception:
        return []
    for code, val in (data or {}).items():
        if not isinstance(val, dict):
            continue
        rows.append(
            {
                "barcode": code,
                "name": val.get("name") or "",
                "brand": val.get("brand") or "",
                "learned_at": val.get("learned_at") or "",
                "kind": val.get("kind") or "",
            }
        )
    rows.sort(key=lambda r: str(r.get("learned_at") or ""), reverse=True)
    return rows[: max(1, min(limit, 50))]


def list_items() -> list[dict[str, Any]]:
    from jarvis.flytying.user_store import list_inventory_items

    return list_inventory_items()
