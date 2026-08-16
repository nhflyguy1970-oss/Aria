"""Pipeline DAG storage — CRUD under automation_product/workflow_dags/."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

from jarvis.automation.paths import EXPORT_DIR, WORKFLOW_DAGS_DIR, ensure_dirs
from jarvis.automation.pipelines.templates import TEMPLATES, get_template, list_template_meta

FAVORITES_FILE = "favorites.json"
STATS_FILE = "usage_stats.json"

# Test/cert pipeline names that must never surface in the owner Automation loft.
_PIPELINE_FIXTURE_NAMES = frozenset(
    {
        "retry",
        "retry path",
        "retry demo",
        "engine dag",
        "dry docs",
        "dry docs unique",
        "eve unique canvas",
        "fav eve",
    }
)


def _is_pipeline_fixture(data: dict[str, Any], *, path_stem: str = "") -> bool:
    name = str(data.get("name") or path_stem or "").strip().lower()
    if name in _PIPELINE_FIXTURE_NAMES:
        return True
    blob = json.dumps(data).lower()
    if "builtin:fail" in blob:
        return True
    if path_stem in {"retry01", "runhist01", "drytest01", "enginedag1"}:
        return True
    return False


def _safe_write(path: Path, payload: dict[str, Any] | list[Any]) -> None:
    ensure_dirs()
    from jarvis.live_data_guard import assert_live_write_allowed

    assert_live_write_allowed(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def _normalize_step(d: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(d.get("id") or uuid.uuid4().hex[:8]),
        "name": str(d.get("name") or d.get("id") or "step"),
        "action": str(d.get("action") or ""),
        "params": dict(d.get("params") or {}),
        "next": list(d.get("next") or []),
        "on_success": list(d.get("on_success") or []),
        "on_failure": list(d.get("on_failure") or []),
        "retries": int(d.get("retries") or 0),
        "retry_delay_sec": float(d.get("retry_delay_sec") or 0.5),
        "when": str(d.get("when") or ""),
        "timeout_sec": float(d.get("timeout_sec") or 0) or None,
    }


def _normalize_pipeline(data: dict[str, Any]) -> dict[str, Any]:
    steps = [_normalize_step(s) for s in (data.get("steps") or [])]
    entry = data.get("entry") or (steps[0]["id"] if steps else "")
    now = time.time()
    return {
        "id": str(data.get("id") or uuid.uuid4().hex[:10]),
        "name": str(data.get("name") or "Untitled pipeline"),
        "version": int(data.get("version") or 1),
        "entry": entry,
        "variables": dict(data.get("variables") or {}),
        "tags": list(data.get("tags") or []),
        "steps": steps,
        "description": str(data.get("description") or ""),
        "documentation": str(data.get("documentation") or ""),
        "template_id": data.get("template_id"),
        "created_at": float(data.get("created_at") or now),
        "updated_at": float(data.get("updated_at") or now),
        "created_by": str(data.get("created_by") or "local"),
        "favorite": bool(data.get("favorite")),
        "versions": list(data.get("versions") or []),  # prior snapshots meta
    }


def list_templates() -> list[dict[str, Any]]:
    return list_template_meta()


def pipeline_path(pipeline_id: str) -> Path:
    return WORKFLOW_DAGS_DIR / f"{pipeline_id}.json"


def list_pipelines(
    *,
    q: str = "",
    tag: str = "",
    sort: str = "name",
    favorites_only: bool = False,
) -> list[dict[str, Any]]:
    ensure_dirs()
    favs = set(_load_favorites())
    stats = _load_stats()
    out: list[dict[str, Any]] = []
    for p in sorted(WORKFLOW_DAGS_DIR.glob("*.json")):
        if p.name in (FAVORITES_FILE, STATS_FILE):
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if _is_pipeline_fixture(data, path_stem=p.stem):
            continue
        if data.get("slug") and not data.get("entry") and not data.get("steps"):
            continue  # learned schema stray
        item = {
            "id": data.get("id") or p.stem,
            "name": data.get("name") or p.stem,
            "version": data.get("version") or 1,
            "tags": data.get("tags") or [],
            "description": data.get("description") or "",
            "template_id": data.get("template_id"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "created_by": data.get("created_by") or "local",
            "step_count": len(data.get("steps") or []),
            "favorite": (data.get("id") or p.stem) in favs or bool(data.get("favorite")),
            "usage_count": int((stats.get(data.get("id") or p.stem) or {}).get("runs") or 0),
            "last_run_at": (stats.get(data.get("id") or p.stem) or {}).get("last_run_at"),
            "path": str(p),
        }
        out.append(item)

    ql = (q or "").strip().lower()
    if ql:
        out = [
            x
            for x in out
            if ql in (x.get("name") or "").lower()
            or ql in (x.get("description") or "").lower()
            or ql in " ".join(x.get("tags") or []).lower()
            or ql in (x.get("id") or "").lower()
        ]
    if tag:
        tl = tag.lower()
        out = [x for x in out if tl in [t.lower() for t in (x.get("tags") or [])]]
    if favorites_only:
        out = [x for x in out if x.get("favorite")]

    reverse = sort.startswith("-")
    key = sort.lstrip("-") or "name"
    if key == "recent":
        out.sort(key=lambda x: float(x.get("last_run_at") or x.get("updated_at") or 0), reverse=True)
    elif key == "updated":
        out.sort(key=lambda x: float(x.get("updated_at") or 0), reverse=not reverse or True)
        if not reverse:
            out.sort(key=lambda x: float(x.get("updated_at") or 0), reverse=True)
    elif key == "usage":
        out.sort(key=lambda x: int(x.get("usage_count") or 0), reverse=True)
    else:
        out.sort(key=lambda x: (x.get("name") or "").lower(), reverse=reverse)
    return out


def get_pipeline(pipeline_id: str) -> dict[str, Any] | None:
    path = pipeline_path(pipeline_id)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return _normalize_pipeline(data)
    except Exception:
        return None


def save_pipeline(data: dict[str, Any], *, bump_version: bool = True) -> dict[str, Any]:
    ensure_dirs()
    existing = get_pipeline(str(data.get("id") or "")) if data.get("id") else None
    wf = _normalize_pipeline(data)
    now = time.time()
    if existing:
        wf["created_at"] = existing.get("created_at") or now
        if bump_version and _steps_changed(existing, wf):
            # Keep light version history (meta only)
            hist = list(existing.get("versions") or [])
            hist.append(
                {
                    "version": existing.get("version") or 1,
                    "saved_at": existing.get("updated_at") or now,
                    "name": existing.get("name"),
                    "step_count": len(existing.get("steps") or []),
                }
            )
            wf["versions"] = hist[-20:]
            wf["version"] = int(existing.get("version") or 1) + 1
        else:
            wf["version"] = int(existing.get("version") or 1)
            wf["versions"] = list(existing.get("versions") or [])
    wf["updated_at"] = now
    path = pipeline_path(wf["id"])
    _safe_write(path, wf)
    return wf


def _steps_changed(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return json.dumps(a.get("steps") or [], sort_keys=True) != json.dumps(b.get("steps") or [], sort_keys=True) or (
        a.get("entry") != b.get("entry")
    ) or (a.get("variables") != b.get("variables"))


def create_from_template(template_id: str, *, name: str | None = None, created_by: str = "local") -> dict[str, Any]:
    tpl = get_template(template_id)
    if not tpl:
        raise KeyError(template_id)
    # Prevent spam: reuse existing pipeline with same template+name if present
    desired_name = name or str(tpl.get("name") or template_id)
    for existing in list_pipelines():
        full = get_pipeline(existing["id"])
        if full and full.get("template_id") == template_id and full.get("name") == desired_name:
            return {**full, "reused": True}
    wid = uuid.uuid4().hex[:10]
    wf = _normalize_pipeline(
        {
            "id": wid,
            "name": desired_name,
            "entry": tpl.get("entry"),
            "steps": tpl.get("steps") or [],
            "tags": tpl.get("tags") or [],
            "description": tpl.get("description") or "",
            "documentation": tpl.get("documentation") or "",
            "template_id": template_id,
            "created_by": created_by,
            "variables": {},
        }
    )
    return save_pipeline(wf, bump_version=False)


def rename_pipeline(pipeline_id: str, name: str) -> dict[str, Any]:
    wf = get_pipeline(pipeline_id)
    if not wf:
        raise KeyError(pipeline_id)
    wf["name"] = (name or "").strip() or wf["name"]
    return save_pipeline(wf, bump_version=False)


def delete_pipeline(pipeline_id: str) -> dict[str, Any]:
    path = pipeline_path(pipeline_id)
    if not path.is_file():
        return {"ok": False, "error": "not_found"}
    path.unlink()
    favs = _load_favorites()
    if pipeline_id in favs:
        favs = [f for f in favs if f != pipeline_id]
        _save_favorites(favs)
    return {"ok": True, "deleted": pipeline_id}


def bulk_delete(ids: list[str]) -> dict[str, Any]:
    deleted = []
    for i in ids:
        r = delete_pipeline(str(i))
        if r.get("ok"):
            deleted.append(i)
    return {"ok": True, "deleted": deleted, "count": len(deleted)}


def duplicate_pipeline(pipeline_id: str, *, name: str | None = None) -> dict[str, Any]:
    wf = get_pipeline(pipeline_id)
    if not wf:
        raise KeyError(pipeline_id)
    new_id = uuid.uuid4().hex[:10]
    wf["id"] = new_id
    wf["name"] = name or f"{wf['name']} (copy)"
    wf["created_at"] = time.time()
    wf["updated_at"] = time.time()
    wf["version"] = 1
    wf["versions"] = []
    wf.pop("reused", None)
    return save_pipeline(wf, bump_version=False)


def export_pipelines(ids: list[str] | None = None) -> dict[str, Any]:
    ensure_dirs()
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    items = []
    for p in list_pipelines():
        if ids and p["id"] not in ids:
            continue
        full = get_pipeline(p["id"])
        if full:
            items.append(full)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"pipelines_export_{stamp}.json"
    payload = {"ok": True, "exported_at": time.time(), "count": len(items), "pipelines": items}
    _safe_write(path, payload)
    return {**payload, "path": str(path)}


def search_pipelines(q: str, *, limit: int = 40) -> list[dict[str, Any]]:
    return list_pipelines(q=q)[:limit]


def set_favorite(pipeline_id: str, favorite: bool = True) -> dict[str, Any]:
    favs = _load_favorites()
    if favorite and pipeline_id not in favs:
        favs.append(pipeline_id)
    if not favorite:
        favs = [f for f in favs if f != pipeline_id]
    _save_favorites(favs)
    return {"ok": True, "favorites": favs}


def record_usage(pipeline_id: str) -> None:
    stats = _load_stats()
    entry = stats.get(pipeline_id) or {"runs": 0}
    entry["runs"] = int(entry.get("runs") or 0) + 1
    entry["last_run_at"] = time.time()
    stats[pipeline_id] = entry
    _save_stats(stats)


def recent_pipelines(limit: int = 8) -> list[dict[str, Any]]:
    return list_pipelines(sort="recent")[:limit]


def _fav_path() -> Path:
    return WORKFLOW_DAGS_DIR / FAVORITES_FILE


def _stats_path() -> Path:
    return WORKFLOW_DAGS_DIR / STATS_FILE


def _load_favorites() -> list[str]:
    p = _fav_path()
    if not p.is_file():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return list(data.get("ids") or data if isinstance(data, list) else [])
    except Exception:
        return []


def _save_favorites(ids: list[str]) -> None:
    _safe_write(_fav_path(), {"ids": ids})


def _load_stats() -> dict[str, Any]:
    p = _stats_path()
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_stats(stats: dict[str, Any]) -> None:
    _safe_write(_stats_path(), stats)


# Ensure TEMPLATES import used (lint)
_ = TEMPLATES
