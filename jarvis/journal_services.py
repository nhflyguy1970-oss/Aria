"""Journal intelligence — reflection, promotion, migration, memory, voice, vision.

All assistants propose only. Mutations require explicit user confirmation.
Journal remains a Bullet Journal (thoughts / notes / reflection), not a task manager.
"""

from __future__ import annotations

import logging
import re
from datetime import date, timedelta
from typing import Any

from jarvis.modules.journal import _month_key, _today, _week_key

log = logging.getLogger("jarvis.journal.services")


def _clip(text: str, n: int = 120) -> str:
    t = (text or "").strip()
    return t if len(t) <= n else t[: n - 1] + "…"


def reflect_assistant(journal, scope: str = "today") -> dict[str, Any]:
    """User-initiated reflection. Does not mutate the journal."""
    scope = (scope or "today").lower().strip()
    if scope not in ("today", "day", "daily", "week", "weekly", "month", "monthly", "habits", "gratitude", "mood"):
        scope = "today"
    try:
        if scope in ("habits",):
            tracker = journal.habit_tracker()
            habits = tracker.get("habits") or []
            lines = [
                f"- {h.get('name')}: streak {h.get('streak', 0)}, "
                f"{h.get('completion_pct', 0)}% this month, longest {h.get('longest_streak', 0)}"
                for h in habits
            ]
            text = "Habit summary\n" + ("\n".join(lines) if lines else "No habits tracked.")
            return {"ok": True, "scope": "habits", "reflection": text, "requires_confirmation": False}
        if scope in ("gratitude", "mood"):
            wellness = journal.wellness_overview(_month_key()) if hasattr(journal, "wellness_overview") else {}
            if scope == "gratitude":
                stream = (wellness.get("gratitude_stream") or [])[-10:]
                text = "Recent gratitude\n" + (
                    "\n".join(f"- {g.get('text') or g}" for g in stream) if stream else "No gratitude entries yet."
                )
            else:
                days = wellness.get("days") or []
                moods = [d for d in days if d.get("mood")]
                avg = round(sum(int(d["mood"]) for d in moods) / max(1, len(moods)), 1) if moods else None
                text = f"Mood insight — {len(moods)} logged days" + (f", average {avg}/5" if avg else "")
            return {"ok": True, "scope": scope, "reflection": text, "requires_confirmation": False}

        map_scope = {
            "today": "today",
            "day": "today",
            "daily": "today",
            "week": "week",
            "weekly": "week",
            "month": "month",
            "monthly": "month",
        }.get(scope, "today")
        reflection = journal.ai_reflect(map_scope)
        return {
            "ok": True,
            "scope": map_scope,
            "reflection": reflection,
            "requires_confirmation": False,
            "message": "Reflection generated — nothing was changed in your journal.",
        }
    except Exception as exc:
        log.exception("reflect_assistant failed")
        return {"ok": False, "error": str(exc), "reflection": ""}


def promotion_assistant(journal, *, limit: int = 12) -> dict[str, Any]:
    """Suggest Planner / Calendar / Memory / Project destinations. Confirm required."""
    open_tasks = journal.open_tasks() if hasattr(journal, "open_tasks") else []
    suggestions: list[dict[str, Any]] = []
    for t in open_tasks[:limit]:
        content = (t.get("content") or "").strip()
        if not content:
            continue
        lower = content.lower()
        dest = "planner"
        reason = "Actionable open bullet — good candidate for Planner"
        if re.search(r"\b(meet|call|appointment|interview|flight|doctor|dentist)\b", lower):
            dest = "calendar"
            reason = "Sounds like a scheduled commitment — Calendar"
        elif re.search(r"\b(remember|idea|insight|learned|note to self)\b", lower) or t.get("type") == "note":
            dest = "memory"
            reason = "Reflective content — Memory candidate"
        elif re.search(r"\b(project|build|ship|milestone)\b", lower):
            dest = "project"
            reason = "Project-shaped work — Project journal candidate"
        if t.get("planner_task_id"):
            continue
        suggestions.append(
            {
                "bullet_id": t.get("id"),
                "content": _clip(content),
                "section": t.get("section"),
                "suggest": dest,
                "reason": reason,
                "requires_confirmation": True,
            }
        )
    return {
        "ok": True,
        "suggestions": suggestions,
        "message": "Review suggestions — nothing moves until you confirm.",
        "requires_confirmation": True,
    }


def migration_assistant(journal, scope: str = "daily") -> dict[str, Any]:
    """Suggest carry-forward / schedule / cancel / archive during reviews."""
    scope = (scope or "daily").lower()
    suggestions: list[dict[str, Any]] = []
    tasks = journal.open_tasks() if hasattr(journal, "open_tasks") else []
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    next_week = _week_key(date.today() + timedelta(days=7))
    next_month = _month_key(date.today().replace(day=28) + timedelta(days=4))

    for t in tasks[:20]:
        content = (t.get("content") or "").strip()
        lower = content.lower()
        action = "carry_forward"
        target = tomorrow if scope in ("daily", "day") else (next_week if scope.startswith("week") else next_month)
        reason = "Still open — consider migrating forward"
        if re.search(r"\b(someday|maybe|later|eventually)\b", lower):
            action = "schedule"
            target = next_month
            reason = "Someday/maybe tone — Future / monthly schedule"
        elif re.search(r"\b(cancel|drop|nevermind|never mind|obsolete)\b", lower):
            action = "cancel"
            target = None
            reason = "Sounds abandoned — cancel?"
        elif re.search(r"\b(done|finished|complete)\b", lower):
            action = "archive"
            target = None
            reason = "May already be done — archive/complete?"
        suggestions.append(
            {
                "bullet_id": t.get("id"),
                "content": _clip(content),
                "section": t.get("section"),
                "action": action,
                "target": target,
                "reason": reason,
                "requires_confirmation": True,
            }
        )
    return {
        "ok": True,
        "scope": scope,
        "suggestions": suggestions,
        "message": "Migration suggestions only — confirm each change.",
        "requires_confirmation": True,
    }


def memory_surface(journal, query: str = "", *, limit: int = 8) -> dict[str, Any]:
    """Soft-surface related memories / KG entities. Review before linking."""
    q = (query or "").strip()
    related: list[dict[str, Any]] = []
    if q:
        try:
            hits = journal.search(q, limit=limit)
            for h in hits:
                related.append(
                    {
                        "kind": "journal",
                        "id": h.get("id"),
                        "label": _clip(h.get("content") or ""),
                        "section": h.get("section"),
                    }
                )
        except Exception:
            log.debug("journal search failed", exc_info=True)
    try:
        from jarvis import memory as mem

        if q and hasattr(mem, "search"):
            for m in (mem.search(q, limit=limit) or [])[:limit]:
                related.append(
                    {
                        "kind": "memory",
                        "id": m.get("id") or m.get("key"),
                        "label": _clip(str(m.get("text") or m.get("value") or m)),
                    }
                )
    except Exception:
        log.debug("memory search unavailable", exc_info=True)
    connections_error = ""
    try:
        from jarvis import knowledge_graph as kg

        if q and hasattr(kg, "search"):
            for e in (kg.search(q, limit=5) or [])[:5]:
                related.append(
                    {
                        "kind": "entity",
                        "id": e.get("id") or e.get("name"),
                        "label": _clip(str(e.get("name") or e.get("label") or e)),
                        "source": "connections",
                    }
                )
    except Exception as exc:
        connections_error = str(exc)
        log.warning("Connections search failed for journal related: %s", exc)

    out = {
        "ok": True,
        "query": q,
        "related": related,
        "requires_confirmation": True,
        "message": "Related items surfaced for review — nothing linked automatically.",
    }
    if connections_error:
        out["connections_error"] = connections_error
    return out


def writing_assistant(text: str, mode: str = "organize") -> dict[str, Any]:
    """Optional writing help. Never rewrites personal thoughts automatically."""
    raw = (text or "").strip()
    mode = (mode or "organize").lower()
    if not raw:
        return {"ok": False, "error": "Nothing to assist with", "suggestions": []}
    suggestions: list[dict[str, Any]] = []
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    if mode in ("organize", "structure"):
        tasks = [ln for ln in lines if not ln.lower().startswith(("n:", "—", "-"))]
        notes = [ln for ln in lines if ln.lower().startswith(("n:", "—", "-"))]
        if tasks or notes:
            suggestions.append(
                {
                    "kind": "organization",
                    "title": "Suggested grouping",
                    "body": "Tasks:\n"
                    + "\n".join(f"• {t}" for t in tasks[:8])
                    + ("\nNotes:\n" + "\n".join(f"— {n}" for n in notes[:8]) if notes else ""),
                }
            )
    if mode in ("title", "titles", "organize"):
        first = lines[0] if lines else raw[:40]
        title = re.sub(r"^(t:|e:|n:|•|○|—|-)\s*", "", first, flags=re.I)[:48]
        suggestions.append({"kind": "title", "title": title or "Untitled collection", "body": title})
    if mode in ("clarity", "organize"):
        long_lines = [ln for ln in lines if len(ln) > 140]
        if long_lines:
            suggestions.append(
                {
                    "kind": "clarity",
                    "title": "Long lines",
                    "body": "Consider splitting into nested bullets:\n"
                    + "\n".join(f"• {_clip(ln, 80)}" for ln in long_lines[:5]),
                }
            )
    if mode in ("collections", "crossref", "organize"):
        topics = sorted({w.lower() for ln in lines for w in re.findall(r"\b[A-Z][a-z]{3,}\b", ln)})
        if topics:
            suggestions.append(
                {
                    "kind": "collections",
                    "title": "Possible collection topics",
                    "body": ", ".join(topics[:8]),
                }
            )
    # Optional LLM polish — suggestion only
    try:
        from jarvis import llm

        if mode == "llm" and len(raw) > 20:
            prompt = (
                "You help with a personal Bullet Journal. Suggest organization only. "
                "Do NOT rewrite the writer's personal thoughts. Return short bullet suggestions.\n\n"
                f"Text:\n{raw[:2000]}"
            )
            out = llm.ask(
                llm.reflection_model(),
                [{"role": "user", "content": prompt}],
                role="reflection",
            )
            suggestions.append({"kind": "llm", "title": "AI organization ideas", "body": out})
    except Exception:
        log.debug("writing llm assist skipped", exc_info=True)

    return {
        "ok": True,
        "mode": mode,
        "suggestions": suggestions,
        "requires_confirmation": True,
        "message": "Suggestions only — your words were not changed.",
    }


def parse_voice_rapid_log(transcript: str) -> dict[str, Any]:
    """Turn voice transcript into rapid-log lines (confirm before save)."""
    raw = (transcript or "").strip()
    if not raw:
        return {"ok": False, "error": "Empty transcript", "text": "", "requires_confirmation": True}
    # Split on common spoken separators
    parts = re.split(r"\s*(?:(?:then|next|also|and then)|[.;])\s+", raw, flags=re.I)
    lines = []
    for p in parts:
        p = p.strip(" ,")
        if not p:
            continue
        lower = p.lower()
        if lower.startswith(("note ", "note:")):
            lines.append("n: " + re.sub(r"^note[:\s]+", "", p, flags=re.I).strip())
        elif lower.startswith(("event ", "event:", "meeting ")):
            lines.append("e: " + re.sub(r"^(event|meeting)[:\s]+", "", p, flags=re.I).strip())
        elif lower.startswith(("task ", "todo ", "to do ")):
            lines.append("t: " + re.sub(r"^(task|to-?do|todo)[:\s]+", "", p, flags=re.I).strip())
        else:
            lines.append(p)
    text = "\n".join(lines)
    return {
        "ok": True,
        "text": text,
        "lines": lines,
        "requires_confirmation": True,
        "message": "Voice draft ready — review before adding to Rapid Log.",
    }


def vision_import_preview(
    *,
    ocr_text: str = "",
    path: str = "",
    source: str = "scan",
    section: str = "daily",
) -> dict[str, Any]:
    """OCR / vision import preview. Accepts pasted text OR image path via shared OCR."""
    raw = (ocr_text or "").strip()
    if path and not raw:
        from jarvis.vision_product.ocr import run_ocr

        ocr = run_ocr(path)
        if not ocr.get("ok"):
            return {
                "ok": False,
                "error": ocr.get("error") or "OCR failed",
                "requires_confirmation": True,
                "preview_lines": [],
            }
        raw = str(ocr.get("text") or "").strip()
    source = (source or "scan").lower()
    section = (section or "daily").lower()
    if section not in ("daily", "weekly", "monthly", "future", "collections"):
        section = "daily"
    if not raw:
        return {
            "ok": False,
            "error": "No OCR text provided",
            "requires_confirmation": True,
            "preview_lines": [],
        }
    lines = []
    for ln in raw.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        # Normalize common BuJo glyphs from OCR
        ln = ln.replace("·", "•").replace("–", "—").replace("−", "—")
        if re.match(r"^[\d\.\)\]]+\s+", ln):
            ln = re.sub(r"^[\d\.\)\]]+\s+", "• ", ln)
        lines.append(ln)
    return {
        "ok": True,
        "source": source,
        "section": section,
        "path": path or "",
        "preview_lines": lines,
        "text": "\n".join(lines),
        "requires_confirmation": True,
        "pipeline": "vision_import",
        "message": f"Vision import from {source} — approve to add to {section}.",
    }


def disambiguate_tasks_intent(message: str) -> dict[str, Any]:
    """Decide Planner vs Journal vs clarify for 'open tasks' style utterances."""
    lower = (message or "").lower().strip()
    journal_signals = (
        r"\bjournal\b",
        r"\bbujo\b",
        r"\bbullet\b",
        r"\bdaily log\b",
        r"\brapid log\b",
        r"\bmigration\b",
        r"\bcollection\b",
    )
    planner_signals = (
        r"\bplanner\b",
        r"\bschedule\b",
        r"\bdue\b",
        r"\bdeadline\b",
        r"\bpriority\b",
        r"\btimer\b",
        r"\balarm\b",
        r"\bfocus\b",
        r"\btriage\b",
        r"\btoday'?s (work|plan)\b",
    )
    j = any(re.search(p, lower) for p in journal_signals)
    p = any(re.search(p, lower) for p in planner_signals)
    if j and not p:
        return {"action": "journal_open_tasks", "params": {}, "thinking": "journal tasks (explicit)"}
    if p and not j:
        return {"action": "planner_today", "params": {}, "thinking": "planner tasks (explicit)"}
    # Ambiguous generic phrases → Planner is the daily action surface.
    # Asking Planner vs Journal forces Jeff to think about products — don't.
    if re.search(
        r"\b(open tasks|my todos?|to-?do list|things to do|what('s| is) on my (plate|list))\b",
        lower,
    ):
        return {
            "action": "planner_today",
            "params": {},
            "thinking": "daily plate → planner (no product quiz)",
        }
    return {"action": "journal_open_tasks", "params": {}, "thinking": "journal tasks default"}


def month_end_wizard(journal, month: str | None = None) -> dict[str, Any]:
    """Guided month-end review payload (suggestions only)."""
    mk = month or _month_key()
    y, m = map(int, mk.split("-"))
    next_m = f"{y:04d}-{m + 1:02d}" if m < 12 else f"{y + 1:04d}-01"
    open_tasks = [
        t
        for t in (journal.open_tasks() if hasattr(journal, "open_tasks") else [])
        if str(t.get("section") or "").startswith(("monthly", "daily", "weekly"))
    ]
    habits = journal.habit_tracker(mk) if hasattr(journal, "habit_tracker") else {}
    migrate = migration_assistant(journal, scope="monthly")
    return {
        "ok": True,
        "month": mk,
        "next_month": next_m,
        "open_count": len(open_tasks),
        "open_preview": [
            {"id": t.get("id"), "content": _clip(t.get("content") or ""), "section": t.get("section")}
            for t in open_tasks[:15]
        ],
        "habit_summary": habits.get("summary") if isinstance(habits, dict) else {},
        "migration_suggestions": migrate.get("suggestions") or [],
        "steps": [
            "Review open bullets",
            "Accept or skip AI migration suggestions",
            "Carry unfinished work to next month or Future log",
            "Optional: AI monthly reflection",
            "Optional: promote actionable items to Planner",
        ],
        "requires_confirmation": True,
        "message": "Month-end wizard ready — confirm each migration.",
    }


def create_backup(journal) -> dict[str, Any]:
    """Timestamped JSON backup beside the live journal."""
    from datetime import datetime, timezone
    from pathlib import Path

    path = Path(journal.path)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = path.with_name(f"{path.stem}.backup-{stamp}{path.suffix}")
    payload = journal.export_all()
    dest.write_text(__import__("json").dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"ok": True, "path": str(dest), "bytes": dest.stat().st_size}
