"""Activity Center bridge for Models events."""

from __future__ import annotations

import time
from typing import Any

_RECENT: list[dict[str, Any]] = []


def emit_model_event(event_type: str, *, message: str = "", detail: dict | None = None) -> dict[str, Any]:
    evt = {
        "id": f"models-{int(time.time() * 1000)}",
        "timestamp": time.time(),
        "category": "models",
        "type": event_type,
        "severity": _severity(event_type),
        "title": _title(event_type),
        "message": message or event_type.replace("_", " "),
        "fix": _fix(event_type),
        "product": "models",
        "detail": detail or {},
    }
    _RECENT.insert(0, evt)
    del _RECENT[100:]
    # Best-effort publish into GUI activity store via file sidecar for producers
    try:
        from jarvis.config import DATA_DIR
        import json

        path = DATA_DIR / "models_product" / "activity_outbox.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(evt) + "\n")
    except Exception:
        pass
    return evt


def drain_outbox(*, limit: int = 50) -> list[dict[str, Any]]:
    from jarvis.config import DATA_DIR
    import json

    path = DATA_DIR / "models_product" / "activity_outbox.jsonl"
    if not path.is_file():
        return list(_RECENT)[:limit]
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    events = []
    for line in lines[-limit:]:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    try:
        path.write_text("", encoding="utf-8")
    except Exception:
        pass
    return list(reversed(events))


def _severity(t: str) -> str:
    if t in ("pull_failed", "oom", "provider_offline"):
        return "error"
    if t in ("vram_warning",):
        return "warning"
    if t in ("pull_completed", "model_switched", "role_changed"):
        return "success"
    return "info"


def _title(t: str) -> str:
    return {
        "model_switched": "Model switched",
        "role_changed": "Role assignment changed",
        "pull_started": "Model pull started",
        "pull_completed": "Model pull completed",
        "pull_failed": "Model pull failed",
        "oom": "Out of memory (model)",
        "vram_warning": "VRAM warning",
        "provider_offline": "Provider offline",
    }.get(t, "Models event")


def _fix(t: str) -> str:
    if t in ("oom", "vram_warning", "provider_offline"):
        return "mc:inference"
    if t.startswith("pull"):
        return "models:catalog"
    return "models:home"
