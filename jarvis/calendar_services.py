"""Calendar intelligence — NL schedule, conflicts, meeting prep, focus, vision, HA modes."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from typing import Any

from jarvis.calendar_time import now_local, today_iso, validate_time_hm

log = logging.getLogger("jarvis.calendar.services")


def parse_natural_schedule(text: str) -> dict[str, Any]:
    """Parse light NL into a proposed commitment (confirm required)."""
    raw = (text or "").strip()
    if not raw:
        return {"ok": False, "message": "Nothing to schedule"}
    lower = raw.lower()
    when = today_iso()
    time_str = None
    title = raw

    # Relative day
    if "tomorrow" in lower:
        when = (now_local().date() + timedelta(days=1)).isoformat()
        title = re.sub(r"\btomorrow\b", "", title, flags=re.I).strip()
    elif "today" in lower:
        when = today_iso()
        title = re.sub(r"\btoday\b", "", title, flags=re.I).strip()
    else:
        # Weekday name
        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for i, name in enumerate(weekdays):
            if name in lower or name[:3] in lower.split():
                today = now_local().date()
                delta = (i - today.weekday()) % 7
                if delta == 0:
                    delta = 7
                when = (today + timedelta(days=delta)).isoformat()
                title = re.sub(rf"\b{name}\b|\b{name[:3]}\b", "", title, flags=re.I).strip()
                break
        # next month
        if "next month" in lower:
            d = now_local().date()
            nm = d.replace(day=1) + timedelta(days=32)
            when = nm.replace(day=min(d.day, 28)).isoformat()
            title = re.sub(r"\bnext month\b", "", title, flags=re.I).strip()

    # Time patterns
    m = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", lower)
    if not m:
        m = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", lower)
    if m:
        try:
            if m.lastindex and m.lastindex >= 3 and m.group(3):
                time_str = validate_time_hm(m.group(0))
            else:
                time_str = validate_time_hm(f"{m.group(1)}:{m.group(2) or '00'}")
        except ValueError:
            time_str = None
        title = re.sub(re.escape(m.group(0)), "", title, flags=re.I).strip()

    # Morning / afternoon / evening
    if not time_str:
        if "morning" in lower:
            time_str = "09:00"
            title = re.sub(r"\bmorning\b", "", title, flags=re.I).strip()
        elif "afternoon" in lower:
            time_str = "14:00"
            title = re.sub(r"\bafternoon\b", "", title, flags=re.I).strip()
        elif "evening" in lower or "night" in lower:
            time_str = "19:00"
            title = re.sub(r"\b(evening|night)\b", "", title, flags=re.I).strip()
        elif "lunch" in lower:
            time_str = "12:00"

    title = re.sub(
        r"^(schedule|add|create|book|set)\s+(a\s+|an\s+)?(meeting|event|appointment)?\s*",
        "",
        title,
        flags=re.I,
    ).strip(" -–—:")
    if not title:
        title = raw[:80]

    proposal = {
        "title": title,
        "day": when,
        "time": time_str,
        "target": "journal",
        "requires_confirmation": True,
    }
    return {"ok": True, "proposal": proposal, "message": f"Schedule “{title}” on {when}" + (f" at {time_str}" if time_str else "") + "?"}


def detect_conflicts(journal, day: str | None = None) -> dict[str, Any]:
    from jarvis.calendar_schedule import schedule_for_day

    d = (day or today_iso())[:10]
    detail = schedule_for_day(journal, d)
    timed = [i for i in detail.get("items") or [] if i.get("time") and i.get("kind") in ("event", "block")]
    conflicts = []
    for i, a in enumerate(timed):
        a0 = int(a["time"][:2]) * 60 + int(a["time"][3:5])
        a1 = a0 + int(a.get("duration_min") or 45)
        if a.get("end_hm"):
            try:
                a1 = int(a["end_hm"][:2]) * 60 + int(a["end_hm"][3:5])
            except Exception:
                pass
        for b in timed[i + 1 :]:
            b0 = int(b["time"][:2]) * 60 + int(b["time"][3:5])
            b1 = b0 + int(b.get("duration_min") or 45)
            if b.get("end_hm"):
                try:
                    b1 = int(b["end_hm"][:2]) * 60 + int(b["end_hm"][3:5])
                except Exception:
                    pass
            if a0 < b1 and b0 < a1:
                conflicts.append(
                    {
                        "a": a.get("title"),
                        "b": b.get("title"),
                        "day": d,
                        "when": a.get("time"),
                        "sources": [a.get("source"), b.get("source")],
                    }
                )
    overload = len([i for i in detail.get("items") or [] if i.get("kind") == "event"]) >= 6
    suggestions = []
    if conflicts:
        suggestions.append("Resolve overlapping commitments before adding more")
    if overload:
        suggestions.append("Day looks overloaded — protect a focus block")
    from jarvis.calendar_schedule import _free_windows

    free = _free_windows({d: detail}, d)
    if free:
        best = max(free, key=lambda w: w.get("minutes", 0))
        if best.get("minutes", 0) >= 45:
            suggestions.append(f"Focus opportunity {best['start_hm']}–{best['end_hm']} ({best['minutes']}m)")
    return {
        "ok": True,
        "day": d,
        "conflicts": conflicts,
        "overloaded": overload,
        "suggestions": suggestions,
        "free_windows": free,
        "requires_confirmation": True,
    }


def meeting_prep(journal, item_id: str | None = None, *, assistant: Any = None) -> dict[str, Any]:
    from jarvis.calendar_schedule import schedule_for_day, timeline_schedule

    day = today_iso()
    timeline = timeline_schedule(journal, day)
    target = None
    if item_id:
        for it in timeline.get("items") or []:
            if it.get("id") == item_id:
                target = it
                break
    if not target:
        target = timeline.get("next")
    if not target:
        return {"ok": False, "message": "No upcoming meeting found"}

    title = target.get("title") or ""
    evidence: list[str] = []
    docs: list[dict] = []
    memory_hits: list[str] = []
    tasks: list[str] = []

    try:
        if assistant is not None and getattr(assistant, "memory", None):
            hits = assistant.memory.search(title, limit=4) or []
            for h in hits[:3]:
                memory_hits.append((h.get("content") or "")[:160])
    except Exception as exc:
        log.debug("prep memory: %s", exc)

    try:
        from jarvis.intelligence.hybrid_rag import hybrid_search

        rag = hybrid_search(title, limit=3)
        docs = rag.get("citations") or []
        if rag.get("hits"):
            evidence.append("Documents retrieved")
    except Exception as exc:
        log.debug("prep rag: %s", exc)

    try:
        from jarvis.intelligence.knowledge_graph import search_graph

        g = search_graph(title, limit=4)
        if g.get("nodes"):
            evidence.append(f"Graph context: {len(g['nodes'])} nodes")
    except Exception as exc:
        log.debug("prep graph: %s", exc)

    try:
        from jarvis.planner_store import list_tasks

        for t in list_tasks()[:5]:
            if any(w in (t.get("text") or "").lower() for w in title.lower().split()[:3] if len(w) > 3):
                tasks.append(t.get("text"))
    except Exception:
        pass

    # Journal notes same day
    notes = []
    try:
        page = journal.daily_get(day, enrich=False)
        for b in page.get("bullets") or []:
            if b.get("type") == "note":
                notes.append(b.get("content") or "")
    except Exception:
        pass

    return {
        "ok": True,
        "meeting": target,
        "agenda": [f"Review: {title}", "Confirm outcomes", "Capture follow-ups in Journal"],
        "memory": memory_hits,
        "documents": docs[:5],
        "notes": notes[:5],
        "open_tasks": tasks[:5],
        "evidence": evidence,
        "message": f"Prep for “{title}” at {target.get('time') or 'unspecified time'}",
    }


def focus_suggestions(journal, day: str | None = None) -> dict[str, Any]:
    conflicts = detect_conflicts(journal, day)
    windows = conflicts.get("free_windows") or []
    priorities = []
    try:
        from jarvis.planner_store import list_tasks

        priorities = [t.get("text") for t in list_tasks()[:3]]
    except Exception:
        pass
    suggestions = []
    for w in windows:
        if w.get("minutes", 0) >= 45:
            suggestions.append(
                {
                    "when": f"{w['start_hm']}–{w['end_hm']}",
                    "minutes": w["minutes"],
                    "action": "Start focus session",
                    "priority": priorities[0] if priorities else "Deep work",
                    "requires_confirmation": True,
                }
            )
    return {
        "ok": True,
        "day": day or today_iso(),
        "suggestions": suggestions[:4],
        "priorities": priorities,
        "requires_confirmation": True,
    }


def memory_dates(assistant: Any | None = None) -> dict[str, Any]:
    hits = []
    try:
        if assistant is not None and getattr(assistant, "memory", None):
            for q in ("birthday", "anniversary", "annual", "every year"):
                for h in assistant.memory.search(q, limit=3) or []:
                    hits.append({"query": q, "content": (h.get("content") or "")[:200]})
    except Exception as exc:
        log.debug("memory dates: %s", exc)
    # dedupe
    seen = set()
    unique = []
    for h in hits:
        key = h["content"][:80]
        if key in seen:
            continue
        seen.add(key)
        unique.append(h)
    return {"ok": True, "reminders": unique[:10], "requires_confirmation": True}


def vision_extract_events(path: str) -> dict[str, Any]:
    """OCR / vision → candidate events via shared Vision import pipeline."""
    from jarvis.vision_product.import_pipeline import vision_import

    out = vision_import(path=path, target="calendar", source="calendar")
    if not out.get("ok"):
        return {
            "ok": False,
            "message": out.get("error") or out.get("message") or "OCR unavailable",
            "candidates": [],
        }
    candidates = []
    for c in out.get("candidates") or []:
        line = str(c.get("text") or "").strip()
        if not line:
            continue
        parsed = parse_natural_schedule(line)
        if parsed.get("ok"):
            candidates.append({**parsed["proposal"], "selected": True, "raw": line})
        else:
            candidates.append({"title": line, "day": today_iso(), "time": None, "selected": True, "raw": line})
        if len(candidates) >= 15:
            break
    return {
        "ok": True,
        "path": out.get("path") or path,
        "raw_text": out.get("raw_text") or "",
        "candidates": candidates,
        "engine": out.get("engine"),
        "confidence": out.get("confidence"),
        "pipeline": "vision_import",
        "message": f"Found {len(candidates)} candidate event(s) — review before import",
        "requires_confirmation": True,
    }


def import_vision_events(journal, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    from jarvis.calendar_schedule import create_commitment

    added = []
    errors = []
    for c in candidates or []:
        if not c.get("selected", True):
            continue
        try:
            row = create_commitment(
                journal,
                title=c.get("title") or c.get("raw") or "",
                day=c.get("day"),
                time=c.get("time"),
                target=c.get("target") or "journal",
            )
            added.append(row)
        except Exception as exc:
            errors.append(str(exc))
    return {"ok": True, "count": len(added), "added": added, "errors": errors[:10]}


def ha_calendar_mode(mode: str, *, enabled: bool | None = None) -> dict[str, Any]:
    """Optional HA scene activation for meeting/focus/travel modes."""
    from jarvis.calendar_store import get_pref, set_pref

    mode = (mode or "").lower().strip()
    if mode not in ("meeting", "focus", "travel", "off"):
        return {"ok": False, "message": "mode must be meeting|focus|travel|off"}
    prefer = get_pref("ha_calendar_modes", True) if enabled is None else bool(enabled)
    if mode == "off":
        set_pref("ha_calendar_active_mode", None)
        return {"ok": True, "mode": None, "home_assistant": None}
    if not prefer:
        return {"ok": True, "mode": mode, "home_assistant": {"skipped": True, "reason": "disabled in prefs"}}
    set_pref("ha_calendar_active_mode", mode)
    ha_result = None
    try:
        from jarvis.scene_presets import activate_preset, list_presets

        presets = list_presets() if callable(list_presets) else []
        match = None
        for p in presets or []:
            label = f"{p.get('id') or ''} {p.get('name') or ''} {p.get('label') or ''}".lower()
            if mode in label:
                match = p.get("id") or p.get("name")
                break
        if match:
            ok, msg = activate_preset(match)
            ha_result = {"ok": ok, "message": msg, "preset": match}
        else:
            ha_result = {"ok": False, "message": f"No {mode} scene preset found"}
    except Exception as exc:
        ha_result = {"ok": False, "message": str(exc)}
    return {"ok": True, "mode": mode, "home_assistant": ha_result}
