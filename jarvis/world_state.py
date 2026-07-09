"""Unified always-updated snapshot of Jarvis / ARIA environment."""

from __future__ import annotations

import os
import threading
import time
from datetime import datetime
from typing import Any

_lock = threading.Lock()
_cache: dict[str, Any] | None = None
_cache_at: float = 0.0
TTL_SEC = float(os.getenv("JARVIS_WORLD_STATE_TTL", "30"))


def jarvis_preset_enabled() -> bool:
    return os.getenv("JARVIS_PRESET", "").strip().lower() == "jarvis"


def world_state_enabled() -> bool:
    if jarvis_preset_enabled():
        return True
    return os.getenv("JARVIS_WORLD_STATE", "1") != "0"


def jarvis_persona_enabled() -> bool:
    if jarvis_preset_enabled():
        return True
    return os.getenv("JARVIS_PERSONA", "").strip().lower() == "jarvis"


def _active_project() -> dict[str, Any]:
    from jarvis.active_project import get_active_project, get_active_slug

    slug = get_active_slug()
    meta = get_active_project() or {}
    return {
        "slug": slug,
        "name": meta.get("name") or slug or "",
        "title": meta.get("title") or meta.get("name") or slug or "",
    }


def _editor_snapshot() -> dict[str, Any]:
    try:
        from jarvis.editor_context import get_context

        ctx = get_context(max_age_s=300)
        if not ctx:
            return {"active": False}
        return {
            "active": True,
            "workspace": ctx.workspace,
            "file": ctx.relative_file or ctx.active_file,
            "language": ctx.language,
            "fresh": ctx.is_fresh(),
        }
    except Exception:
        return {"active": False}


def _ha_snapshot() -> dict[str, Any]:
    try:
        from jarvis.home_assistant import leave_scene, status_payload

        st = status_payload()
        leave = leave_scene()
        return {
            "enabled": bool(st.get("enabled")),
            "connected": bool(st.get("connected")),
            "configured": bool(st.get("configured")),
            "leave_scene": leave,
            "leave_scene_armed": bool(leave and st.get("connected")),
            "url": st.get("url") or "",
        }
    except Exception:
        return {"enabled": False, "connected": False, "leave_scene_armed": False}


def _scene_mode() -> str:
    try:
        from jarvis.config import _load_chat_settings

        state = _load_chat_settings().get("scene_state") or {}
        return (state.get("active_preset") or "").strip()
    except Exception:
        return ""


def _jobs_snapshot() -> dict[str, Any]:
    media: dict[str, Any] = {"busy": False, "pending": 0, "label": ""}
    coding: dict[str, Any] = {"busy": False, "pending": 0}
    print_jobs: list[dict[str, Any]] = []
    research_pending = False

    try:
        from jarvis.media_jobs import busy_state

        media = busy_state()
    except Exception:
        pass
    try:
        from jarvis.coding_jobs import job_stats

        coding = job_stats()
    except Exception:
        pass
    try:
        from jarvis.engineering.print_jobs import list_jobs

        print_jobs = [
            j for j in list_jobs(limit=8)
            if (j.get("status") or "") in ("queued", "running", "printing")
        ]
    except Exception:
        pass
    try:
        from jarvis.knowledge_research_daily import _load_state, research_enabled
        from jarvis.modules.journal import _today

        if research_enabled():
            day = _today()
            st = _load_state()
            research_pending = not bool(st.get("days", {}).get(day, {}).get("completed"))
    except Exception:
        pass

    running = (
        int(bool(media.get("busy") or media.get("pending")))
        + int(bool(coding.get("busy") or coding.get("pending")))
        + len(print_jobs)
        + int(research_pending)
    )
    return {
        "media": media,
        "coding": coding,
        "print_jobs": print_jobs,
        "research_pending": research_pending,
        "running_count": running,
    }


def _planner_next_event() -> dict[str, Any] | None:
    try:
        from jarvis.feature_flags import planner_enabled

        if not planner_enabled():
            return None
        from jarvis.planner_store import events_for_day

        now = datetime.now()
        day = now.date().isoformat()
        upcoming: list[tuple[datetime, dict[str, Any]]] = []
        for ev in events_for_day(day):
            raw = (ev.get("start_time") or "").strip()
            if not raw:
                continue
            try:
                start = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                if start.tzinfo:
                    start = start.replace(tzinfo=None)
            except ValueError:
                continue
            if start >= now:
                upcoming.append((start, ev))
        if not upcoming:
            return None
        upcoming.sort(key=lambda x: x[0])
        start, ev = upcoming[0]
        return {
            "title": ev.get("title") or "",
            "start_time": start.isoformat(timespec="minutes"),
            "minutes_until": max(0, int((start - now).total_seconds() // 60)),
            "source": ev.get("source") or "planner",
        }
    except Exception:
        return None


def _recent_failures(memory_store=None, *, limit: int = 3) -> list[dict[str, str]]:
    store = memory_store
    if store is None:
        try:
            from jarvis.assistant_instance import get_assistant

            store = get_assistant().memory
        except Exception:
            return []
    if store is None:
        return []
    try:
        from jarvis.experience_memory import EXPERIENCE_NAMESPACE

        rows = store.list_entries(
            entry_type="failure",
            namespace=EXPERIENCE_NAMESPACE,
        )
        rows.sort(key=lambda e: e.get("timestamp") or "", reverse=True)
        out: list[dict[str, str]] = []
        for row in rows[:limit]:
            out.append({
                "id": row.get("id") or "",
                "content": (row.get("content") or "")[:220],
                "timestamp": row.get("timestamp") or "",
            })
        return out
    except Exception:
        return []


def _services_summary() -> dict[str, Any]:
    try:
        from jarvis.workstation.registry import registry_snapshot

        snap = registry_snapshot()
        return {
            "ready": bool(snap.get("ready")),
            "ollama": any(
                c.get("running")
                for c in snap.get("components") or []
                if c.get("id") == "ollama"
            ),
            "comfyui": any(
                c.get("running")
                for c in snap.get("components") or []
                if c.get("id") == "comfyui"
            ),
            "required_down": snap.get("required_down") or [],
            "optional_down": snap.get("optional_down") or [],
            "running": (snap.get("summary") or {}).get("running"),
            "total": (snap.get("summary") or {}).get("total"),
        }
    except Exception:
        try:
            from jarvis.services import get_status

            st = get_status()
            svcs = st.get("services") or []
            down = [s.get("name") for s in svcs if s.get("required") and not s.get("running")]
            optional_down = [s.get("name") for s in svcs if not s.get("required") and not s.get("running")]
            return {
                "ready": bool(st.get("ready")),
                "ollama": bool(st.get("ollama", {}).get("running")),
                "comfyui": bool(st.get("comfyui", {}).get("running")),
                "required_down": down,
                "optional_down": optional_down[:4],
            }
        except Exception:
            return {"ready": False, "required_down": []}


def _knowledge_summary() -> dict[str, Any]:
    try:
        from jarvis.knowledge.registry import registry_snapshot

        snap = registry_snapshot()
        return {
            "sources": snap.get("source_count", 0),
            "searchable": snap.get("retrieval_count", 0),
            "stale": snap.get("stale_count", 0),
            "healthy": snap.get("healthy_count", 0),
        }
    except Exception:
        return {"sources": 0, "searchable": 0}


def build_world_state(*, memory_store=None) -> dict[str, Any]:
    """Build a fresh world-state snapshot (no cache)."""
    project = _active_project()
    editor = _editor_snapshot()
    ha = _ha_snapshot()
    jobs = _jobs_snapshot()
    mode = _scene_mode()
    return {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "project": project,
        "editor": editor,
        "home_assistant": ha,
        "scene_mode": mode,
        "jobs": jobs,
        "planner_next": _planner_next_event(),
        "recent_failures": _recent_failures(memory_store),
        "services": _services_summary(),
        "knowledge": _knowledge_summary(),
    }


def refresh_world_state_cache(*, force: bool = False, memory_store=None) -> dict[str, Any]:
    """Return cached snapshot, rebuilding when TTL expired."""
    global _cache, _cache_at
    now = time.time()
    with _lock:
        if not force and _cache is not None and (now - _cache_at) < TTL_SEC:
            return dict(_cache)
    state = build_world_state(memory_store=memory_store)
    with _lock:
        _cache = state
        _cache_at = now
    return dict(state)


def world_state_summary(state: dict[str, Any] | None = None) -> str:
    """Compact markdown block for system prompts."""
    if not world_state_enabled():
        return ""
    snap = state or refresh_world_state_cache()
    lines = ["**World state**"]

    proj = snap.get("project") or {}
    slug = proj.get("slug") or "default"
    name = proj.get("name") or slug
    lines.append(f"- Project: **{name}** (`{slug or 'none'}`)")

    editor = snap.get("editor") or {}
    if editor.get("active") and editor.get("file"):
        lines.append(f"- Editor: `{editor.get('file')}`")

    ha = snap.get("home_assistant") or {}
    if ha.get("enabled"):
        ha_line = "connected" if ha.get("connected") else "offline"
        if ha.get("leave_scene_armed"):
            ha_line += f" · leave `{ha.get('leave_scene')}` armed"
        lines.append(f"- Home: {ha_line}")

    mode = (snap.get("scene_mode") or "").strip()
    if mode:
        lines.append(f"- Mode: **{mode}**")

    jobs = snap.get("jobs") or {}
    rc = int(jobs.get("running_count") or 0)
    if rc:
        parts = []
        media = jobs.get("media") or {}
        if media.get("busy") or media.get("pending"):
            parts.append("media")
        coding = jobs.get("coding") or {}
        if coding.get("busy") or coding.get("pending"):
            parts.append("coding")
        if jobs.get("print_jobs"):
            parts.append(f"print×{len(jobs.get('print_jobs') or [])}")
        if jobs.get("research_pending"):
            parts.append("research")
        lines.append(f"- Jobs: {rc} active ({', '.join(parts) or 'background'})")

    nxt = snap.get("planner_next")
    if nxt and nxt.get("title"):
        mins = nxt.get("minutes_until")
        when = f" in {mins}m" if mins is not None else ""
        lines.append(f"- Next: **{nxt.get('title')}**{when}")

    failures = snap.get("recent_failures") or []
    if failures:
        lines.append("- Recent failures:")
        for f in failures[:3]:
            content = (f.get("content") or "").replace("\n", " ")[:120]
            lines.append(f"  - {content}")

    svc = snap.get("services") or {}
    if svc.get("required_down"):
        lines.append(f"- Services down: {', '.join(svc['required_down'])}")
    elif not svc.get("ready"):
        lines.append("- Services: warming up")

    return "\n".join(lines)
