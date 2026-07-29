"""Planner bridge — structured candidate payloads (does not invent full Planner APIs)."""

from __future__ import annotations

from typing import Any


def planner_candidates(
    *,
    kind: str = "tie_this_week",
    recipe_ids: list[str] | None = None,
    title: str = "",
    notes: str = "",
    month: int | None = None,
) -> dict[str, Any]:
    """
    Return preview candidates for Planner integration.
    Caller confirms before creating Planner tasks.
    """
    kind = (kind or "tie_this_week").strip().lower()
    candidates: list[dict[str, Any]] = []

    if kind in ("queue", "tie_this_week", "recurring_tying"):
        from jarvis.flytying.user_store import user_state

        queue = list((user_state().get("queue") or []))
        for item in queue[:20]:
            if not isinstance(item, dict):
                continue
            rid = str(item.get("recipe_id") or item.get("id") or "")
            name = str(item.get("name") or rid or "Pattern")
            candidates.append(
                {
                    "title": title or f"Tie: {name}",
                    "notes": notes or f"Fly Tying queue item {rid}",
                    "recipe_id": rid,
                    "kind": kind,
                    "source": "flytying_queue",
                    "selected": True,
                }
            )
        if recipe_ids:
            for rid in recipe_ids:
                candidates.append(
                    {
                        "title": title or f"Tie: {rid}",
                        "notes": notes,
                        "recipe_id": rid,
                        "kind": kind,
                        "source": "flytying_explicit",
                        "selected": True,
                    }
                )

    elif kind in ("trip_prep", "seasonal_tying"):
        from jarvis.flytying.hatch import hatch_context

        ctx = hatch_context(month=month)
        hatches = ", ".join(str(h) for h in (ctx.get("hatches") or [])[:6])
        types = ", ".join(str(t) for t in (ctx.get("suggest_types") or [])[:6])
        candidates.append(
            {
                "title": title or f"Seasonal tying — {ctx.get('region')} (month {ctx.get('month')})",
                "notes": notes or f"Hatches: {hatches}. Types: {types}. {ctx.get('notes') or ''}".strip(),
                "kind": kind,
                "region": ctx.get("region"),
                "month": ctx.get("month"),
                "suggest_types": ctx.get("suggest_types") or [],
                "source": "flytying_hatch",
                "selected": True,
            }
        )

    elif kind == "material_reminders":
        from jarvis.flytying_product.inventory import low_stock_items

        for item in low_stock_items()[:15]:
            name = item.get("name") or item.get("what") or item.get("id")
            candidates.append(
                {
                    "title": title or f"Restock: {name}",
                    "notes": notes or str(item.get("notes") or "Low stock"),
                    "kind": kind,
                    "material_id": item.get("id"),
                    "source": "flytying_low_stock",
                    "selected": True,
                }
            )
    else:
        candidates.append(
            {
                "title": title or "Fly Tying task",
                "notes": notes,
                "kind": kind,
                "recipe_ids": list(recipe_ids or []),
                "source": "flytying",
                "selected": True,
            }
        )

    return {
        "ok": True,
        "product": "Fly Tying",
        "target": "Planner",
        "requires_confirmation": True,
        "kind": kind,
        "candidates": candidates,
        "message": "Preview only — confirm in Planner to create tasks.",
        "pipeline": "flytying_planner_bridge",
    }


def queue_to_planner_preview() -> dict[str, Any]:
    return planner_candidates(kind="queue")


def seasonal_tying_plan(*, month: int | None = None) -> dict[str, Any]:
    return planner_candidates(kind="seasonal_tying", month=month)
