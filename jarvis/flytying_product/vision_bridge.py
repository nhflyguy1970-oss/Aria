"""Vision bridge — identify materials / finished flies via shared Vision engine (never duplicate)."""

from __future__ import annotations

from typing import Any


_MATERIAL_PROMPT = (
    "Identify this fly-tying material for a tying bench inventory. "
    "Name the material type (hook, feather, dubbing, thread, bead, wire, foam, etc.), "
    "color, approximate size if visible, and brand if readable. "
    "Return a concise structured description suitable for inventory."
)

_FINISHED_FLY_PROMPT = (
    "Identify this finished fly pattern. Name the likely pattern, fly type "
    "(dry, nymph, streamer, etc.), hook size if visible, and key materials. "
    "Suggest closest classic patterns if uncertain."
)


def identify_material(
    path: str,
    *,
    assistant=None,
    question: str = "",
    source: str = "flytying_vision",
    force: bool = True,
) -> dict[str, Any]:
    from jarvis.config import is_uncensored
    from jarvis.flytying_product.history import add_entry
    from jarvis.flytying_product.status_bus import set_flytying_state
    from jarvis.vision_product.engine import analyze

    set_flytying_state("scanning", detail="identify_material", task="vision_material")
    try:
        result = analyze(
            path=path,
            action="describe",
            question=(question or _MATERIAL_PROMPT).strip(),
            source=source,
            assistant=assistant,
            force=force,
        )
        analysis = str(result.get("analysis") or result.get("message") or result.get("answer") or "")
        entry = add_entry(
            {
                "kind": "vision_scan",
                "summary": "Material identification",
                "detail": analysis[:4000],
                "path": str(path or ""),
                "confidence": result.get("confidence"),
                "source": source,
                "uncensored_origin": bool(is_uncensored()),
                "meta": {"task": "identify_material", "history_id": result.get("history_id")},
            }
        )
        draft = _inventory_draft_from_analysis(analysis, path=path)
        return {
            "ok": bool(result.get("ok", True)),
            "task": "identify_material",
            "vision": result,
            "analysis": analysis,
            "inventory_draft": draft,
            "draft_inventory": draft,
            "requires_confirmation": True,
            "history_id": entry.get("id"),
            "bridge": "vision_product",
            "message": "Confirm before adding to Fly Tying inventory — Vision never auto-writes inventory.",
        }
    finally:
        set_flytying_state("idle", detail="scan_done")


def identify_finished_fly(
    path: str,
    *,
    assistant=None,
    question: str = "",
    source: str = "flytying_vision",
    force: bool = True,
    suggest_limit: int = 6,
    limit: int | None = None,
) -> dict[str, Any]:
    from jarvis.config import is_uncensored
    from jarvis.flytying_product.history import add_entry
    from jarvis.flytying_product.status_bus import set_flytying_state
    from jarvis.vision_product.engine import analyze

    n = int(limit if limit is not None else suggest_limit)
    set_flytying_state("scanning", detail="identify_finished_fly", task="vision_fly")
    try:
        result = analyze(
            path=path,
            action="describe",
            question=(question or _FINISHED_FLY_PROMPT).strip(),
            source=source,
            assistant=assistant,
            force=force,
        )
        analysis = str(result.get("analysis") or result.get("message") or result.get("answer") or "")
        matches: list[dict[str, Any]] = []
        try:
            from jarvis.flytying.search import unified_search

            q = analysis.split(".")[0].strip()[:80]
            if q:
                payload = unified_search(q, limit=max(1, min(n, 12)))
                matches = list(payload.get("results") or payload.get("recipes") or [])[:n]
        except Exception:
            matches = []
        entry = add_entry(
            {
                "kind": "vision_scan",
                "summary": "Finished fly identification",
                "detail": analysis[:4000],
                "path": str(path or ""),
                "matches": [
                    {"id": m.get("id") or m.get("recipe_id"), "name": m.get("name") or m.get("fly_name")}
                    for m in matches
                    if isinstance(m, dict)
                ],
                "confidence": result.get("confidence"),
                "source": source,
                "uncensored_origin": bool(is_uncensored()),
                "meta": {"task": "identify_finished_fly", "history_id": result.get("history_id")},
            }
        )
        return {
            "ok": bool(result.get("ok", True)),
            "task": "identify_finished_fly",
            "vision": result,
            "analysis": analysis,
            "matches": matches,
            "library_matches": matches,
            "history_id": entry.get("id"),
            "bridge": "vision_product",
        }
    finally:
        set_flytying_state("idle", detail="scan_done")


def confirm_inventory_draft(draft: dict[str, Any] | None, *, confirmed: bool = False) -> dict[str, Any]:
    """Apply a Vision-proposed inventory item only after explicit confirmation."""
    if not confirmed:
        return {
            "ok": False,
            "requires_confirmation": True,
            "message": "Set confirmed=true to add Vision draft to inventory",
            "draft": draft,
        }
    draft = dict(draft or {})
    what = (draft.get("what") or draft.get("name") or "").strip()
    if not what:
        return {"ok": False, "message": "draft missing name/what"}
    from jarvis.flytying.user_store import add_structured_item

    return add_structured_item(
        what,
        color=str(draft.get("color") or "").strip(),
        size=str(draft.get("size") or "").strip(),
        brand=str(draft.get("brand") or "").strip(),
        notes=str(draft.get("notes") or "Added via Vision identification").strip(),
        source="vision",
        barcode=str(draft.get("barcode") or "").strip(),
    )


def _inventory_draft_from_analysis(analysis: str, *, path: str = "") -> dict[str, Any]:
    text = (analysis or "").strip()
    first = text.split("\n")[0].strip() if text else "Unknown material"
    what = ""
    low = text.lower()
    for kind in ("hook", "thread", "hackle", "feather", "dubbing", "bead", "wire", "foam", "tinsel", "chenille"):
        if kind in low:
            what = kind
            break
    return {
        "what": what or first[:120] or "Unknown material",
        "color": "",
        "size": "",
        "brand": "",
        "notes": text[:500],
        "source": "vision",
        "path": path,
    }
