"""Pull manager — progress tracking (Ollama pull remains source of truth)."""

from __future__ import annotations

import json
import time
from typing import Any

from jarvis.config import DATA_DIR

_STATE = DATA_DIR / "models_product" / "pull_state.json"


def get_pull_state() -> dict[str, Any]:
    try:
        if _STATE.is_file():
            return json.loads(_STATE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"active": None, "history": []}


def mark_pull_started(model: str) -> dict[str, Any]:
    state = get_pull_state()
    state["active"] = {
        "model": model,
        "started_at": time.time(),
        "status": "running",
        "progress": 0,
        "message": f"Pulling {model}",
    }
    _save(state)
    try:
        from jarvis.models_product.activity_bridge import emit_model_event

        emit_model_event("pull_started", message=f"Pulling {model}")
    except Exception:
        pass
    return state


def mark_pull_progress(model: str, *, progress: float = 0, message: str = "") -> dict[str, Any]:
    state = get_pull_state()
    active = state.get("active") or {}
    if active.get("model") == model:
        active["progress"] = progress
        if message:
            active["message"] = message
        state["active"] = active
        _save(state)
    return state


def mark_pull_finished(model: str, *, ok: bool = True, message: str = "") -> dict[str, Any]:
    state = get_pull_state()
    entry = {
        "model": model,
        "ok": ok,
        "finished_at": time.time(),
        "message": message or ("completed" if ok else "failed"),
    }
    hist = list(state.get("history") or [])
    hist.insert(0, entry)
    state["history"] = hist[:40]
    state["active"] = None
    _save(state)
    try:
        from jarvis.models_product.activity_bridge import emit_model_event

        emit_model_event("pull_completed" if ok else "pull_failed", message=entry["message"])
    except Exception:
        pass
    return state


def _save(state: dict[str, Any]) -> None:
    _STATE.parent.mkdir(parents=True, exist_ok=True)
    _STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
