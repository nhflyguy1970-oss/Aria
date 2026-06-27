"""User fly-tying data: materials inventory, favorites, queue, notes."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.flytying.barcode import barcode_kind, normalize_barcode

MATERIALS_FILE = DATA_DIR / "flytying_materials.json"
FAVORITES_FILE = DATA_DIR / "flytying_favorites.json"
QUEUE_FILE = DATA_DIR / "flytying_queue.json"
NOTES_FILE = DATA_DIR / "flytying_notes.json"


def _read(path, default):
    if not path.is_file():
        return default
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, type(default)) else default
    except (OSError, json.JSONDecodeError):
        return default


def _write(path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_item_id() -> str:
    return f"m-{uuid.uuid4().hex[:10]}"


def compose_material_name(
    what: str,
    *,
    color: str = "",
    size: str = "",
    brand: str = "",
) -> str:
    """Build a recipe-matching label, e.g. olive 14 dry hook (Uni)."""
    w = (what or "").strip()
    if not w:
        return ""
    lead = [p for p in ((color or "").strip(), (size or "").strip()) if p]
    desc = " ".join(lead + [w])
    b = (brand or "").strip()
    if b and b.lower() not in desc.lower():
        desc = f"{desc} ({b})"
    return desc


def _ensure_item_name(item: dict[str, Any]) -> dict[str, Any]:
    row = dict(item)
    what = str(row.get("what") or "").strip()
    name = str(row.get("name") or "").strip()
    if not what and name:
        row["what"] = name
        what = name
    if what:
        row["name"] = compose_material_name(
            what,
            color=str(row.get("color") or ""),
            size=str(row.get("size") or ""),
            brand=str(row.get("brand") or ""),
        ) or name or what
    elif name:
        row["name"] = name
    return row


def _item_key(item: dict[str, Any]) -> str:
    row = _ensure_item_name(item)
    return str(row.get("name") or "").strip().lower()


def _structured_entry(
    what: str,
    *,
    color: str = "",
    size: str = "",
    brand: str = "",
    notes: str = "",
    source: str = "manual",
    barcode: str = "",
) -> dict[str, Any]:
    w = (what or "").strip()
    entry: dict[str, Any] = {
        "id": _new_item_id(),
        "what": w,
        "color": (color or "").strip(),
        "size": (size or "").strip(),
        "brand": (brand or "").strip(),
        "source": (source or "manual").strip() or "manual",
        "added_at": _now(),
    }
    if notes:
        entry["notes"] = (notes or "").strip()
    code = normalize_barcode(barcode) if barcode else ""
    if code:
        entry["barcode"] = code
        entry["barcode_kind"] = barcode_kind(code)
    return _ensure_item_name(entry)


def _load_inventory_raw() -> dict[str, Any]:
    if not MATERIALS_FILE.is_file():
        return {"version": 2, "items": []}
    try:
        raw = json.loads(MATERIALS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 2, "items": []}
    if isinstance(raw, list):
        items = []
        for m in raw:
            name = str(m).strip()
            if name:
                items.append(
                    {
                        "id": _new_item_id(),
                        "name": name,
                        "source": "manual",
                        "added_at": _now(),
                    }
                )
        store = {"version": 2, "items": items}
        _write(MATERIALS_FILE, store)
        return store
    if isinstance(raw, dict) and isinstance(raw.get("items"), list):
        return raw
    return {"version": 2, "items": []}


def _save_inventory_items(items: list[dict[str, Any]]) -> None:
    _write(MATERIALS_FILE, {"version": 2, "items": items[-500:]})


def list_inventory_items() -> list[dict[str, Any]]:
    store = _load_inventory_raw()
    items = store.get("items") or []
    out: list[dict[str, Any]] = []
    for i in items:
        if not isinstance(i, dict):
            continue
        row = _ensure_item_name(dict(i))
        if str(row.get("name") or "").strip() or str(row.get("what") or "").strip():
            out.append(row)
    return out


def list_materials() -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for item in list_inventory_items():
        name = str(item.get("name") or "").strip()
        low = name.lower()
        if name and low not in seen:
            seen.add(low)
            names.append(name)
    return names


def save_materials(materials: list[str]) -> dict[str, Any]:
    """Merge manual material names into inventory (legacy textarea save)."""
    items = list_inventory_items()
    by_name = {str(i.get("name") or "").strip().lower(): i for i in items}
    added = 0
    for m in materials or []:
        name = str(m).strip()
        low = name.lower()
        if not name or low in by_name:
            continue
        entry = {
            "id": _new_item_id(),
            "what": name,
            "name": name,
            "source": "manual",
            "added_at": _now(),
        }
        items.append(entry)
        by_name[low] = entry
        added += 1
    _save_inventory_items(items)
    names = list_materials()
    return {"ok": True, "materials": names, "inventory": items, "count": len(names), "added": added}


def replace_materials(materials: list[str]) -> dict[str, Any]:
    """Replace inventory with an exact name list (used when removing items)."""
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for m in materials or []:
        name = str(m).strip()
        low = name.lower()
        if not name or low in seen:
            continue
        seen.add(low)
        items.append(
            {
                "id": _new_item_id(),
                "what": name,
                "name": name,
                "source": "manual",
                "added_at": _now(),
            }
        )
    _save_inventory_items(items)
    names = list_materials()
    return {"ok": True, "materials": names, "inventory": items, "count": len(names), "replaced": True}


def replace_inventory_items(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Replace inventory with structured rows (client sync / legacy fallback)."""
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in rows or []:
        if not isinstance(raw, dict):
            continue
        what = str(raw.get("what") or raw.get("name") or "").strip()
        if not what:
            continue
        entry = _structured_entry(
            what,
            color=str(raw.get("color") or ""),
            size=str(raw.get("size") or ""),
            brand=str(raw.get("brand") or ""),
            notes=str(raw.get("notes") or ""),
            source=str(raw.get("source") or "manual"),
            barcode=str(raw.get("barcode") or ""),
        )
        if raw.get("id"):
            entry["id"] = str(raw["id"])
        key = _item_key(entry)
        if not key or key in seen:
            continue
        seen.add(key)
        items.append(entry)
    _save_inventory_items(items)
    names = list_materials()
    return {"ok": True, "materials": names, "inventory": items, "count": len(names), "replaced": True}


def add_structured_item(
    what: str,
    *,
    color: str = "",
    size: str = "",
    brand: str = "",
    notes: str = "",
    source: str = "manual",
    barcode: str = "",
) -> dict[str, Any]:
    w = (what or "").strip()
    if not w:
        return {"ok": False, "message": "what required"}
    entry = _structured_entry(
        w,
        color=color,
        size=size,
        brand=brand,
        notes=notes,
        source=source,
        barcode=barcode,
    )
    key = _item_key(entry)
    items = list_inventory_items()
    for item in items:
        if _item_key(item) == key:
            return {"ok": True, "item": item, "merged": True, "inventory": items, "materials": list_materials()}
    items.append(entry)
    _save_inventory_items(items)
    return {"ok": True, "item": entry, "merged": False, "inventory": items, "materials": list_materials()}


def update_inventory_item(item_id: str, fields: dict[str, Any]) -> dict[str, Any]:
    iid = (item_id or "").strip()
    if not iid:
        return {"ok": False, "message": "item_id required"}
    items = list_inventory_items()
    target: dict[str, Any] | None = None
    for item in items:
        if str(item.get("id") or "") == iid:
            target = item
            break
    if target is None:
        return {"ok": False, "message": "not found"}
    old_key = _item_key(target)
    for key in ("what", "color", "size", "brand", "notes", "barcode", "source"):
        if key in fields:
            target[key] = str(fields.get(key) or "").strip()
    if str(target.get("what") or "").strip():
        updated = _ensure_item_name(target)
        target.clear()
        target.update(updated)
    elif fields.get("name"):
        target["name"] = str(fields.get("name") or "").strip()
    new_key = _item_key(target)
    if new_key and new_key != old_key:
        for item in items:
            if str(item.get("id") or "") != iid and _item_key(item) == new_key:
                return {"ok": False, "message": "duplicate material"}
    target["updated_at"] = _now()
    _save_inventory_items(items)
    return {"ok": True, "item": target, "inventory": items, "materials": list_materials()}


def find_inventory_item(*, item_id: str = "", barcode: str = "") -> dict[str, Any] | None:
    iid = (item_id or "").strip()
    code = normalize_barcode(barcode) if barcode else ""
    for item in list_inventory_items():
        if iid and str(item.get("id") or "") == iid:
            return item
        if code and normalize_barcode(str(item.get("barcode") or "")) == code:
            return item
    return None


def add_inventory_item(
    name: str,
    *,
    what: str = "",
    color: str = "",
    size: str = "",
    barcode: str = "",
    source: str = "manual",
    brand: str = "",
    qty: int | None = None,
    notes: str = "",
    merge_on_barcode: bool = True,
) -> dict[str, Any]:
    w = (what or "").strip()
    if w:
        return add_structured_item(
            w,
            color=color,
            size=size,
            brand=brand,
            notes=notes,
            source=source,
            barcode=barcode,
        )
    label = (name or "").strip()
    if not label:
        return {"ok": False, "message": "name required"}
    code = normalize_barcode(barcode) if barcode else ""
    items = list_inventory_items()
    now = _now()

    if merge_on_barcode and code:
        for item in items:
            if normalize_barcode(str(item.get("barcode") or "")) == code:
                item["name"] = label
                item["last_scanned_at"] = now
                if brand:
                    item["brand"] = brand
                if notes:
                    item["notes"] = notes
                if qty is not None:
                    item["qty"] = int(qty)
                elif item.get("qty") is not None:
                    try:
                        item["qty"] = int(item.get("qty") or 0) + 1
                    except (TypeError, ValueError):
                        item["qty"] = 1
                _save_inventory_items(items)
                return {"ok": True, "item": item, "merged": True, "inventory": items, "materials": list_materials()}

    low = label.lower()
    for item in items:
        if not code and str(item.get("name") or "").strip().lower() == low:
            item["last_scanned_at"] = now
            _save_inventory_items(items)
            return {"ok": True, "item": item, "merged": True, "inventory": items, "materials": list_materials()}

    entry: dict[str, Any] = _ensure_item_name(
        {
            "id": _new_item_id(),
            "what": label,
            "name": label,
            "source": (source or "manual").strip() or "manual",
            "added_at": now,
            "last_scanned_at": now if code else None,
            "brand": brand,
            "notes": notes,
        }
    )
    if code:
        entry["barcode"] = code
        entry["barcode_kind"] = barcode_kind(code)
    if qty is not None:
        entry["qty"] = int(qty)
    items.append(entry)
    _save_inventory_items(items)
    return {"ok": True, "item": entry, "merged": False, "inventory": items, "materials": list_materials()}


def remove_inventory_item(item_id: str) -> dict[str, Any]:
    iid = (item_id or "").strip()
    if not iid:
        return {"ok": False, "message": "item_id required"}
    items = [i for i in list_inventory_items() if str(i.get("id") or "") != iid]
    _save_inventory_items(items)
    return {"ok": True, "item_id": iid, "inventory": items, "materials": list_materials()}


def scan_barcode_into_inventory(
    raw_barcode: str,
    *,
    name: str = "",
    brand: str = "",
    learn: bool = True,
    online_lookup: bool = True,
) -> dict[str, Any]:
    from jarvis.flytying.barcode import learn_barcode_mapping, lookup_barcode

    code = normalize_barcode(raw_barcode)
    if not code:
        return {"ok": False, "message": "barcode required"}

    lookup = lookup_barcode(code, online=online_lookup)
    resolved_name = (name or "").strip() or str(lookup.get("name") or "").strip()
    resolved_brand = (brand or "").strip() or str(lookup.get("brand") or "").strip()

    if not resolved_name:
        return {
            "ok": True,
            "added": False,
            "lookup": lookup,
            "barcode": code,
            "needs_name": True,
            "message": lookup.get("message") or "Name this barcode to add it to inventory.",
        }

    if learn and resolved_name:
        if name or not lookup.get("found"):
            learn_barcode_mapping(code, resolved_name, brand=resolved_brand)
        elif lookup.get("source") not in ("local_map",):
            learn_barcode_mapping(code, resolved_name, brand=resolved_brand)

    source = "scan_upc" if lookup.get("kind") in ("upc_ean", "ean") else "scan_custom"
    if code.startswith("FT:"):
        source = "scan_custom"
    add_result = add_structured_item(
        resolved_name,
        brand=resolved_brand,
        source=source,
        barcode=code,
    )
    if not add_result.get("ok"):
        add_result = add_inventory_item(
            resolved_name,
            what=resolved_name,
            barcode=code,
            source=source,
            brand=resolved_brand,
            merge_on_barcode=True,
        )
    return {
        "ok": True,
        "added": True,
        "lookup": lookup,
        "barcode": code,
        "needs_name": False,
        **add_result,
    }


def list_favorites() -> list[str]:
    rows = _read(FAVORITES_FILE, [])
    return [str(r).strip() for r in rows if str(r).strip()] if isinstance(rows, list) else []


def toggle_favorite(recipe_id: str) -> dict[str, Any]:
    rid = (recipe_id or "").strip()
    if not rid:
        return {"ok": False, "message": "recipe_id required"}
    favs = list_favorites()
    if rid in favs:
        favs.remove(rid)
        added = False
    else:
        favs.append(rid)
        added = True
    _write(FAVORITES_FILE, favs)
    return {"ok": True, "recipe_id": rid, "favorited": added, "favorites": favs}


def list_queue() -> list[dict[str, Any]]:
    rows = _read(QUEUE_FILE, [])
    return rows if isinstance(rows, list) else []


def add_to_queue(recipe_id: str, *, name: str = "") -> dict[str, Any]:
    rid = (recipe_id or "").strip()
    if not rid:
        return {"ok": False, "message": "recipe_id required"}
    queue = list_queue()
    if any(str(q.get("recipe_id") or "") == rid for q in queue):
        return {"ok": True, "message": "already queued", "queue": queue}
    queue.append(
        {
            "recipe_id": rid,
            "name": (name or "").strip(),
            "added_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    _write(QUEUE_FILE, queue[-50:])
    return {"ok": True, "queue": queue}


def remove_from_queue(recipe_id: str) -> dict[str, Any]:
    rid = (recipe_id or "").strip()
    queue = [q for q in list_queue() if str(q.get("recipe_id") or "") != rid]
    _write(QUEUE_FILE, queue)
    return {"ok": True, "queue": queue}


def get_note(recipe_id: str) -> str:
    notes = _read(NOTES_FILE, {})
    if not isinstance(notes, dict):
        return ""
    return str(notes.get(recipe_id) or "")


def save_note(recipe_id: str, text: str) -> dict[str, Any]:
    rid = (recipe_id or "").strip()
    if not rid:
        return {"ok": False, "message": "recipe_id required"}
    notes = _read(NOTES_FILE, {})
    if not isinstance(notes, dict):
        notes = {}
    text = (text or "").strip()
    if text:
        notes[rid] = text
    else:
        notes.pop(rid, None)
    _write(NOTES_FILE, notes)
    return {"ok": True, "recipe_id": rid, "note": text}


def user_state() -> dict[str, Any]:
    return {
        "materials": list_materials(),
        "inventory": list_inventory_items(),
        "favorites": list_favorites(),
        "queue": list_queue(),
        "notes_count": len(_read(NOTES_FILE, {}) if NOTES_FILE.is_file() else {}),
    }
