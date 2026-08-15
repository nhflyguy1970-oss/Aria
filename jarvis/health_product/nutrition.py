"""Nutrition habit logging — natural language only; never a calorie counter."""

from __future__ import annotations

import json
import re
from datetime import date, timedelta
from typing import Any

from jarvis.health_product import store
from jarvis.health_product.terminology import DISCLAIMER

_BOUNDARY = (
    "Nutrition entries are habit notes from what you told Aria. "
    "This is not a calorie counter and not medical dietary advice."
)

_NUM = r"(\d+(?:\.\d+)?)"


def parse_nutrition_utterance(text: str) -> list[dict[str, Any]]:
    lower = (text or "").strip().lower()
    out: list[dict[str, Any]] = []
    if not lower:
        return out

    if m := re.search(rf"\b(?:i )?(?:drank|drink|had)\s+{_NUM}\s*(?:oz|ounces|glasses|cups|ml|liters?)\s+(?:of\s+)?water\b", lower):
        units = "oz"
        if "glass" in lower:
            units = "glasses"
        elif "cup" in lower:
            units = "cups"
        elif "ml" in lower:
            units = "ml"
        elif "liter" in lower:
            units = "liters"
        out.append({"kind": "water", "description": text.strip(), "quantity": float(m.group(1)), "units": units})
        return out

    if m := re.search(rf"\b(?:i )?(?:had|drank|drink)\s+{_NUM}\s*(?:beers?|drinks?|glasses?\s+of\s+wine|shots?)\b", lower) or re.search(
        rf"\b(?:i )?(?:had|drank)\s+(?:a|an|one|two|three|four|five|six)\s+(beers?|wines?|cocktails?)\b", lower
    ):
        qty = 1.0
        if m and m.lastindex and str(m.group(1)).replace(".", "", 1).isdigit():
            qty = float(m.group(1))
        else:
            words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "a": 1, "an": 1}
            for w, n in words.items():
                if re.search(rf"\b{w}\b", lower):
                    qty = float(n)
                    break
        out.append({"kind": "alcohol", "description": text.strip(), "quantity": qty, "units": "drinks"})
        return out

    if re.search(r"\b(?:i )?(?:skipped|missed)\s+(breakfast|lunch|dinner|snack)\b", lower):
        slot = re.search(r"\b(breakfast|lunch|dinner|snack)\b", lower)
        out.append({"kind": "note", "meal_slot": slot.group(1) if slot else "", "description": text.strip(), "tags": ["skipped"]})
        return out

    if m := re.search(
        r"\b(?:i )?(?:had|ate|eaten)\s+(.+?)(?:\s+for\s+(breakfast|lunch|dinner|snack))?(?:[.!?]|$)",
        lower,
    ):
        food = m.group(1).strip(" .")
        slot = (m.group(2) or "").strip()
        if not slot:
            if "breakfast" in lower:
                slot = "breakfast"
            elif "lunch" in lower:
                slot = "lunch"
            elif "dinner" in lower:
                slot = "dinner"
        if food and not _looks_like_med(food):
            out.append(
                {
                    "kind": "meal",
                    "meal_slot": slot or "",
                    "description": text.strip(),
                    "items": [food],
                }
            )
            return out

    if re.search(r"\b(?:breakfast|lunch|dinner)\s+was\s+(.+)$", lower):
        m = re.search(r"\b(breakfast|lunch|dinner)\s+was\s+(.+)$", lower)
        if m and not _looks_like_med(m.group(2)):
            out.append({"kind": "meal", "meal_slot": m.group(1), "description": text.strip(), "items": [m.group(2).strip(" .")]})
    return out


def _looks_like_med(text: str) -> bool:
    t = (text or "").lower()
    return bool(re.search(r"\b(mg|mcg|tablet|capsule|dose|metformin|lisinopril|atorvastatin|aspirin)\b", t))


def looks_like_food(text: str) -> bool:
    return bool(parse_nutrition_utterance(text))


def log_entries(entries: list[dict[str, Any]], *, provenance: str = "chat_nl") -> list[dict[str, Any]]:
    saved = []
    for e in entries:
        items = e.get("items")
        if isinstance(items, list):
            items = json.dumps(items)
        tags = e.get("tags")
        if isinstance(tags, list):
            tags = json.dumps(tags)
        # Explicitly refuse calorie fields
        payload = {
            "kind": e.get("kind") or "meal",
            "meal_slot": e.get("meal_slot") or "",
            "description": e.get("description") or "",
            "items": items or "",
            "quantity": e.get("quantity"),
            "units": e.get("units") or "",
            "tags": tags or "",
            "notes": e.get("notes") or "",
            "day": e.get("day"),
            "provenance": provenance,
            "confidence": "user_entered",
        }
        for banned in ("calories", "calorie", "protein_g", "carbs_g", "fat_g", "macros"):
            payload.pop(banned, None)
        saved.append(store.add_nutrition(payload))
        # Mirror light habit into check-in for continuity
        bits = {}
        if payload["kind"] == "water":
            bits["water"] = payload["description"]
        elif payload["kind"] == "alcohol":
            bits["alcohol"] = payload["description"]
        elif payload["kind"] == "meal":
            bits["meals"] = payload["description"]
        if bits:
            try:
                store.upsert_checkin(bits)
            except Exception:
                pass
    return saved


def habits(*, days: int = 14) -> dict[str, Any]:
    since = (date.today() - timedelta(days=days)).isoformat()
    rows = [r for r in store.list_table("nutrition_log", limit=500) if str(r.get("day") or "") >= since]
    meals = [r for r in rows if r.get("kind") == "meal"]
    water = [r for r in rows if r.get("kind") == "water"]
    alcohol = [r for r in rows if r.get("kind") == "alcohol"]
    lines = ["**Nutrition habits**", "", _BOUNDARY, ""]
    lines.append(f"Last {days} days: {len(meals)} meal note(s), {len(water)} water note(s), {len(alcohol)} alcohol note(s).")
    if meals:
        lines.append("Recent meals: " + "; ".join(str(m.get("description"))[:60] for m in meals[:5]))
    if water:
        lines.append("Water notes: " + "; ".join(str(m.get("description"))[:60] for m in water[:3]))
    lines += ["", "_" + DISCLAIMER + "_"]
    return {
        "ok": True,
        "intent": "nutrition_habits",
        "days": days,
        "counts": {"meals": len(meals), "water": len(water), "alcohol": len(alcohol)},
        "entries": rows[:80],
        "boundary": _BOUNDARY,
        "message": "\n".join(lines),
        "disclaimer": DISCLAIMER,
    }
