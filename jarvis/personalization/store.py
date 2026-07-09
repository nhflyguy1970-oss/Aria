"""Personalization store — learned preferences, never hard-coded."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from jarvis.config import DATA_DIR

logger = logging.getLogger("jarvis.personalization")

PREFS_FILE = DATA_DIR / "personalization" / "preferences.json"
MAX_LIST = 20


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _load() -> dict[str, Any]:
    if not PREFS_FILE.is_file():
        return {"version": 1, "updated_at": "", "preferences": {}}
    try:
        return json.loads(PREFS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"version": 1, "updated_at": "", "preferences": {}}


def _save(data: dict[str, Any]) -> None:
    PREFS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = _utc_now()
    PREFS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_preferences() -> dict[str, Any]:
    return dict(_load().get("preferences") or {})


def get(key: str, default: Any = None) -> Any:
    return get_preferences().get(key, default)


def _bump_counter(prefs: dict, key: str, value: str, *, weight: float = 1.0) -> None:
    bucket = prefs.setdefault(key, {})
    if not isinstance(bucket, dict):
        bucket = {}
        prefs[key] = bucket
    entry = bucket.get(value) or {"count": 0, "last_used": ""}
    entry["count"] = float(entry.get("count") or 0) + weight
    entry["last_used"] = _utc_now()
    bucket[value] = entry
    # keep top N by count
    sorted_items = sorted(
        bucket.items(), key=lambda kv: float(kv[1].get("count") or 0), reverse=True
    )
    prefs[key] = dict(sorted_items[:MAX_LIST])


def record_model_use(role: str, model: str) -> None:
    data = _load()
    prefs = data.setdefault("preferences", {})
    _bump_counter(prefs, f"models:{role}", model)
    _save(data)


def record_tool_use(tool_id: str, *, success: bool = True) -> None:
    data = _load()
    prefs = data.setdefault("preferences", {})
    weight = 2.0 if success else 0.25
    _bump_counter(prefs, "coding_tools", tool_id, weight=weight)
    _save(data)


def record_repo_use(repo_path: str) -> None:
    data = _load()
    prefs = data.setdefault("preferences", {})
    _bump_counter(prefs, "repositories", repo_path)
    _save(data)


def record_project_use(slug: str) -> None:
    data = _load()
    prefs = data.setdefault("preferences", {})
    _bump_counter(prefs, "projects", slug)
    _save(data)


def record_workflow(workflow_id: str) -> None:
    data = _load()
    prefs = data.setdefault("preferences", {})
    _bump_counter(prefs, "workflows", workflow_id)
    _save(data)


def preferred_model(role: str, fallback: str = "") -> str:
    prefs = get_preferences()
    bucket = prefs.get(f"models:{role}") or {}
    if not bucket:
        return fallback
    best = max(bucket.items(), key=lambda kv: float(kv[1].get("count") or 0))
    return best[0] or fallback


def preferred_tool(fallback: str = "") -> str:
    prefs = get_preferences()
    bucket = prefs.get("coding_tools") or {}
    if not bucket:
        return fallback
    best = max(bucket.items(), key=lambda kv: float(kv[1].get("count") or 0))
    return best[0] or fallback


def preferred_project() -> str:
    prefs = get_preferences()
    bucket = prefs.get("projects") or {}
    if not bucket:
        return ""
    return max(bucket.items(), key=lambda kv: float(kv[1].get("count") or 0))[0]


def snapshot() -> dict[str, Any]:
    prefs = get_preferences()
    top_models = {
        k.replace("models:", ""): max(v.items(), key=lambda kv: float(kv[1].get("count") or 0))[0]
        for k, v in prefs.items()
        if k.startswith("models:") and v
    }
    return {
        "ok": True,
        "preferences": prefs,
        "top_models": top_models,
        "preferred_tool": preferred_tool(),
        "preferred_project": preferred_project(),
    }


def format_preferences_markdown(data: dict[str, Any] | None = None) -> str:
    snap = data or snapshot()
    lines = ["## Learned Preferences", ""]
    tool = snap.get("preferred_tool")
    if tool:
        lines.append(f"- **Coding tool:** `{tool}`")
    proj = snap.get("preferred_project")
    if proj:
        lines.append(f"- **Project:** `{proj}`")
    for role, model in (snap.get("top_models") or {}).items():
        lines.append(f"- **Model ({role}):** `{model}`")
    if len(lines) == 2:
        lines.append("_No preferences learned yet — use chat and tools normally._")
    return "\n".join(lines)
