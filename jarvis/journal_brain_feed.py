"""Debounced auto-feed from bullet journal into brain memory."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

log = logging.getLogger("jarvis.journal_brain_feed")

_LOCK = threading.Lock()
_LAST_FEED: dict[str, float] = {}
_DEBOUNCE_SEC = float(__import__("os").getenv("JARVIS_JOURNAL_FEED_DEBOUNCE", "45"))


def _enabled() -> bool:
    from jarvis.brain_memory import auto_journal_learn_enabled

    return auto_journal_learn_enabled()


def _substantive_bullet(bullet: dict | None) -> bool:
    if not bullet:
        return False
    content = (bullet.get("content") or "").strip()
    if len(content) < 12:
        return False
    if bullet.get("type") == "note" and bullet.get("status") == "open":
        return True
    if bullet.get("type") == "task":
        return True
    return bullet.get("type") == "event"


def maybe_feed_journal_event(
    memory,
    journal,
    *,
    event: str,
    bullet: dict | None = None,
    day: str | None = None,
    migrated: int = 0,
) -> None:
    """Schedule debounced journal → brain learning (non-blocking)."""
    if not _enabled() or memory is None:
        return
    key = f"{event}:{day or ''}:{bullet.get('id') if bullet else ''}:{migrated}"
    now = time.monotonic()
    with _LOCK:
        if now - _LAST_FEED.get(key, 0.0) < _DEBOUNCE_SEC:
            return
        _LAST_FEED[key] = now

    threading.Thread(
        target=_feed_worker,
        args=(memory, journal, event, bullet, day, migrated),
        daemon=True,
        name="journal-brain-feed",
    ).start()


def _feed_worker(
    memory,
    journal,
    event: str,
    bullet: dict | None,
    day: str | None,
    migrated: int,
) -> None:
    try:
        from jarvis.journal_learning import extract_and_store
        from jarvis.modules.journal import _format_bullet, _today

        d = day or _today()
        if event in ("daily_add", "rapid_add") and _substantive_bullet(bullet):
            text = _format_bullet(bullet)
            extract_and_store(memory, text, project="main", day=d)
        elif event == "task_complete" and _substantive_bullet(bullet):
            text = f"Completed: {_format_bullet(bullet)}"
            extract_and_store(memory, text, project="main", day=d)
        elif event == "migrate_month" and migrated > 0:
            page = journal.monthly_get()
            open_lines = [
                _format_bullet(b)
                for b in (page.get("bullets") or [])
                if b.get("type") == "task" and b.get("status") == "open"
            ]
            if open_lines:
                text = f"Monthly migration — open tasks carried forward:\n" + "\n".join(open_lines[:12])
                extract_and_store(memory, text, project="main", day=d)
        elif event == "migrate_daily" and migrated > 0:
            text = f"Daily migration: moved {migrated} open task(s) forward on {d}."
            extract_and_store(memory, text, project="main", day=d)
    except Exception as exc:
        log.debug("Journal brain feed skipped: %s", exc)


def run_journal_day_consolidation(memory, journal=None, *, day: str | None = None) -> dict[str, Any]:
    """Nightly summary of journal tasks, completions, and habits into memory."""
    from jarvis.brain_memory import auto_journal_learn_enabled
    from jarvis.journal_learning import JOURNAL_LEARN_NAMESPACE, extract_and_store
    from jarvis.modules.journal import BulletJournal, _format_bullet, _today

    if not auto_journal_learn_enabled() or memory is None:
        return {"skipped": True, "reason": "disabled"}

    j = journal or BulletJournal()
    d = day or _today()
    page = j.daily_get(d, enrich=False)
    bullets = page.get("bullets") or []
    open_tasks = [b for b in bullets if b.get("type") == "task" and b.get("status") == "open"]
    done_tasks = [b for b in bullets if b.get("type") == "task" and b.get("status") == "done"]
    tracker = j.habit_tracker(d[:7])
    habits_done = [
        h["name"]
        for h in tracker.get("habits") or []
        if h.get("days", {}).get(d)
    ]

    if not open_tasks and not done_tasks and not habits_done:
        return {"skipped": True, "reason": "empty_day"}

    parts = [f"Journal summary for {d}:"]
    if done_tasks:
        parts.append("Completed: " + "; ".join(_format_bullet(b) for b in done_tasks[:8]))
    if open_tasks:
        parts.append("Still open: " + "; ".join(_format_bullet(b) for b in open_tasks[:8]))
    if habits_done:
        parts.append("Habits: " + ", ".join(habits_done))
    text = "\n".join(parts)
    result = extract_and_store(
        memory,
        text,
        project="main",
        day=d,
        namespace=JOURNAL_LEARN_NAMESPACE,
        max_facts=4,
    )
    return {"skipped": False, "facts": len(result.get("facts") or []), "day": d}
