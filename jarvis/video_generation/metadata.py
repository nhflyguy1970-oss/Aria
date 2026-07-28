"""Per-video generation metadata (method, seed, prompts) — not a second library product."""

from __future__ import annotations

import json
import time
from typing import Any

from jarvis.config import DATA_DIR

META_FILE = DATA_DIR / "video_generation" / "metadata.json"


def _load() -> dict[str, Any]:
    if not META_FILE.exists():
        return {}
    try:
        data = json.loads(META_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save(store: dict[str, Any]) -> None:
    META_FILE.parent.mkdir(parents=True, exist_ok=True)
    META_FILE.write_text(json.dumps(store, indent=2), encoding="utf-8")


def get_meta(name: str) -> dict[str, Any]:
    return dict((_load().get(name) or {}))


def set_meta(name: str, fields: dict[str, Any]) -> dict[str, Any]:
    store = _load()
    cur = dict(store.get(name) or {})
    cur.update({k: v for k, v in (fields or {}).items() if v is not None})
    store[name] = cur
    _save(store)
    return {"ok": True, "meta": cur}


def mark_generation(
    name: str,
    *,
    prompt: str = "",
    enhanced: str = "",
    negative: str = "",
    engine: str = "",
    method: str = "",
    seed: str = "",
    duration: float | None = None,
    fps: int | None = None,
    width: int | None = None,
    height: int | None = None,
    uncensored: bool = False,
    project: str = "",
    clip_plan: dict | None = None,
) -> dict[str, Any]:
    return set_meta(
        name,
        {
            "prompt": (prompt or "")[:2000],
            "enhanced_prompt": (enhanced or "")[:4000],
            "negative_prompt": (negative or "")[:2000],
            "engine": engine or "",
            "method": method or "",
            "seed": seed or "",
            "duration": duration,
            "fps": fps,
            "width": width,
            "height": height,
            "uncensored": bool(uncensored),
            "project": project or "",
            "clip_plan": clip_plan or {},
            "created_at": time.time(),
            "source": "generation",
        },
    )


def is_restricted_for_viewer(name: str, *, viewer_uncensored: bool | None = None) -> bool:
    """True when asset was made uncensored but viewer is in standard mode."""
    if viewer_uncensored is None:
        try:
            from jarvis.config import is_uncensored

            viewer_uncensored = is_uncensored()
        except Exception:
            viewer_uncensored = False
    if viewer_uncensored:
        return False
    return bool(get_meta(name).get("uncensored"))


def apply_visibility(item: dict[str, Any], *, viewer_uncensored: bool | None = None) -> dict[str, Any]:
    out = dict(item)
    name = out.get("name") or ""
    meta = get_meta(name)
    out.update({k: meta.get(k) for k in ("method", "engine", "seed", "duration", "fps", "width", "height") if meta.get(k) is not None})
    if meta.get("prompt"):
        out.setdefault("prompt", meta.get("prompt"))
    if not is_restricted_for_viewer(name, viewer_uncensored=viewer_uncensored):
        out["restricted"] = False
        return out
    out["restricted"] = True
    out["thumb_blocked"] = True
    for k in ("prompt", "enhanced_prompt", "negative_prompt", "caption"):
        if k in out:
            out[k] = None
    out["preview_message"] = "Restricted — created in uncensored mode. Reveal requires uncensored profile."
    return out
