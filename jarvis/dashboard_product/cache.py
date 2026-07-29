"""Last-good Home cache for offline / degraded refresh."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

CACHE_DIR = Path(DATA_DIR) / "dashboard_product"
CACHE_FILE = CACHE_DIR / "last_good_home.json"
LAYOUT_FILE = CACHE_DIR / "layout.json"
DEFAULT_TTL_S = 900


def _ensure() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def save_last_good(payload: dict[str, Any]) -> None:
    _ensure()
    slim = {
        "saved_at": time.time(),
        "generated_at": payload.get("generated_at"),
        "greeting": payload.get("greeting"),
        "widgets": payload.get("widgets"),
        "attention": payload.get("attention"),
        "daily_brief": payload.get("daily_brief"),
        "diagnostics": {
            "healthy": (payload.get("diagnostics") or {}).get("healthy"),
            "widget_failures": (payload.get("diagnostics") or {}).get("widget_failures"),
        },
    }
    CACHE_FILE.write_text(json.dumps(slim, indent=2, default=str), encoding="utf-8")


def load_last_good(*, max_age_s: float = DEFAULT_TTL_S) -> dict[str, Any] | None:
    if not CACHE_FILE.is_file():
        return None
    try:
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        age = time.time() - float(data.get("saved_at") or 0)
        data["cache_age_s"] = round(age, 1)
        data["cache_stale"] = age > max_age_s
        data["from_cache"] = True
        return data
    except Exception:
        return None


def load_layout() -> dict[str, Any]:
    _ensure()
    defaults = {
        "order": [],
        "hidden": ["news"],  # Daily Brief preferred over separate news by default
        "density": "comfortable",
        "role": "default",
        "collapsed": [],
    }
    if not LAYOUT_FILE.is_file():
        return dict(defaults)
    try:
        data = json.loads(LAYOUT_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return dict(defaults)
        out = dict(defaults)
        out.update(data)
        return out
    except Exception:
        return dict(defaults)


def save_layout(patch: dict[str, Any] | None = None) -> dict[str, Any]:
    data = load_layout()
    if isinstance(patch, dict):
        for k, v in patch.items():
            if k in ("order", "hidden", "collapsed") and isinstance(v, list):
                data[k] = v
            elif k in ("density", "role") and isinstance(v, str):
                data[k] = v
    _ensure()
    LAYOUT_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
