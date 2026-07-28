"""Optional local similarity clustering (filename/prompt heuristics + optional embeddings)."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from jarvis.gallery_product.library import list_images
from jarvis.gallery_product.metadata import get_meta


def cluster_similar(*, limit: int = 60) -> dict[str, Any]:
    """Group by shared prompt prefix / checkpoint — local, opt-in browse aid."""
    page = list_images(offset=0, limit=limit, include_artifacts=False)
    groups: dict[str, list[str]] = defaultdict(list)
    for img in page.get("images") or []:
        if img.get("restricted"):
            continue
        meta = get_meta(img["name"])
        prompt = (meta.get("prompt") or img.get("prompt") or "")[:40].strip().lower() or "untitled"
        ck = (meta.get("checkpoint") or "default").lower()
        key = f"{ck}::{prompt}"
        groups[key].append(img["name"])
    clusters = [
        {"id": i, "label": k.split("::", 1)[-1][:60] or "Group", "names": names, "size": len(names)}
        for i, (k, names) in enumerate(groups.items())
        if len(names) >= 2
    ]
    clusters.sort(key=lambda c: c["size"], reverse=True)
    return {"ok": True, "clusters": clusters[:20], "method": "prompt_prefix_local"}
