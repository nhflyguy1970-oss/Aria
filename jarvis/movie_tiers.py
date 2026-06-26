"""Movie Jarvis tier helpers — trust health, task nudge, export, ICS, profile hints."""

from __future__ import annotations

import os
import re
import time
from datetime import datetime
from typing import Any

from jarvis.config import DATA_DIR


def trust_health() -> dict[str, Any]:
    from jarvis.trust_memory import TRUST_MEMORY_TYPES, is_test_artifact

    disk_gb = 0.0
    try:
        import shutil

        disk_gb = round(shutil.disk_usage(str(DATA_DIR)).free / (1024**3), 1)
    except OSError:
        pass

    last_scrub = ""
    scrub_file = DATA_DIR / "memory_scrub.json"
    if scrub_file.is_file():
        try:
            import json

            last_scrub = json.loads(scrub_file.read_text()).get("last_run", "")[:19]
        except Exception:
            pass

    strategy_count = failure_count = 0
    try:
        from jarvis.memory_store import MemoryStore

        store = MemoryStore()
        strategy_count = len(store.list_entries(entry_type="strategy"))
        failure_count = len(store.list_entries(entry_type="failure"))
    except Exception:
        pass

    return {
        "disk_free_gb": disk_gb,
        "last_scrub": last_scrub or "never",
        "test_filter": "active",
        "test_sample_blocked": is_test_artifact("pytest journal scratch buy milk"),
        "strategy_entries": strategy_count,
        "failure_entries": failure_count,
        "trust_types": list(TRUST_MEMORY_TYPES),
    }


def profile_banner(profile: str | None = None) -> dict[str, Any]:
    from jarvis.environment import active_profile_name

    name = (profile or active_profile_name() or "default").lower()
    offline = name in ("offline", "gaming")
    web_off = offline or os.getenv("JARVIS_WEB_SEARCH", "1") == "0"
    return {
        "profile": name,
        "show": offline or web_off,
        "message": f"Profile **{name}** — web search {'off' if web_off else 'on'}",
        "web_search_off": web_off,
    }


def task_nudge_check(*, hour: int | None = None, threshold: int | None = None) -> dict[str, Any]:
    """Return whether to nudge user about open journal tasks."""
    if os.getenv("JARVIS_TASK_NUDGE", "1") != "1":
        return {"nudge": False, "reason": "disabled"}

    now = datetime.now()
    h = hour if hour is not None else now.hour
    if h < int(os.getenv("JARVIS_TASK_NUDGE_HOUR", "10")):
        return {"nudge": False, "reason": "before_nudge_hour"}

    state_file = DATA_DIR / "task_nudge_state.json"
    today = now.date().isoformat()
    if state_file.is_file():
        try:
            import json

            st = json.loads(state_file.read_text())
            if st.get("date") == today:
                return {"nudge": False, "reason": "already_nudged_today"}
        except Exception:
            pass

    open_tasks = 0
    try:
        from jarvis.modules.journal import JournalModule

        daily = JournalModule().daily_get(now.date().isoformat())
        bullets = daily.get("bullets") or []
        open_tasks = sum(1 for b in bullets if b.get("type") == "task" and not b.get("done"))
    except Exception:
        pass

    limit = threshold or int(os.getenv("JARVIS_TASK_NUDGE_THRESHOLD", "3"))
    if open_tasks < limit:
        return {"nudge": False, "open_tasks": open_tasks, "threshold": limit}

    return {
        "nudge": True,
        "open_tasks": open_tasks,
        "threshold": limit,
        "message": f"You have **{open_tasks}** open tasks in today's journal.",
    }


def mark_task_nudge_shown() -> None:
    import json

    state_file = DATA_DIR / "task_nudge_state.json"
    state_file.write_text(
        json.dumps({"date": datetime.now().date().isoformat(), "ts": time.time()}),
        encoding="utf-8",
    )


def validate_ics_url(url: str) -> dict[str, Any]:
    u = (url or "").strip()
    if not u:
        return {"ok": False, "message": "URL required"}
    if not u.startswith("http"):
        return {"ok": False, "message": "URL must start with http(s)"}
    try:
        import urllib.request
        from datetime import date

        from jarvis.calendar_ics import _parse_ics_events

        req = urllib.request.Request(u, headers={"User-Agent": "Jarvis/3.2 Calendar"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
        if "BEGIN:VCALENDAR" not in body:
            return {"ok": False, "message": "Response is not a valid ICS calendar"}
        events = _parse_ics_events(body, date.today())
        return {
            "ok": True,
            "message": f"ICS feed valid — {len(events)} event(s) today",
            "events_today": len(events),
            "preview": [e.get("summary") for e in events[:3]],
        }
    except Exception as exc:
        return {"ok": False, "message": str(exc)[:200]}


def save_ics_url(url: str) -> dict[str, Any]:
    from jarvis.env_loader import load_jarvis_env, upsert_env_vars

    u = (url or "").strip()
    check = validate_ics_url(u) if u else {"ok": True, "message": "cleared"}
    if u and not check.get("ok"):
        return check
    load_jarvis_env()
    upsert_env_vars({"JARVIS_ICS_URL": u})
    return {"ok": True, "message": "Calendar URL saved" if u else "Calendar URL cleared", **check}


def export_chat_with_memory(
    messages: list[dict],
    *,
    branch_name: str,
    memory_hits: list[dict] | None = None,
) -> str:
    lines = [f"# Jarvis Chat — {branch_name}\n"]
    if memory_hits:
        lines.append("## Memories referenced\n")
        for h in memory_hits[:12]:
            lines.append(f"- **{h.get('type', 'fact')}** ({(h.get('date') or '')[:10]}): {h.get('content', '')[:200]}")
        lines.append("")
    for m in messages:
        role = m.get("role", "?")
        if role == "system":
            continue
        content = m.get("content", "")
        lines.append(f"## {role.capitalize()}\n\n{content}\n")
    return "\n".join(lines)


def memory_citations_from_context(context_block: str) -> list[dict[str, str]]:
    """Parse injected memory lines into citation objects."""
    cites: list[dict[str, str]] = []
    for line in (context_block or "").splitlines():
        line = line.strip()
        if not line.startswith("- "):
            continue
        m = re.match(r"-\s*\*\*(\w+)\*\*\s*(?:\(([^)]+)\))?\s*:\s*(.+)", line)
        if m:
            cites.append({"type": m.group(1), "date": m.group(2) or "", "content": m.group(3).strip()})
    return cites[:8]


def service_restart(name: str) -> dict[str, Any]:
    svc = (name or "").strip().lower()
    if svc == "jarvis":
        from jarvis.server_restart import request_restart

        return request_restart()
    if svc == "ollama":
        from jarvis.services import ensure_ollama

        ok = ensure_ollama(timeout=45)
        return {"ok": ok, "service": svc, "message": "Ollama restarted" if ok else "Ollama failed to start"}
    if svc == "comfyui":
        from jarvis.services import ensure_comfyui_nvidia

        ok = ensure_comfyui_nvidia(block=True, timeout=120)
        return {"ok": ok, "service": svc, "message": "ComfyUI restarted" if ok else "ComfyUI failed — check logs"}
    if svc in ("homeassistant", "ha"):
        from jarvis.ha_docker import ensure_homeassistant

        ok = ensure_homeassistant(block=True, timeout=90)
        return {"ok": ok, "service": "homeassistant", "message": "Home Assistant restarted" if ok else "HA failed"}
    return {"ok": False, "message": f"Unknown service: {name}"}


def last_good_media_settings() -> dict[str, Any]:
    from jarvis.resource_router import suggested_for_action

    return {
        "image": suggested_for_action("generate_image"),
        "video": suggested_for_action("generate_video"),
        "meme": suggested_for_action("generate_meme"),
    }
