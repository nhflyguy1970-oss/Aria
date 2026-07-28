"""Gallery library — paginated, filtered, searchable stills inventory."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.gallery_product.inventory import IMAGE_EXTS, classify_name, is_intentional_still
from jarvis.gallery_product.visibility import apply_visibility

GENERATED = DATA_DIR / "generated"


def library_root(*, project: str = "") -> Path:
    """Global generated/ or optional per-project images dir."""
    if project:
        from jarvis.project_registry import project_dir

        p = project_dir(project) / "images"
        p.mkdir(parents=True, exist_ok=True)
        return p
    try:
        from jarvis.active_project import get_active_slug

        slug = get_active_slug() or ""
        # Only use project dir when explicitly scoped via project= param;
        # active project alone does not hide global library.
        _ = slug
    except Exception:
        pass
    GENERATED.mkdir(parents=True, exist_ok=True)
    return GENERATED


def _file_info(path: Path) -> dict[str, Any]:
    st = path.stat()
    kind = classify_name(path.name)
    w = h = None
    try:
        from PIL import Image

        with Image.open(path) as im:
            w, h = im.size
    except Exception:
        pass
    return {
        "name": path.name,
        "path": str(path),
        "mtime": st.st_mtime,
        "size": st.st_size,
        "kind": kind,
        "width": w,
        "height": h,
        "created_at": st.st_mtime,
    }


def scan_files(
    *,
    project: str = "",
    include_artifacts: bool = False,
    kinds: list[str] | None = None,
) -> list[dict[str, Any]]:
    root = library_root(project=project)
    out: list[dict[str, Any]] = []
    try:
        files = [p for p in root.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
    except Exception:
        files = []
    for p in files:
        kind = classify_name(p.name)
        if kinds:
            if kind not in kinds:
                continue
        elif not include_artifacts and not is_intentional_still(p.name):
            continue
        out.append(_file_info(p))
    return out


def list_images(
    *,
    offset: int = 0,
    limit: int = 48,
    query: str = "",
    sort: str = "newest",
    include_artifacts: bool = False,
    kinds: str = "",
    project: str = "",
    favorites_only: bool = False,
    collection_id: str = "",
    date_from: float | None = None,
    date_to: float | None = None,
) -> dict[str, Any]:
    from jarvis.gallery_product.collections import is_favorite, list_collections
    from jarvis.gallery_product.metadata import get_meta
    from jarvis.gallery_product.search import matches_query

    kind_list = [k.strip() for k in (kinds or "").split(",") if k.strip()] or None
    items = scan_files(project=project, include_artifacts=include_artifacts, kinds=kind_list)

    if collection_id:
        cols = list_collections().get("items") or []
        col = next((c for c in cols if c.get("id") == collection_id), None)
        allowed = set(col.get("names") or []) if col else set()
        items = [i for i in items if i["name"] in allowed]

    if favorites_only:
        items = [i for i in items if is_favorite(i["name"])]

    if date_from is not None:
        items = [i for i in items if float(i.get("mtime") or 0) >= date_from]
    if date_to is not None:
        items = [i for i in items if float(i.get("mtime") or 0) <= date_to]

    enriched = []
    for i in items:
        meta = get_meta(i["name"])
        row = {
            **i,
            "favorite": is_favorite(i["name"]),
            "prompt": meta.get("prompt") or "",
            "caption": meta.get("caption") or "",
            "tags": meta.get("tags") or [],
            "uncensored": bool(meta.get("uncensored")),
            "meta": meta,
        }
        if query and not matches_query(row, query):
            continue
        enriched.append(apply_visibility(row))

    reverse = sort != "oldest"
    if sort in ("newest", "oldest"):
        enriched.sort(key=lambda x: float(x.get("mtime") or 0), reverse=reverse)
    elif sort == "name":
        enriched.sort(key=lambda x: (x.get("name") or "").lower())
    elif sort == "size":
        enriched.sort(key=lambda x: int(x.get("size") or 0), reverse=True)

    total = len(enriched)
    offset = max(0, int(offset or 0))
    limit = max(1, min(int(limit or 48), 200))
    page = enriched[offset : offset + limit]
    return {
        "ok": True,
        "images": page,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": offset + limit < total,
        "include_artifacts": include_artifacts,
        "scanned_at": time.time(),
    }


def resolve_image(name: str, *, project: str = "") -> Path | None:
    root = library_root(project=project)
    path = (root / Path(name).name).resolve()
    if root.resolve() not in path.parents and path.parent != root.resolve():
        return None
    if not path.is_file() or path.suffix.lower() not in IMAGE_EXTS:
        return None
    return path
