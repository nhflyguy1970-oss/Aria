"""Bullet Journal extensions — threading, scheduling, wellness, review, undo, links."""

from __future__ import annotations

import copy
import re
from datetime import datetime, timezone

from jarvis.modules.journal import (
    SYMBOLS,
    _format_bullet,
    _month_key,
    _new_bullet,
    _today,
    _week_key,
)

MONTHLY_REVIEW_CHECKLIST = (
    {"id": "scan_monthly", "label": "Review monthly task list"},
    {"id": "scan_future", "label": "Review future log entries"},
    {"id": "migrate_incomplete", "label": "Migrate or schedule incomplete tasks"},
    {"id": "gratitude", "label": "Reflect on gratitude this month"},
    {"id": "habits", "label": "Review habit tracker patterns"},
    {"id": "next_goals", "label": "Set goals for next month"},
    {"id": "collections", "label": "Update active collections"},
    {"id": "index", "label": "Update index for new topics"},
)

WEEKLY_REVIEW_CHECKLIST = (
    {"id": "scan_weekly", "label": "Review weekly task list"},
    {"id": "scan_daily", "label": "Scan daily logs this week"},
    {"id": "migrate_open", "label": "Migrate open tasks to next week / schedule"},
    {"id": "upcoming", "label": "Preview upcoming events"},
    {"id": "habits", "label": "Check habit tracker"},
    {"id": "gratitude", "label": "Note gratitude highlights"},
    {"id": "next_week", "label": "Set intentions for next week"},
)

TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})\s+(.+)$")
TIME_ONLY_RE = re.compile(r"^(\d{1,2}):(\d{2})$")


def _parse_event_time(content: str) -> tuple[str | None, str, int | None]:
    """Parse '14:30 Meeting' or '14:30' prefix from event content."""
    m = TIME_RE.match(content.strip())
    if m:
        hh, mm, rest = m.group(1), m.group(2), m.group(3).strip()
        return f"{int(hh):02d}:{mm}", rest, None
    return None, content.strip(), None


def _search_bullets(bullets: list, bullet_id: str) -> tuple[dict, list, int] | None:
    for i, b in enumerate(bullets):
        if b.get("id") == bullet_id:
            return b, bullets, i
        kids = b.get("children", [])
        hit = _search_bullets(kids, bullet_id)
        if hit:
            return hit
    return None


def _iter_bullets(bullets: list, section: str):
    """Yield all bullets including nested children."""
    for b in bullets:
        yield b, section
        yield from _iter_bullets(b.get("children", []), section)


class BujoMixin:
    """Extra Ryder Carroll methods mixed into BulletJournal."""

    HISTORY_LIMIT = 20

    def _ensure_bujo_meta(self) -> None:
        if "page_counter" not in self._data:
            self._data["page_counter"] = 0
        if "history" not in self._data:
            self._data["history"] = []
        if "redo" not in self._data:
            self._data["redo"] = []
        self._data["version"] = max(self._data.get("version", 1), 2)

    def _alloc_page_number(self) -> int:
        self._ensure_bujo_meta()
        n = int(self._data.get("page_counter", 0)) + 1
        self._data["page_counter"] = n
        return n

    def _ensure_page_number(self, page: dict) -> int:
        if page.get("page_number"):
            return page["page_number"]
        page["page_number"] = self._alloc_page_number()
        return page["page_number"]

    def page_ref(self, page: dict) -> str:
        n = page.get("page_number")
        return f"p.{n}" if n else ""

    def _snapshot_for_undo(self) -> None:
        self._ensure_bujo_meta()
        snap = copy.deepcopy({k: v for k, v in self._data.items() if k != "history"})
        hist = self._data.setdefault("history", [])
        if hist and hist[-1].get("data") == snap:
            return
        hist.append({"ts": datetime.now(timezone.utc).isoformat(), "data": snap})
        self._data["history"] = hist[-self.HISTORY_LIMIT :]

    def undo(self) -> dict:
        self._ensure_bujo_meta()
        hist = self._data.get("history", [])
        if not hist:
            return {"ok": False, "error": "nothing to undo"}
        current = copy.deepcopy({k: v for k, v in self._data.items() if k not in ("history", "redo")})
        redo = self._data.setdefault("redo", [])
        redo.append({"ts": datetime.now(timezone.utc).isoformat(), "data": current})
        self._data["redo"] = redo[-self.HISTORY_LIMIT :]
        prev = hist.pop()
        self._data = prev["data"]
        self._data["history"] = hist
        self._data["redo"] = redo
        self._save(skip_snapshot=True)
        return {"ok": True, "restored_at": prev.get("ts")}

    def redo(self) -> dict:
        self._ensure_bujo_meta()
        redo = self._data.get("redo", [])
        if not redo:
            return {"ok": False, "error": "nothing to redo"}
        current = copy.deepcopy({k: v for k, v in self._data.items() if k not in ("history", "redo")})
        hist = self._data.setdefault("history", [])
        hist.append({"ts": datetime.now(timezone.utc).isoformat(), "data": current})
        self._data["history"] = hist[-self.HISTORY_LIMIT :]
        nxt = redo.pop()
        self._data = nxt["data"]
        self._data["history"] = hist
        self._data["redo"] = redo
        self._save(skip_snapshot=True)
        return {"ok": True, "restored_at": nxt.get("ts")}

    def history_info(self) -> dict:
        self._ensure_bujo_meta()
        hist = self._data.get("history", [])
        redo = self._data.get("redo", [])
        return {
            "count": len(hist),
            "can_undo": bool(hist),
            "redo_count": len(redo),
            "can_redo": bool(redo),
        }

    def update_key(
        self,
        *,
        symbols: dict | None = None,
        description: str | None = None,
        custom: list[dict] | None = None,
    ) -> dict:
        key = self._data.setdefault("key", {})
        if symbols:
            merged = {**SYMBOLS, **key.get("symbols", SYMBOLS), **symbols}
            key["symbols"] = merged
        if description is not None:
            key["description"] = description.strip()
        if custom is not None:
            key["custom"] = custom
        self._save()
        return key

    def _find_bullet_nested(self, bullet_id: str) -> tuple[dict, list, int] | None:
        for section in ("future_log", "monthly_log", "daily_log", "weekly_log"):
            data = self._data.get(section, {})
            if section == "future_log":
                for bullets in data.values():
                    hit = _search_bullets(bullets, bullet_id)
                    if hit:
                        return hit
            else:
                for page in data.values():
                    hit = _search_bullets(page.get("bullets", []), bullet_id)
                    if hit:
                        return hit
        for col in self._data.get("collections", {}).values():
            hit = _search_bullets(col.get("bullets", []), bullet_id)
            if hit:
                return hit
        return None

    def bullet_add_child(
        self,
        parent_id: str,
        content: str,
        bullet_type: str = "task",
        *,
        signifiers: list[str] | None = None,
        time: str | None = None,
    ) -> dict | None:
        found = self._find_bullet_nested(parent_id)
        if not found:
            return None
        parent, _, _ = found
        child = _new_bullet(
            content,
            bullet_type,
            signifiers=signifiers,
            location=parent.get("location", "journal"),
            time=time,
        )
        parent.setdefault("children", []).append(child)
        self._auto_index_bullet(child)
        self._save()
        return child

    def bullet_set_time(
        self,
        bullet_id: str,
        time: str | None = None,
        duration_min: int | None = None,
    ) -> dict | None:
        found = self._find_bullet_nested(bullet_id)
        if not found:
            return None
        b, _, _ = found
        if time is not None:
            b["time"] = time.strip() or None
        if duration_min is not None:
            b["duration_min"] = duration_min
        b["updated"] = datetime.now(timezone.utc).isoformat()
        self._save()
        return b

    def bullet_link(self, from_id: str, to_id: str, label: str = "") -> dict | None:
        found = self._find_bullet_nested(from_id)
        if not found or from_id == to_id:
            return None
        b, _, _ = found
        links = b.setdefault("links", [])
        if not any(link.get("bullet_id") == to_id for link in links):
            links.append({"bullet_id": to_id, "label": (label or "").strip()})
        self._save()
        return b

    def bullet_unlink(self, from_id: str, to_id: str) -> dict | None:
        found = self._find_bullet_nested(from_id)
        if not found:
            return None
        b, _, _ = found
        links = b.get("links", [])
        b["links"] = [link for link in links if link.get("bullet_id") != to_id]
        self._save()
        return b

    def bullet_resolve(self, bullet_id: str) -> dict | None:
        found = self._find_bullet_nested(bullet_id)
        if not found:
            return None
        b, _, _ = found
        return {
            "id": b.get("id"),
            "content": b.get("content"),
            "location": b.get("location"),
            "formatted": _format_bullet(b, self.get_key().get("symbols")),
        }

    def bullet_schedule(self, bullet_id: str, month: str) -> dict | None:
        """BuJo < — mark scheduled and copy to future log."""
        found = self._find_bullet_nested(bullet_id)
        if not found:
            return None
        b, _, _ = found
        if b.get("type") != "task":
            return None
        content = b.get("content", "")
        sigs = list(b.get("signifiers", []))
        btype = b.get("type", "task")
        b["status"] = "scheduled"
        new_b = self.future_add(month, content, btype, sigs)
        new_b.setdefault("links", []).append({"bullet_id": bullet_id, "label": "scheduled from"})
        self._save()
        return new_b

    def bullet_thread_to_daily(
        self,
        bullet_id: str,
        day: str | None = None,
        *,
        duplicate: bool = False,
    ) -> dict | None:
        """Thread task into daily log — default BuJo migrate (>); optional duplicate copy."""
        found = self._find_bullet_nested(bullet_id)
        if not found:
            return None
        b, _, _ = found
        d = day or _today()
        if duplicate:
            new_b = self.daily_add(
                b.get("content", ""),
                b.get("type", "task"),
                b.get("signifiers"),
                day=d,
                time=b.get("time"),
            )
            new_b.setdefault("links", []).append({"bullet_id": bullet_id, "label": "copy from"})
            self._save()
            return new_b
        return self.bullet_migrate(bullet_id, d)

    def bullet_duplicate_to_daily(self, bullet_id: str, day: str | None = None) -> dict | None:
        return self.bullet_thread_to_daily(bullet_id, day, duplicate=True)

    def transfer_future_to_month(self, future_month: str, monthly_month: str | None = None) -> dict:
        mk = monthly_month or _month_key()
        src = self.future_list(future_month)
        if not isinstance(src, list):
            src = []
        moved, kept = [], []
        for b in src:
            if b.get("type") == "task" and b.get("status") == "open":
                self.monthly_add(
                    b.get("content", ""),
                    b.get("type", "task"),
                    b.get("signifiers"),
                    month=mk,
                )
                b["status"] = "migrated"
                moved.append(b)
            else:
                kept.append(b)
        self._data.setdefault("future_log", {})[future_month] = kept
        self._auto_index_monthly_page(mk)
        self._save()
        return {"migrated": len(moved), "month": mk, "from": future_month}

    def daily_set_wellness(
        self,
        day: str,
        *,
        mood: int | None = None,
        gratitude: list[str] | None = None,
    ) -> dict:
        page = self.daily_get(day, enrich=True)
        if mood is not None:
            page["mood"] = max(1, min(5, int(mood))) if mood else None
        if gratitude is not None:
            page["gratitude"] = [g.strip() for g in gratitude if g.strip()]
        self._save()
        return page

    def daily_add_gratitude(self, day: str, text: str) -> dict:
        page = self.daily_get(day, enrich=True)
        items = page.setdefault("gratitude", [])
        t = self._normalize_gratitude_text(text)
        if t:
            items.append(t)
        self._save()
        return page

    @staticmethod
    def _normalize_gratitude_text(text: str) -> str:
        t = text.strip()
        if not t:
            return ""
        prefix = "I am grateful for "
        if t.lower().startswith(prefix.lower()):
            rest = t[len(prefix):].strip()
            return f"{prefix}{rest}" if rest else ""
        return f"{prefix}{t}"

    def wellness_overview(self, month: str | None = None) -> dict:
        mk = month or _month_key()
        prefix = f"{mk}-"
        days = []
        for day_str in sorted(self._data.get("daily_log", {})):
            if not day_str.startswith(prefix):
                continue
            page = self._data["daily_log"][day_str]
            days.append({
                "date": day_str,
                "title": page.get("title", day_str),
                "mood": page.get("mood"),
                "gratitude": page.get("gratitude", []),
            })
        gratitude_all = []
        for d in days:
            for g in d.get("gratitude", []):
                gratitude_all.append({"date": d["date"], "text": g})
        moods = [d["mood"] for d in days if d.get("mood")]
        avg = round(sum(moods) / len(moods), 1) if moods else None
        return {
            "month": mk,
            "days": days,
            "gratitude_stream": gratitude_all[-50:],
            "mood_average": avg,
            "days_logged": len(moods),
        }

    def _default_review(self) -> dict:
        return {item["id"]: False for item in MONTHLY_REVIEW_CHECKLIST}

    def monthly_review_get(self, month: str | None = None) -> dict:
        mk = month or _month_key()
        page = self.monthly_get(mk)
        review = page.setdefault("review", self._default_review())
        for item in MONTHLY_REVIEW_CHECKLIST:
            review.setdefault(item["id"], False)
        return {
            "month": mk,
            "title": page.get("title", mk),
            "checklist": MONTHLY_REVIEW_CHECKLIST,
            "review": review,
            "review_notes": page.get("review_notes", ""),
            "page_number": page.get("page_number"),
        }

    def monthly_review_toggle(self, item_id: str, month: str | None = None) -> dict:
        mk = month or _month_key()
        page = self.monthly_get(mk)
        review = page.setdefault("review", self._default_review())
        review[item_id] = not review.get(item_id, False)
        self._save()
        return self.monthly_review_get(mk)

    def monthly_review_set_notes(self, notes: str, month: str | None = None) -> dict:
        mk = month or _month_key()
        page = self.monthly_get(mk)
        page["review_notes"] = notes.strip()
        self._save()
        return self.monthly_review_get(mk)

    def daily_timeline(self, day: str | None = None) -> dict:
        """Timed events for a day — vertical schedule."""
        d = day or _today()
        page = self.daily_get(d, enrich=False)
        events: list[dict] = []

        def walk(bullets: list) -> None:
            for b in bullets:
                if b.get("type") == "event" and b.get("time"):
                    events.append({
                        "id": b.get("id"),
                        "time": b.get("time"),
                        "content": b.get("content", ""),
                        "duration_min": b.get("duration_min"),
                    })
                walk(b.get("children", []))

        walk(page.get("bullets", []))
        events.sort(key=lambda e: e.get("time", ""))
        return {"day": d, "title": page.get("title", d), "events": events}

    def _default_weekly_review(self) -> dict:
        return {item["id"]: False for item in WEEKLY_REVIEW_CHECKLIST}

    def weekly_review_get(self, week: str | None = None) -> dict:
        wk = week or _week_key()
        page = self.weekly_get(wk)
        review = page.setdefault("review", self._default_weekly_review())
        for item in WEEKLY_REVIEW_CHECKLIST:
            review.setdefault(item["id"], False)
        return {
            "week": wk,
            "title": page.get("title", wk),
            "checklist": WEEKLY_REVIEW_CHECKLIST,
            "review": review,
            "review_notes": page.get("review_notes", ""),
            "page_number": page.get("page_number"),
        }

    def weekly_review_toggle(self, item_id: str, week: str | None = None) -> dict:
        wk = week or _week_key()
        page = self.weekly_get(wk)
        review = page.setdefault("review", self._default_weekly_review())
        review[item_id] = not review.get(item_id, False)
        self._save()
        return self.weekly_review_get(wk)

    def weekly_review_set_notes(self, notes: str, week: str | None = None) -> dict:
        wk = week or _week_key()
        page = self.weekly_get(wk)
        page["review_notes"] = notes.strip()
        self._save()
        return self.weekly_review_get(wk)

    def match_open_task(
        self,
        message: str,
        *,
        bullet_id: str | None = None,
        task_query: str | None = None,
        limit: int = 25,
    ) -> tuple[dict | None, list[dict], str]:
        """Match an open task from chat text. Returns (task, candidates, hint)."""
        tasks = self.open_tasks(limit=999)

        if bullet_id:
            for t in tasks:
                if t.get("id") == bullet_id:
                    return t, [], ""
            found = self._find_bullet(bullet_id)
            if found:
                b, loc, _ = found
                if b.get("type") == "task" and b.get("status") == "open":
                    return {**b, "section": loc}, [], ""
            return None, [], ""

        hint = (task_query or "").strip()
        if not hint:
            for pat in (
                r"schedule\s+['\"](.+?)['\"]\s+to",
                r"schedule\s+(.+?)\s+to\s+\d{4}-\d{2}",
                r"thread\s+['\"](.+?)['\"]\s+to",
                r"thread\s+(.+?)\s+to\s+(?:today|\d{4}-\d{2}-\d{2})",
                r"pull\s+(.+?)\s+to\s+today",
            ):
                m = re.search(pat, message, re.I)
                if m:
                    hint = re.sub(r"^(the|task)\s+", "", m.group(1).strip(), flags=re.I)
                    break

        if hint:
            exact = [t for t in tasks if hint.lower() in t.get("content", "").lower()]
            if len(exact) == 1:
                return exact[0], [], hint
            if len(exact) > 1:
                return None, exact, hint
            words = [w for w in re.findall(r"\w+", hint.lower()) if len(w) > 2]
            if words:
                scored: list[tuple[int, dict]] = []
                for t in tasks:
                    content = t.get("content", "").lower()
                    score = sum(1 for w in words if w in content)
                    if score:
                        scored.append((score, t))
                if scored:
                    scored.sort(key=lambda x: (-x[0], x[1].get("content", "")))
                    best = scored[0][0]
                    top = [t for s, t in scored if s == best]
                    if len(top) == 1:
                        return top[0], [], hint
                    return None, top, hint

        if len(tasks) == 1:
            return tasks[0], [], hint
        if not tasks:
            return None, [], hint
        return None, tasks[:limit], hint

    def ai_reflect_review(self, scope: str = "month", month: str | None = None, week: str | None = None) -> str:
        """AI summary after structured review checklist."""
        from jarvis import llm

        if scope == "week":
            review = self.weekly_review_get(week)
            body = self.format_page("weekly", week or _week_key())
            checklist = review.get("review", {})
        else:
            review = self.monthly_review_get(month)
            body = self.format_page("monthly", month or _month_key())
            checklist = review.get("review", {})
        done = [k for k, v in checklist.items() if v]
        notes = review.get("review_notes", "")
        prompt = f"""Bullet journal {scope} review. Checklist completed: {', '.join(done) or 'none'}.
Review notes: {notes or '(none)'}

Journal content:
{body}

Summarize themes, priorities, and one encouraging next step."""
        return llm.ask(llm.general_model(), [{"role": "user", "content": prompt}])

    def day_events(self, month: str | None = None) -> dict[str, list[dict]]:
        """Events with times grouped by date for calendar display."""
        mk = month or _month_key()
        prefix = f"{mk}-"
        out: dict[str, list[dict]] = {}

        def collect(bullets: list, day_str: str) -> None:
            for b in bullets:
                if b.get("type") == "event" and b.get("time"):
                    out.setdefault(day_str, []).append({
                        "id": b.get("id"),
                        "time": b.get("time"),
                        "content": b.get("content"),
                        "duration_min": b.get("duration_min"),
                    })
                collect(b.get("children", []), day_str)

        for day_str, page in self._data.get("daily_log", {}).items():
            if day_str.startswith(prefix):
                collect(page.get("bullets", []), day_str)
        for day_str in out:
            out[day_str].sort(key=lambda e: e.get("time", ""))
        return out

    def _index_page_label(self, page_type: str, key: str) -> str:
        if page_type == "daily":
            page = self._data.get("daily_log", {}).get(key, {})
        elif page_type == "monthly":
            page = self._data.get("monthly_log", {}).get(key, {})
        elif page_type == "weekly":
            page = self._data.get("weekly_log", {}).get(key, {})
        else:
            return key
        pn = page.get("page_number")
        title = page.get("title", key)
        return f"p.{pn} {title}" if pn else title
