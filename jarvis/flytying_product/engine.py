"""One Fly Tying engine — product status + action helpers over jarvis.flytying.*."""

from __future__ import annotations

from typing import Any

from jarvis.flytying_product.terminology import BOUNDARIES, TERMINOLOGY


def product_status() -> dict[str, Any]:
    from jarvis.flytying import bridge
    from jarvis.flytying_product.history import list_history
    from jarvis.flytying_product.profiles import active_profile_id, list_profiles
    from jarvis.flytying_product.sessions import active_session
    from jarvis.flytying_product.settings import load_settings
    from jarvis.flytying_product.status_bus import get_flytying_state

    st: dict[str, Any] = {}
    try:
        st = bridge.status()
    except Exception as exc:
        st = {"ok": False, "error": str(exc)}
    recovery = recovery_status()
    session = None
    try:
        session = active_session()
    except Exception:
        session = None
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "boundaries": BOUNDARIES,
        "state": get_flytying_state(),
        "settings": load_settings(),
        "profiles": {"active": active_profile_id(), "count": len(list_profiles())},
        "session": session,
        "bridge": st,
        "recovery": recovery,
        "history_recent": list_history(limit=5),
        "pipeline": [
            "pattern_library",
            "inventory",
            "barcode",
            "vision",
            "voice",
            "planner",
            "gallery",
            "documents",
            "flytying_engine",
            "search",
            "suggestions",
            "recipe",
            "session",
            "history",
            "mission_control",
            "completion",
        ],
    }


def recovery_status() -> dict[str, Any]:
    """Guided Blackfly setup — paths + enablement, not admin jargon first."""
    from jarvis.flytying.config import (
        blackfly_enablement,
        gold_recipes_path,
        scraped_dataset_path,
        flytying_root,
        images_root,
    )

    enablement = blackfly_enablement()
    scraped = scraped_dataset_path()
    gold = gold_recipes_path()
    root = flytying_root()
    steps: list[dict[str, Any]] = []
    data_ok = bool(enablement.get("data_available"))
    rag_ok = bool(enablement.get("rag_available"))
    modules_ok = bool(enablement.get("has_blackfly_modules"))

    if not data_ok:
        steps.append(
            {
                "id": "mount_dataset",
                "label": "Locate Blackfly recipe dataset",
                "done": False,
                "detail": (
                    f"Expected scraped JSONL at {scraped}. "
                    "Set JARVIS_FLYTYING_ROOT or mount the Blackfly project."
                ),
            }
        )
    else:
        steps.append(
            {
                "id": "mount_dataset",
                "label": "Recipe dataset found",
                "done": True,
                "detail": f"{enablement.get('record_count') or 0} records at {enablement.get('scraped_db_path')}",
            }
        )

    steps.append(
        {
            "id": "blackfly_modules",
            "label": "Blackfly Python modules",
            "done": modules_ok,
            "detail": str(root) if modules_ok else "Need blackfly_rag.py and blackfly_gold.py in project root",
        }
    )
    steps.append(
        {
            "id": "semantic_rag",
            "label": "Semantic search (optional)",
            "done": rag_ok,
            "detail": "blackfly_rag importable" if rag_ok else "Keyword search still works without RAG",
        }
    )
    steps.append(
        {
            "id": "gold_optional",
            "label": "Gold quality filter (optional)",
            "done": gold.is_file(),
            "detail": str(gold) if gold.is_file() else "Build gold from scraped dataset when ready",
        }
    )
    images = images_root()
    steps.append(
        {
            "id": "images",
            "label": "Recipe images folder",
            "done": images.is_dir(),
            "detail": str(images),
        }
    )

    ready = data_ok
    return {
        "ok": True,
        "ready": ready,
        "guided": True,
        "enablement": enablement,
        "paths": {
            "project_root": str(root),
            "scraped": str(scraped),
            "gold": str(gold),
            "images": str(images),
        },
        "steps": steps,
        "hint": enablement.get("hint") or ("Ready" if ready else "Follow guided setup steps"),
        "deep_links": {
            "status": "/api/flytying/product",
            "library": "/api/flytying/library/status",
            "home": "#flytying",
        },
    }


def search_patterns(
    q: str = "",
    *,
    fly_type: str = "",
    limit: int = 20,
    offset: int = 0,
    min_quality: float | None = None,
    favorites_only: bool = False,
    hook_size: int | None = None,
) -> dict[str, Any]:
    from jarvis.flytying import bridge
    from jarvis.flytying.search import unified_search
    from jarvis.flytying_product.settings import load_settings
    from jarvis.flytying_product.status_bus import set_flytying_state

    settings = load_settings()
    mq = settings.get("min_quality") if min_quality is None else min_quality
    set_flytying_state("searching", detail=q or fly_type or "browse")
    try:
        if not bridge.gold_available():
            return {"ok": False, "message": "Blackfly scraped database missing", "loaded": False, **recovery_status()}
        payload = unified_search(
            q,
            fly_type=fly_type or None,
            limit=max(1, min(limit, 200)),
            offset=max(0, offset),
            min_quality=float(mq or 0),
            favorites_only=favorites_only,
            hook_size=hook_size or None,
        )
        return {"ok": True, **payload}
    finally:
        set_flytying_state("idle", detail="search_done")


def get_recipe(name_or_id: str) -> dict[str, Any] | None:
    from jarvis.flytying import bridge

    return bridge.get_recipe(name_or_id)


def suggest_from_materials(
    materials: list[str] | None = None,
    *,
    limit: int = 8,
    source: str = "api",
) -> dict[str, Any]:
    from jarvis.config import is_uncensored
    from jarvis.flytying import bridge
    from jarvis.flytying.user_store import list_inventory_items, list_materials
    from jarvis.flytying_product.history import add_entry
    from jarvis.flytying_product.status_bus import set_flytying_state

    mats = [str(m).strip() for m in (materials or []) if str(m).strip()]
    if not mats:
        mats = list_materials()
        if not mats:
            mats = [str(i.get("name") or "").strip() for i in list_inventory_items() if i.get("name")]
    set_flytying_state("suggesting", detail=f"{len(mats)} materials")
    try:
        hits = bridge.suggest_from_materials(mats, limit=limit)
        entry = add_entry(
            {
                "kind": "suggestion",
                "summary": f"Suggested {len(hits)} patterns from {len(mats)} materials",
                "materials": mats[:40],
                "matches": [
                    {"id": h.get("id") or h.get("recipe_id"), "name": h.get("name") or h.get("fly_name")}
                    for h in (hits or [])[:12]
                    if isinstance(h, dict)
                ],
                "source": source,
                "uncensored_origin": bool(is_uncensored()),
            }
        )
        return {
            "ok": True,
            "materials": mats,
            "matches": hits,
            "history_id": entry.get("id"),
        }
    finally:
        set_flytying_state("idle", detail="suggest_done")


def compare_recipes(recipe_ids: list[str]) -> dict[str, Any]:
    from jarvis.flytying import bridge

    return bridge.compare_recipes_by_id([str(i).strip() for i in recipe_ids if str(i).strip()])


def seasonal_suggestions(*, month: int | None = None, limit: int = 8) -> dict[str, Any]:
    from jarvis.flytying import bridge

    return bridge.seasonal_suggestions(month=month, limit=limit)


def home_payload() -> dict[str, Any]:
    """Fly Tying Home — inventory-first overview for operators (not admin chrome)."""
    from jarvis.flytying.hatch import hatch_context
    from jarvis.flytying_product.inventory import inventory_summary
    from jarvis.flytying_product.profiles import active_profile_id
    from jarvis.flytying_product.sessions import active_session

    recovery = recovery_status()
    inv: dict[str, Any] = {"ok": False, "count": 0, "low_stock": [], "queue": [], "recent_scans": []}
    try:
        inv = inventory_summary()
    except Exception as exc:
        inv = {**inv, "error": str(exc)}

    potd: dict[str, Any] = {"ok": False}
    try:
        from jarvis.flytying.nightly import pattern_of_the_day

        potd = pattern_of_the_day()
    except Exception as exc:
        potd = {"ok": False, "message": str(exc)}

    hatch: dict[str, Any] = {}
    try:
        hatch = hatch_context()
    except Exception:
        hatch = {"region": "", "hatches": []}

    session = None
    try:
        session = active_session()
    except Exception:
        session = None

    health = {
        "ready": recovery.get("ready"),
        "hint": recovery.get("hint"),
        "record_count": (recovery.get("enablement") or {}).get("record_count"),
    }

    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "inventory": inv,
        "pattern_of_the_day": potd,
        "session": session,
        "hatch": hatch,
        "recovery": recovery,
        "health": health,
        "active_profile": active_profile_id(),
        "deep_links": {
            "inventory": "#flytying",
            "mission": "/api/flytying/product/mission",
            "recovery": "/api/flytying/product/recovery",
            "history": "/api/flytying/product/history",
        },
    }
