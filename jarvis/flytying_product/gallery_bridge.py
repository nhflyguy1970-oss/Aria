"""Gallery bridge — finished-fly photos link to recipes via Gallery metadata (never duplicate Gallery)."""

from __future__ import annotations

from typing import Any


def link_finished_fly(
    name: str,
    *,
    recipe_id: str = "",
    recipe_name: str = "",
    session_id: str = "",
    notes: str = "",
    collection: str = "Finished flies",
) -> dict[str, Any]:
    """
    Tag a Gallery image as a finished fly and optionally add to a collection.
    Storage stays in Gallery; Fly Tying only records history + recipe linkage.
    """
    from jarvis.config import is_uncensored
    from jarvis.flytying_product.history import add_entry
    from jarvis.gallery_product import collections as gal_cols
    from jarvis.gallery_product.metadata import set_meta

    filename = (name or "").strip()
    if not filename:
        return {"ok": False, "message": "name required"}

    meta = set_meta(
        filename,
        {
            "flytying": True,
            "finished_fly": True,
            "recipe_id": (recipe_id or "").strip(),
            "recipe_name": (recipe_name or "").strip(),
            "session_id": (session_id or "").strip(),
            "notes": (notes or "")[:2000],
            "source_product": "flytying",
        },
    )

    collection_id = ""
    if collection:
        listed = gal_cols.list_collections()
        cols = listed.get("items") if isinstance(listed, dict) else (listed or [])
        match = next(
            (c for c in (cols or []) if str(c.get("title") or "").lower() == collection.lower()),
            None,
        )
        if match:
            collection_id = str(match.get("id") or "")
        else:
            created = gal_cols.create_collection(collection, names=[filename])
            collection_id = str(created.get("id") or (created.get("collection") or {}).get("id") or "")
        if collection_id:
            try:
                gal_cols.add_to_collection(collection_id, filename)
            except Exception:
                pass

    entry = add_entry(
        {
            "kind": "gallery_link",
            "summary": f"Finished fly photo linked: {recipe_name or recipe_id or filename}",
            "recipe_id": recipe_id,
            "recipe_name": recipe_name,
            "session_id": session_id,
            "path": filename,
            "detail": notes[:2000] if notes else "",
            "source": "gallery_bridge",
            "uncensored_origin": bool(is_uncensored()),
            "meta": {"collection_id": collection_id},
        }
    )

    if session_id:
        try:
            from jarvis.flytying_product.sessions import update_session

            update_session(session_id, {"add_photo": filename})
        except Exception:
            pass

    return {
        "ok": True,
        "meta": (meta or {}).get("meta") or meta,
        "collection_id": collection_id,
        "history_id": entry.get("id"),
        "bridge": "gallery_product",
        "message": "Linked finished fly in Gallery metadata — Gallery owns storage.",
    }


def list_finished_fly_links(*, limit: int = 40) -> dict[str, Any]:
    from jarvis.gallery_product.metadata import _load

    rows = []
    for name, meta in (_load() or {}).items():
        if not isinstance(meta, dict):
            continue
        if meta.get("finished_fly") or meta.get("flytying"):
            rows.append({"name": name, **meta})
    rows.sort(key=lambda r: float(r.get("updated_at") or 0), reverse=True)
    return {"ok": True, "items": rows[: max(1, min(limit, 200))]}
