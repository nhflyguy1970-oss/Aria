"""Gold library health metrics and duplicate analysis."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from jarvis.flytying import index as recipe_index
from jarvis.flytying.aliases import alias_map


def _normalize_name(name: str | None) -> str:
    base = re.sub(r"[^\w\s]", "", str(name or "").lower())
    return re.sub(r"\s+", " ", base).strip()


def library_health() -> dict[str, Any]:
    items = recipe_index.recipes()
    alias_count = len(alias_map())
    if not items:
        return {
            "ok": False,
            "total": 0,
            "message": "no recipes loaded",
            "alias_count": alias_count,
            "duplicate_name_groups": 0,
        }
    with_images = 0
    with_videos = 0
    with_hook = 0
    qualities: list[float] = []
    type_counts: Counter[str] = Counter()
    name_groups: Counter[str] = Counter()
    for item in items:
        name = str(item.get("fly_name") or item.get("name") or item.get("instruction") or "")
        norm = _normalize_name(name)
        if norm:
            name_groups[norm] += 1
        if item.get("image_urls") or item.get("saved_image_paths") or item.get("hero_image"):
            with_images += 1
        if item.get("source_url"):
            with_videos += 1
        if item.get("hook"):
            with_hook += 1
        qualities.append(float(item.get("quality_score") or 0))
        type_counts[str(item.get("type") or "unknown")] += 1
    total = len(items)
    dup_groups = sum(1 for c in name_groups.values() if c > 1)
    return {
        "ok": True,
        "total": total,
        "with_images": with_images,
        "with_videos": with_videos,
        "with_hook": with_hook,
        "image_pct": round(100 * with_images / max(1, total), 1),
        "video_pct": round(100 * with_videos / max(1, total), 1),
        "avg_quality": round(sum(qualities) / max(1, len(qualities)), 1),
        "types": dict(type_counts),
        "alias_count": alias_count,
        "duplicate_name_groups": dup_groups,
    }
