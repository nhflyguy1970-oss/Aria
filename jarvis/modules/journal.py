"""Bullet Journal — Ryder Carroll method with Index, Future Log, Monthly/Daily logs, Collections."""

import calendar
import copy
import json
import os
import re
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

from jarvis import llm
from jarvis.config import JOURNAL_DIR
from jarvis.journal_holidays import holidays_for_month

JOURNAL_FILE = JOURNAL_DIR / "bullet_journal.json"
JOURNAL_PHOTOS_DIR = JOURNAL_DIR / "photos"

# Standard BuJo symbols
SYMBOLS = {
    "task": "•",
    "task_done": "×",
    "task_migrated": ">",
    "task_scheduled": "<",
    "task_cancelled": "~",
    "event": "○",
    "note": "—",
    "important": "*",
    "inspiration": "!",
    "explore": "👁",
}

BULLET_TYPES = ("task", "event", "note")


def _today() -> str:
    return date.today().isoformat()


def _month_key(d: date | None = None) -> str:
    d = d or date.today()
    return f"{d.year:04d}-{d.month:02d}"


def _week_key(d: date | None = None) -> str:
    d = d or date.today()
    iso = d.isocalendar()
    return f"{iso.year:04d}-W{iso.week:02d}"


def _week_range(week: str) -> tuple[str, str]:
    y, w = week.split("-W")
    from datetime import timedelta
    start = date.fromisocalendar(int(y), int(w), 1)
    end = start + timedelta(days=6)
    return start.isoformat(), end.isoformat()


def _new_bullet(
    content: str,
    bullet_type: str = "task",
    *,
    status: str = "open",
    signifiers: list[str] | None = None,
    location: str = "daily",
    time: str | None = None,
    duration_min: int | None = None,
) -> dict:
    return {
        "id": str(uuid.uuid4())[:8],
        "type": bullet_type if bullet_type in BULLET_TYPES else "note",
        "content": content.strip(),
        "status": status,
        "signifiers": signifiers or [],
        "location": location,
        "children": [],
        "links": [],
        "time": time,
        "duration_min": duration_min,
        "created": datetime.now(timezone.utc).isoformat(),
        "updated": datetime.now(timezone.utc).isoformat(),
    }


def _format_bullet(b: dict, symbols: dict | None = None) -> str:
    sym_map = symbols or SYMBOLS

    def _sym(bb: dict) -> str:
        t, s = bb.get("type", "note"), bb.get("status", "open")
        if t == "task":
            if s == "done":
                return sym_map.get("task_done", "×")
            if s == "migrated":
                return sym_map.get("task_migrated", ">")
            if s == "scheduled":
                return sym_map.get("task_scheduled", "<")
            if s == "cancelled":
                return sym_map.get("task_cancelled", "~")
            return sym_map.get("task", "•")
        if t == "event":
            return sym_map.get("event", "○")
        return sym_map.get("note", "—")

    prefix = _sym(b)
    sigs = "".join(
        sym_map.get(s, s) for s in b.get("signifiers", [])
        if s in ("important", "inspiration", "explore")
    )
    time_prefix = f"{b['time']} " if b.get("time") else ""
    line = f"{prefix}{sigs} {time_prefix}{b.get('content', '')}"
    child_lines = []
    for c in b.get("children", []):
        child_lines.append("  " + _format_bullet(c, sym_map))
    if child_lines:
        return line + "\n" + "\n".join(child_lines)
    return line


from jarvis.modules.journal_bujo import BujoMixin, _parse_event_time


class BulletJournal(BujoMixin):
    """Full bullet journal store."""

    def __init__(self, path=None):
        self.path = path or JOURNAL_FILE
        JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
        self._loaded_mtime = 0.0
        self._data = self._load()
        if self.path.exists():
            try:
                self._loaded_mtime = self.path.stat().st_mtime
            except OSError:
                pass

    def _sync_from_disk_if_newer(self) -> None:
        """Reload when another process edited the journal (e.g. cleanup while server runs)."""
        if not self.path.exists():
            return
        try:
            mtime = self.path.stat().st_mtime
        except OSError:
            return
        if mtime <= self._loaded_mtime:
            return
        self._data = self._load()
        self._loaded_mtime = mtime

    def _load(self) -> dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return self._empty()

    def _empty(self) -> dict:
        return {
            "version": 1,
            "key": {
                "symbols": SYMBOLS,
                "description": (
                    "• task  × done  > migrated  < scheduled  ~ cancelled  "
                    "○ event  — note  * important  ! inspiration  👁 explore"
                ),
            },
            "index": [],
            "future_log": {},
            "monthly_log": {},
            "daily_log": {},
            "weekly_log": {},
            "collections": {},
            "habits": {},
            "page_counter": 0,
            "history": [],
        }

    def _save(self, *, skip_snapshot: bool = False) -> None:
        self._sync_from_disk_if_newer()
        self._ensure_bujo_meta()
        current_clean = {k: v for k, v in self._data.items() if k != "history"}
        if not skip_snapshot and self.path.exists():
            try:
                prev = json.loads(self.path.read_text(encoding="utf-8"))
                prev_clean = {k: v for k, v in prev.items() if k != "history"}
                if prev_clean != current_clean:
                    hist = self._data.setdefault("history", [])
                    hist.append({
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "data": copy.deepcopy(prev_clean),
                    })
                    self._data["history"] = hist[-self.HISTORY_LIMIT :]
            except (json.JSONDecodeError, OSError):
                pass
        self.path.parent.mkdir(parents=True, exist_ok=True)
        from jarvis.live_data_guard import assert_live_write_allowed

        assert_live_write_allowed(self.path)
        self.path.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        try:
            self._loaded_mtime = self.path.stat().st_mtime
        except OSError:
            pass

    def get_key(self) -> dict:
        return self._data.get("key", {})

    def export_all(self) -> dict:
        return self._data

    def import_all(self, data: dict) -> None:
        self._data = data
        self._save()

    # --- Index ---
    def index_add(self, topic: str, pages: list[str] | None = None) -> dict:
        entry = {
            "id": str(uuid.uuid4())[:8],
            "topic": topic.strip(),
            "pages": pages or [],
            "created": datetime.now(timezone.utc).isoformat(),
        }
        self._data.setdefault("index", []).append(entry)
        self._save()
        return entry

    def index_list(self) -> list[dict]:
        return self._data.get("index", [])

    def index_update(self, entry_id: str, topic: str | None = None, pages: list[str] | None = None) -> dict | None:
        for e in self._data.get("index", []):
            if e.get("id") == entry_id:
                if topic is not None:
                    e["topic"] = topic.strip()
                if pages is not None:
                    e["pages"] = pages
                self._save()
                return e
        return None

    def index_delete(self, entry_id: str) -> bool:
        idx = self._data.get("index", [])
        for i, e in enumerate(idx):
            if e.get("id") == entry_id:
                del idx[i]
                self._save()
                return True
        return False

    def _index_remove_auto(self, source: str) -> bool:
        idx = self._data.get("index", [])
        for i, e in enumerate(idx):
            if e.get("auto_source") == source:
                del idx[i]
                self._save()
                return True
        return False

    def _index_upsert_auto(self, source: str, topic: str, pages: list[str]) -> dict:
        idx = self._data.setdefault("index", [])
        for e in idx:
            if e.get("auto_source") == source:
                e["topic"] = topic.strip()
                e["pages"] = pages
                e["auto"] = True
                self._save()
                return e
        entry = {
            "id": str(uuid.uuid4())[:8],
            "topic": topic.strip(),
            "pages": pages,
            "auto": True,
            "auto_source": source,
            "created": datetime.now(timezone.utc).isoformat(),
        }
        idx.append(entry)
        self._save()
        return entry

    def _auto_index_daily_page(self, day: str) -> None:
        page = self._data.get("daily_log", {}).get(day)
        if not page or not page.get("bullets"):
            self._index_remove_auto(f"daily:{day}")
            return
        self._ensure_page_number(page)
        self._index_upsert_auto(
            f"daily:{day}",
            page.get("title", day),
            [f"daily:{day}", self.page_ref(page)],
        )

    def _auto_index_monthly_page(self, month: str) -> None:
        page = self._data.get("monthly_log", {}).get(month)
        if not page:
            self._index_remove_auto(f"monthly:{month}")
            return
        has_content = bool(page.get("bullets")) or bool(page.get("calendar_notes"))
        prefix = f"{month}-"
        has_daily = any(d.startswith(prefix) for d in self._data.get("daily_log", {}))
        if not has_content and not has_daily:
            self._index_remove_auto(f"monthly:{month}")
            return
        self._ensure_page_number(page)
        self._index_upsert_auto(
            f"monthly:{month}",
            page.get("title", month),
            [f"monthly:{month}", self.page_ref(page)],
        )

    def _auto_index_weekly_page(self, week: str) -> None:
        page = self._data.get("weekly_log", {}).get(week)
        if not page or not page.get("bullets"):
            self._index_remove_auto(f"weekly:{week}")
            return
        self._ensure_page_number(page)
        self._index_upsert_auto(
            f"weekly:{week}",
            page.get("title", week),
            [f"weekly:{week}", self.page_ref(page)],
        )

    def _auto_index_bullet(self, bullet: dict) -> None:
        src = f"bullet:{bullet.get('id', '')}"
        sigs = bullet.get("signifiers", [])
        if not any(s in sigs for s in ("important", "inspiration")):
            self._index_remove_auto(src)
            return
        content = bullet.get("content", "").strip()
        if not content:
            self._index_remove_auto(src)
            return
        prefix = "! " if "inspiration" in sigs else "★ " if "important" in sigs else ""
        topic = content[:80] + ("…" if len(content) > 80 else "")
        self._index_upsert_auto(src, f"{prefix}{topic}", [bullet.get("location", "journal")])

    def rebuild_auto_index(self) -> dict:
        """Rebuild auto-generated index entries; manual entries are preserved."""
        manual = [e for e in self._data.get("index", []) if not e.get("auto")]
        self._data["index"] = manual
        counts = {"daily": 0, "monthly": 0, "weekly": 0, "collection": 0, "bullet": 0}

        for day in self._data.get("daily_log", {}):
            page = self._data["daily_log"][day]
            if page.get("bullets"):
                self._auto_index_daily_page(day)
                counts["daily"] += 1

        for month in self._data.get("monthly_log", {}):
            self._auto_index_monthly_page(month)
            if any(e.get("auto_source") == f"monthly:{month}" for e in self.index_list()):
                counts["monthly"] += 1

        for week in self._data.get("weekly_log", {}):
            self._auto_index_weekly_page(week)
            if any(e.get("auto_source") == f"weekly:{week}" for e in self.index_list()):
                counts["weekly"] += 1

        for name in self._data.get("collections", {}):
            self._index_upsert_auto(f"collection:{name}", name, [f"collection:{name}"])
            counts["collection"] += 1

        for section in ("future_log", "monthly_log", "daily_log", "weekly_log"):
            data = self._data.get(section, {})
            if section == "future_log":
                for bullets in data.values():
                    for b in bullets:
                        if any(s in b.get("signifiers", []) for s in ("important", "inspiration")):
                            self._auto_index_bullet(b)
                            counts["bullet"] += 1
            else:
                for page in data.values():
                    for b in page.get("bullets", []):
                        if any(s in b.get("signifiers", []) for s in ("important", "inspiration")):
                            self._auto_index_bullet(b)
                            counts["bullet"] += 1
        for col in self._data.get("collections", {}).values():
            for b in col.get("bullets", []):
                if any(s in b.get("signifiers", []) for s in ("important", "inspiration")):
                    self._auto_index_bullet(b)
                    counts["bullet"] += 1

        return {
            "manual": len(manual),
            "auto": sum(counts.values()),
            **counts,
            "total": len(self.index_list()),
        }

    def index_resolve_page(self, page_ref: str) -> dict | None:
        """Map an index page reference to a navigable journal location."""
        ref = page_ref.strip()
        for prefix, kind, key_name in (
            ("daily:", "daily", "day"),
            ("monthly:", "monthly", "month"),
            ("weekly:", "weekly", "week"),
            ("collection:", "collection", "name"),
            ("future:", "future", "month"),
        ):
            if ref.startswith(prefix):
                return {key_name: ref.split(":", 1)[1], "type": kind}
        if re.match(r"^\d{4}-\d{2}-\d{2}$", ref):
            return {"type": "daily", "day": ref}
        if re.match(r"^\d{4}-\d{2}$", ref):
            return {"type": "monthly", "month": ref}
        return None

    # --- Future Log ---
    def future_add(self, month: str, content: str, bullet_type: str = "task", signifiers: list[str] | None = None) -> dict:
        fl = self._data.setdefault("future_log", {})
        fl.setdefault(month, [])
        b = _new_bullet(content, bullet_type, signifiers=signifiers, location=f"future:{month}")
        fl[month].append(b)
        self._auto_index_bullet(b)
        self._save()
        return b

    def future_list(self, month: str | None = None) -> dict | list:
        fl = self._data.get("future_log", {})
        if month:
            return fl.get(month, [])
        return fl

    # --- Monthly Log ---
    def _ensure_monthly(self, month: str) -> dict:
        ml = self._data.setdefault("monthly_log", {})
        if month not in ml:
            y, m = map(int, month.split("-"))
            page = {
                "month": month,
                "title": date(y, m, 1).strftime("%B %Y"),
                "bullets": [],
                "calendar_notes": {},
                "review": self._default_review(),
                "review_notes": "",
            }
            self._ensure_page_number(page)
            ml[month] = page
        return ml[month]

    def monthly_add(self, content: str, bullet_type: str = "task", signifiers: list[str] | None = None, month: str | None = None) -> dict:
        mk = month or _month_key()
        page = self._ensure_monthly(mk)
        b = _new_bullet(content, bullet_type, signifiers=signifiers, location=f"monthly:{mk}")
        page["bullets"].append(b)
        self._auto_index_monthly_page(mk)
        self._auto_index_bullet(b)
        self._save()
        return b

    def monthly_get(self, month: str | None = None) -> dict:
        return self._ensure_monthly(month or _month_key())

    def monthly_calendar(self, month: str | None = None) -> dict:
        """Calendar grid for a month with per-day entry counts."""
        mk = month or _month_key()
        page = self._ensure_monthly(mk)
        y, m = map(int, mk.split("-"))
        weeks = calendar.monthcalendar(y, m)
        daily = self._data.get("daily_log", {})
        days: dict[str, dict] = {}
        prefix = f"{mk}-"
        for day_str, day_page in daily.items():
            if not day_str.startswith(prefix):
                continue
            try:
                day_num = int(day_str.split("-")[2])
            except (IndexError, ValueError):
                continue
            bullets = day_page.get("bullets", [])
            days[str(day_num)] = {
                "date": day_str,
                "title": day_page.get("title", day_str),
                "count": len(bullets),
                "open_tasks": sum(
                    1 for b in bullets
                    if b.get("type") == "task" and b.get("status") == "open"
                ),
            }
        notes = page.get("calendar_notes", {})
        events = self.day_events(mk)
        holidays = holidays_for_month(mk)
        return {
            "month": mk,
            "title": page.get("title", mk),
            "page_number": page.get("page_number"),
            "weeks": weeks,
            "days": days,
            "events": events,
            "holidays": holidays,
            "calendar_notes": notes,
            "monthly_bullets": page.get("bullets", []),
            "today": _today(),
        }

    def monthly_calendar_note(self, day: int, note: str, month: str | None = None) -> dict:
        page = self._ensure_monthly(month or _month_key())
        page.setdefault("calendar_notes", {})[str(day)] = note.strip()
        self._auto_index_monthly_page(month or _month_key())
        self._save()
        return page

    # --- Daily Log ---
    def _ensure_daily(self, day: str) -> dict:
        dl = self._data.setdefault("daily_log", {})
        if day not in dl:
            d = date.fromisoformat(day)
            page: dict = {
                "date": day,
                "title": d.strftime("%A, %B %d, %Y"),
                "bullets": [],
                "gratitude": [],
                "mood": None,
            }
            self._ensure_page_number(page)
            dl[day] = page
        return dl[day]

    def daily_add(
        self,
        content: str,
        bullet_type: str = "task",
        signifiers: list[str] | None = None,
        day: str | None = None,
        *,
        time: str | None = None,
    ) -> dict:
        d = day or _today()
        page = self._ensure_daily(d)
        parsed_time, body, _ = _parse_event_time(content) if bullet_type == "event" else (time, content, None)
        if bullet_type == "event" and not time:
            time = parsed_time
            content = body
        b = _new_bullet(content, bullet_type, signifiers=signifiers, location=f"daily:{d}", time=time)
        page["bullets"].append(b)
        self._auto_index_daily_page(d)
        self._auto_index_bullet(b)
        self._save()
        return b

    def daily_get(self, day: str | None = None, *, enrich: bool = True) -> dict:
        self._sync_from_disk_if_newer()
        d = day or _today()
        page = self._ensure_daily(d)
        if enrich:
            self._enrich_daily_page(page)
        return page

    def _enrich_daily_page(self, page: dict) -> dict:
        from jarvis.journal_prompts import prompts_for_day
        from jarvis.journal_quotes import daily_quote
        from jarvis.journal_weather import weather_for_day

        day = page.get("date", _today())
        dirty = False
        w = page.get("weather") or {}
        loc_key = (
            os.getenv("JARVIS_WEATHER_LAT", ""),
            os.getenv("JARVIS_WEATHER_LON", ""),
            os.getenv("JARVIS_WEATHER_LOCATION", ""),
        )
        if w.get("date") != day or w.get("loc_key") != loc_key or not w.get("icon"):
            fetched = weather_for_day(day)
            if fetched:
                fetched["loc_key"] = loc_key
                page["weather"] = fetched
                dirty = True
        if not page.get("quote"):
            page["quote"] = daily_quote(day)
            dirty = True
        prompts = page.setdefault("prompts", {})
        defaults = prompts_for_day(day)
        if "morning_question" not in prompts:
            prompts["morning_question"] = defaults["morning_question"]
            dirty = True
        if "evening_question" not in prompts:
            prompts["evening_question"] = defaults["evening_question"]
            dirty = True
        prompts.setdefault("morning", prompts.get("morning", ""))
        prompts.setdefault("evening", prompts.get("evening", ""))
        if "photos" not in page:
            page["photos"] = []
            dirty = True
        if dirty:
            self._save()
        return page

    def daily_set_prompts(
        self,
        day: str,
        *,
        morning: str | None = None,
        evening: str | None = None,
    ) -> dict:
        page = self.daily_get(day, enrich=True)
        if morning is not None:
            page["prompts"]["morning"] = morning.strip()
        if evening is not None:
            page["prompts"]["evening"] = evening.strip()
        self._save()
        return page

    def daily_add_photo(self, day: str, filename: str, content: bytes, caption: str = "") -> dict:
        page = self.daily_get(day, enrich=True)
        JOURNAL_PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
        ext = Path(filename).suffix.lower() or ".jpg"
        if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
            ext = ".jpg"
        pid = uuid.uuid4().hex[:10]
        safe = f"{day}_{pid}{ext}"
        path = JOURNAL_PHOTOS_DIR / safe
        path.write_bytes(content)
        entry = {
            "id": pid,
            "filename": safe,
            "caption": (caption or "").strip(),
            "created": datetime.now(timezone.utc).isoformat(),
        }
        page["photos"].append(entry)
        self._save()
        return entry

    def daily_delete_photo(self, day: str, photo_id: str) -> bool:
        page = self.daily_get(day, enrich=False)
        photos = page.get("photos", [])
        for i, p in enumerate(photos):
            if p.get("id") == photo_id:
                fp = JOURNAL_PHOTOS_DIR / p.get("filename", "")
                if fp.is_file():
                    fp.unlink(missing_ok=True)
                del photos[i]
                self._save()
                return True
        return False

    def photo_path(self, filename: str) -> Path | None:
        fp = JOURNAL_PHOTOS_DIR / filename
        return fp if fp.is_file() else None

    def daily_list_dates(self, limit: int = 30) -> list[str]:
        dates = sorted(self._data.get("daily_log", {}).keys(), reverse=True)
        return dates[:limit]

    # --- Weekly Log ---
    def _ensure_weekly(self, week: str) -> dict:
        wl = self._data.setdefault("weekly_log", {})
        if week not in wl:
            start, end = _week_range(week)
            page = {
                "week": week,
                "title": f"Week {week.split('-W')[1]} · {start} — {end}",
                "start": start,
                "end": end,
                "bullets": [],
            }
            self._ensure_page_number(page)
            wl[week] = page
        return wl[week]

    def weekly_add(self, content: str, bullet_type: str = "task", week: str | None = None, **kw) -> dict:
        wk = week or _week_key()
        page = self._ensure_weekly(wk)
        b = _new_bullet(content, bullet_type, signifiers=kw.get("signifiers"), location=f"weekly:{wk}")
        page["bullets"].append(b)
        self._auto_index_weekly_page(wk)
        self._auto_index_bullet(b)
        self._save()
        return b

    def weekly_get(self, week: str | None = None) -> dict:
        return self._ensure_weekly(week or _week_key())

    # --- Habits ---
    DEFAULT_HABITS = (
        ("meditation", "Meditation"),
        ("exercise", "Exercise"),
        ("reading", "Reading"),
        ("tai_chi", "Tai Chi practice"),
        ("journal", "Journal"),
    )

    def habit_list(self) -> list[dict]:
        habits = self._data.setdefault("habits", {})
        if not habits:
            for hid, name in self.DEFAULT_HABITS:
                habits[hid] = {"id": hid, "name": name, "track": {}, "custom": False}
            self._save()
        return list(habits.values())

    def habit_create(self, name: str) -> dict:
        hid = re.sub(r"[^\w-]+", "-", name.lower()).strip("-") or uuid.uuid4().hex[:8]
        habits = self._data.setdefault("habits", {})
        if hid in habits:
            return habits[hid]
        entry = {"id": hid, "name": name.strip(), "track": {}, "custom": True}
        habits[hid] = entry
        self._save()
        return entry

    def habit_toggle(self, habit_id: str, day: str | None = None) -> dict | None:
        self.habit_list()
        habits = self._data.get("habits", {})
        h = habits.get(habit_id)
        if not h:
            return None
        d = day or _today()
        track = h.setdefault("track", {})
        track[d] = not track.get(d, False)
        self._save()
        return h

    def habit_tracker(self, month: str | None = None) -> dict:
        mk = month or _month_key()
        y, m = map(int, mk.split("-"))
        import calendar as cal_mod
        days_in = cal_mod.monthrange(y, m)[1]
        days = [f"{mk}-{d:02d}" for d in range(1, days_in + 1)]
        habits = self.habit_list()
        rows = []
        for h in habits:
            track = h.get("track", {})
            rows.append({
                **h,
                "days": {d: bool(track.get(d)) for d in days},
                "done_count": sum(1 for d in days if track.get(d)),
            })
        return {"month": mk, "days": days, "habits": rows}

    def bullet_remember_text(self, bullet_id: str) -> str | None:
        found = self._find_bullet(bullet_id)
        if not found:
            return None
        b, _, _ = found
        loc = b.get("location", "journal")
        return f"From bullet journal ({loc}): {_format_bullet(b)}"

    # --- Collections ---
    def collection_create(self, name: str, description: str = "") -> dict:
        col = self._data.setdefault("collections", {})
        if name in col:
            return col[name]
        col[name] = {
            "name": name,
            "description": description,
            "bullets": [],
            "created": datetime.now(timezone.utc).isoformat(),
        }
        self._ensure_page_number(col[name])
        self._index_collection(name)
        self._save()
        return col[name]

    def _index_collection(self, name: str) -> None:
        col = self._data.get("collections", {}).get(name, {})
        self._index_upsert_auto(
            f"collection:{name}",
            name,
            [f"collection:{name}", self.page_ref(col)],
        )

    def collection_add(self, name: str, content: str, bullet_type: str = "task", signifiers: list[str] | None = None) -> dict:
        col = self.collection_create(name)
        b = _new_bullet(content, bullet_type, signifiers=signifiers, location=f"collection:{name}")
        col["bullets"].append(b)
        self._auto_index_bullet(b)
        self._save()
        return b

    def collection_get(self, name: str) -> dict | None:
        return self._data.get("collections", {}).get(name)

    def collection_list(self) -> list[str]:
        return list(self._data.get("collections", {}).keys())

    # --- Bullet CRUD (any location) ---
    def _find_bullet(self, bullet_id: str) -> tuple[dict, list, int] | None:
        return self._find_bullet_nested(bullet_id)

    def bullet_update(
        self,
        bullet_id: str,
        *,
        content: str | None = None,
        status: str | None = None,
        bullet_type: str | None = None,
        signifiers: list[str] | None = None,
    ) -> dict | None:
        found = self._find_bullet(bullet_id)
        if not found:
            return None
        b, _, _ = found
        if content is not None:
            b["content"] = content.strip()
        if status is not None:
            b["status"] = status
        if bullet_type is not None:
            b["type"] = bullet_type
        if signifiers is not None:
            b["signifiers"] = signifiers
        b["updated"] = datetime.now(timezone.utc).isoformat()
        self._auto_index_bullet(b)
        self._save()
        return b

    def bullet_toggle_signifier(self, bullet_id: str, signifier: str) -> dict | None:
        if signifier not in ("important", "inspiration", "explore"):
            return None
        found = self._find_bullet(bullet_id)
        if not found:
            return None
        b, _, _ = found
        sigs = list(b.get("signifiers", []))
        if signifier in sigs:
            sigs.remove(signifier)
        else:
            sigs.append(signifier)
        return self.bullet_update(bullet_id, signifiers=sigs)

    def bullet_cancel(self, bullet_id: str) -> dict | None:
        return self.bullet_update(bullet_id, status="cancelled")

    def bullet_delete(self, bullet_id: str) -> bool:
        found = self._find_bullet(bullet_id)
        if not found:
            return False
        b, bullets, i = found
        loc = b.get("location", "")
        self._index_remove_auto(f"bullet:{bullet_id}")
        del bullets[i]
        self._reindex_location(loc)
        self._save()
        return True

    def _reindex_location(self, location: str) -> None:
        if not location or ":" not in location:
            return
        kind, key = location.split(":", 1)
        if kind == "daily":
            self._auto_index_daily_page(key)
        elif kind == "monthly":
            self._auto_index_monthly_page(key)
        elif kind == "weekly":
            self._auto_index_weekly_page(key)

    def bullet_complete(self, bullet_id: str) -> dict | None:
        return self.bullet_update(bullet_id, status="done")

    def bullet_migrate(self, bullet_id: str, target: str) -> dict | None:
        """Migrate task — mark source > and create at target (BuJo faithful)."""
        found = self._find_bullet(bullet_id)
        if not found:
            return None
        b, _, _ = found
        if b.get("type") != "task" or b.get("status") != "open":
            return None
        content = b.get("content", "")
        sigs = b.get("signifiers", [])
        btype = b.get("type", "task")
        b["status"] = "migrated"
        b["updated"] = datetime.now(timezone.utc).isoformat()
        if re.match(r"^\d{4}-\d{2}-\d{2}$", target):
            new_b = self.daily_add(content, btype, sigs, day=target)
        elif re.match(r"^\d{4}-\d{2}$", target):
            new_b = self.future_add(target, content, btype, sigs)
        else:
            new_b = self.monthly_add(content, btype, sigs, month=target)
        self._save()
        return new_b

    def migrate_month(self, from_month: str, to_month: str, *, dest: str = "monthly") -> dict:
        """BuJo monthly migration — open tasks to next monthly log or future log."""
        page = self.monthly_get(from_month)
        moved = []
        for b in page.get("bullets", []):
            if b.get("type") == "task" and b.get("status") == "open":
                b["status"] = "migrated"
                b["updated"] = datetime.now(timezone.utc).isoformat()
                if dest == "future":
                    self.future_add(to_month, b["content"], "task", b.get("signifiers"))
                else:
                    self.monthly_add(b["content"], "task", b.get("signifiers"), month=to_month)
                moved.append(b)
        if dest == "monthly":
            self._auto_index_monthly_page(to_month)
        self._save()
        open_left = sum(1 for b in page.get("bullets", []) if b.get("type") == "task" and b.get("status") == "open")
        return {"migrated": len(moved), "remaining": open_left, "dest": dest, "to_month": to_month}

    def migrate_daily_open(self, from_day: str, to_day: str) -> dict:
        page = self.daily_get(from_day)
        moved = 0
        for b in page.get("bullets", []):
            if b.get("type") == "task" and b.get("status") == "open":
                b["status"] = "migrated"
                b["updated"] = datetime.now(timezone.utc).isoformat()
                self.daily_add(b["content"], "task", b.get("signifiers"), day=to_day)
                moved += 1
        self._save()
        return {"migrated": moved, "to_day": to_day}

    def open_tasks(self, *, day: str | None = None, month: str | None = None, limit: int = 25) -> list[dict]:
        """Open tasks from today's daily log, current monthly log, and future log."""
        d = day or _today()
        mk = month or _month_key()
        tasks: list[dict] = []

        for b in self.daily_get(d).get("bullets", []):
            if b.get("type") == "task" and b.get("status") == "open":
                tasks.append({**b, "section": f"daily:{d}"})

        for b in self.monthly_get(mk).get("bullets", []):
            if b.get("type") == "task" and b.get("status") == "open":
                tasks.append({**b, "section": f"monthly:{mk}"})

        wk = _week_key()
        for b in self.weekly_get(wk).get("bullets", []):
            if b.get("type") == "task" and b.get("status") == "open":
                tasks.append({**b, "section": f"weekly:{wk}"})

        fl = self.future_list()
        if isinstance(fl, dict):
            for fm, bullets in sorted(fl.items()):
                if fm < mk:
                    continue
                for b in bullets:
                    if b.get("type") == "task" and b.get("status") == "open":
                        tasks.append({**b, "section": f"future:{fm}"})

        for name, col in self._data.get("collections", {}).items():
            for b in col.get("bullets", []):
                if b.get("type") == "task" and b.get("status") == "open":
                    tasks.append({**b, "section": f"collection:{name}"})

        return tasks[:limit]

    def stats(self) -> dict:
        daily = self._data.get("daily_log", {})
        monthly = self._data.get("monthly_log", {})
        future = self._data.get("future_log", {})
        collections = self._data.get("collections", {})
        habits = self._data.get("habits", {})
        weekly = self._data.get("weekly_log", {})
        return {
            "daily_pages": len(daily),
            "monthly_pages": len(monthly),
            "future_months": len(future),
            "collections": len(collections),
            "weekly_pages": len(weekly),
            "habits": len(habits),
            "index_entries": len(self.index_list()),
            "open_tasks": len(self.open_tasks(limit=999)),
            "today": _today(),
            "month": _month_key(),
        }

    def format_open_tasks(self, limit: int = 15) -> str:
        tasks = self.open_tasks(limit=limit)
        if not tasks:
            return "No open journal tasks."
        return "\n".join(f"- [{t.get('section')}] {_format_bullet(t)}" for t in tasks)

    def search(self, query: str, limit: int = 20) -> list[dict]:
        from jarvis.modules.journal_bujo import _iter_bullets

        q = query.lower()
        hits = []
        for section_name, getter in (
            ("index", lambda: [{"content": e["topic"], **e} for e in self.index_list()]),
        ):
            for item in getter():
                if q in str(item).lower():
                    hits.append({**item, "section": section_name})

        future = self.future_list()
        for month, bullets in future.items() if isinstance(future, dict) else []:
            for b, sec in _iter_bullets(bullets, f"future:{month}"):
                if q in b.get("content", "").lower():
                    hits.append({**b, "section": sec})

        for month, page in self._data.get("monthly_log", {}).items():
            for b, sec in _iter_bullets(page.get("bullets", []), f"monthly:{month}"):
                if q in b.get("content", "").lower():
                    hits.append({**b, "section": sec})

        for day, page in self._data.get("daily_log", {}).items():
            for b, sec in _iter_bullets(page.get("bullets", []), f"daily:{day}"):
                if q in b.get("content", "").lower():
                    hits.append({**b, "section": sec})

        for week, page in self._data.get("weekly_log", {}).items():
            for b, sec in _iter_bullets(page.get("bullets", []), f"weekly:{week}"):
                if q in b.get("content", "").lower():
                    hits.append({**b, "section": sec})

        for name, col in self._data.get("collections", {}).items():
            for b, sec in _iter_bullets(col.get("bullets", []), f"collection:{name}"):
                if q in b.get("content", "").lower():
                    hits.append({**b, "section": sec})

        return hits[:limit]

    def format_page(self, section: str, key: str | None = None) -> str:
        lines = []
        if section == "index":
            lines.append("# Index\n")
            for e in self.index_list():
                pages = ", ".join(e.get("pages", []))
                lines.append(f"{e['topic']} .......... {pages}")
        elif section == "future":
            lines.append("# Future Log\n")
            future = self.future_list()
            for month in sorted(future.keys()) if isinstance(future, dict) else []:
                lines.append(f"\n## {month}\n")
                for b in self.future_list(month):
                    lines.append(_format_bullet(b))
        elif section == "monthly":
            mk = key or _month_key()
            page = self.monthly_get(mk)
            lines.append(f"# {page.get('title', mk)}\n")
            notes = page.get("calendar_notes", {})
            if notes:
                lines.append("\n## Calendar\n")
                for d, n in sorted(notes.items(), key=lambda x: int(x[0])):
                    lines.append(f"  {d}: {n}")
            lines.append("\n## Tasks & Events\n")
            for b in page.get("bullets", []):
                lines.append(_format_bullet(b))
        elif section == "daily":
            dk = key or _today()
            page = self.daily_get(dk)
            lines.append(f"# {page.get('title', dk)}\n")
            from jarvis.journal_weather import format_weather_line

            wline = format_weather_line(page.get("weather"))
            if wline:
                lines.append(f"Weather: {wline}\n")
            q = page.get("quote") or {}
            if q.get("text"):
                lines.append(f"\n> {q['text']}\n> — {q.get('author', '')}\n")
            prompts = page.get("prompts") or {}
            if prompts.get("morning"):
                lines.append(f"\nMorning: {prompts['morning']}")
            if prompts.get("evening"):
                lines.append(f"Evening: {prompts['evening']}")
            lines.append("")
            for b in page.get("bullets", []):
                lines.append(_format_bullet(b))
        elif section == "weekly":
            wk = key or _week_key()
            page = self.weekly_get(wk)
            lines.append(f"# {page.get('title', wk)}\n")
            for b in page.get("bullets", []):
                lines.append(_format_bullet(b))
        elif section == "collection" and key:
            col = self.collection_get(key)
            if col:
                lines.append(f"# Collection: {key}\n")
                if col.get("description"):
                    lines.append(col["description"] + "\n")
                for b in col.get("bullets", []):
                    lines.append(_format_bullet(b))
        return "\n".join(lines)

    def parse_rapid_log(self, text: str, day: str | None = None, *, default_type: str = "task") -> list[dict]:
        """Parse symbol-prefixed lines; indent with 2 spaces to nest under previous bullet."""
        if default_type not in BULLET_TYPES:
            default_type = "task"
        created: list[dict] = []
        parents: list[dict] = []

        def parse_line(raw: str) -> tuple[str, str, list[str], str, str | None]:
            bullet_type, status, signifiers, content = default_type, "open", [], raw.strip()
            lower = content.lower()
            if lower.startswith("t:"):
                bullet_type, content = "task", content[2:].strip()
            elif lower.startswith("e:"):
                bullet_type, content = "event", content[2:].strip()
            elif lower.startswith("n:"):
                bullet_type, content = "note", content[2:].strip()
            elif content.startswith("×") or lower.startswith("x "):
                bullet_type, status = "task", "done"
                content = content[1:].strip()
            elif content.startswith(">"):
                bullet_type, status = "task", "migrated"
                content = content[1:].strip()
            elif content.startswith("<"):
                bullet_type, status = "task", "scheduled"
                content = content[1:].strip()
            elif content.startswith("•"):
                bullet_type = "task"
                content = content[1:].strip()
            elif content.startswith("-"):
                bullet_type = "note"
                content = content[1:].strip()
            elif content.startswith("○") or content.startswith("O "):
                bullet_type = "event"
                content = content[1:].strip() if content.startswith("○") else content[2:].strip()
            elif content.startswith("—") or content.startswith("--"):
                bullet_type = "note"
                content = content.lstrip("—-").strip()
            if content.startswith("*"):
                signifiers.append("important")
                content = content.lstrip("*").strip()
            if content.startswith("!"):
                signifiers.append("inspiration")
                content = content.lstrip("!").strip()
            event_time = None
            if bullet_type == "event":
                event_time, content, _ = _parse_event_time(content)
            return bullet_type, status, signifiers, content, event_time

        for raw_line in text.splitlines():
            if not raw_line.strip():
                continue
            indent = len(raw_line) - len(raw_line.lstrip(" "))
            level = indent // 2
            bullet_type, status, signifiers, content, event_time = parse_line(raw_line)
            if not content:
                continue
            if level == 0 or not parents:
                b = self.daily_add(content, bullet_type, signifiers, day=day, time=event_time)
                parents[:] = [b]
            else:
                parent = parents[min(level - 1, len(parents) - 1)]
                child = self.bullet_add_child(
                    parent["id"], content, bullet_type, signifiers=signifiers, time=event_time,
                )
                if child is None:
                    b = self.daily_add(content, bullet_type, signifiers, day=day, time=event_time)
                    parents[:] = [b]
                else:
                    b = child
                    if len(parents) > level:
                        parents[level] = b
                    elif len(parents) == level:
                        parents.append(b)
                    else:
                        while len(parents) < level:
                            parents.append(parents[-1])
                        parents.append(b)
            if status != "open":
                self.bullet_update(b["id"], status=status)
            created.append(b)
        return created

    def ai_reflect(self, scope: str = "week") -> str:
        """AI-assisted journal reflection."""
        if scope == "month":
            self.monthly_get()
            text = self.format_page("monthly")
        elif scope == "today":
            text = self.format_page("daily")
        else:
            days = self.daily_list_dates(7)
            parts = [self.format_page("daily", d) for d in days]
            text = "\n\n".join(parts)
        prompt = f"""You are a bullet journal reflection assistant. Review this journal content and provide:
1. Key themes
2. Open tasks to prioritize
3. Suggested migrations or scheduling
4. A brief encouraging summary

Journal:
{text}
"""
        return llm.ask(llm.general_model(), [{"role": "user", "content": prompt}])


class JournalEngine:
    def __init__(self):
        self.journal = BulletJournal()

    def handle(self, prompt: str) -> bool:
        if prompt.lower() == "exit":
            return False
        j = self.journal
        p = prompt.strip()

        if p.startswith("log "):
            entries = j.parse_rapid_log(p[4:])
            print(f"\nAdded {len(entries)} bullets to today.\n")
            return True
        if p == "today":
            print("\n" + j.format_page("daily") + "\n")
            return True
        if p == "index":
            print("\n" + j.format_page("index") + "\n")
            return True
        if p == "future":
            print("\n" + j.format_page("future") + "\n")
            return True
        if p == "month":
            print("\n" + j.format_page("monthly") + "\n")
            return True
        if p.startswith("collection "):
            name = p[11:].strip()
            j.collection_get(name) or j.collection_create(name)
            print("\n" + j.format_page("collection", name) + "\n")
            return True
        if p.startswith("migrate"):
            parts = p.split()
            if len(parts) >= 3:
                r = j.migrate_month(parts[1], parts[2])
            else:
                mk = _month_key()
                y, m = map(int, mk.split("-"))
                nm = f"{y:04d}-{m+1:02d}" if m < 12 else f"{y+1:04d}-01"
                r = j.migrate_month(mk, nm)
            print(f"\nMigration complete: {r}\n")
            return True
        if p.startswith("reflect"):
            print("\n" + j.ai_reflect("week") + "\n")
            return True
        if p.startswith("search "):
            hits = j.search(p[7:])
            for h in hits:
                print(f"  [{h.get('section')}] {_format_bullet(h)}")
            print()
            return True

        print("\nBuJo commands: log, today, index, future, month, collection <name>, migrate, reflect, search\n")
        return True


def main():
    print("\nJarvis Bullet Journal")
    print("Symbols: • task  × done  > migrated  ○ event  — note  * important\n")
    engine = JournalEngine()
    while True:
        try:
            if not engine.handle(input("Journal > ")):
                break
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
