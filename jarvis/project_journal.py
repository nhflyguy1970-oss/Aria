"""Per-project daily journals — separate daily logs scoped to a project."""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from pathlib import Path

from jarvis.config import JOURNAL_DIR
from jarvis.modules.journal import BULLET_TYPES, SYMBOLS, _format_bullet, _new_bullet, _today

PROJECTS_DIR = JOURNAL_DIR / "projects"
INDEX_FILE = PROJECTS_DIR / "index.json"


def _slugify(name: str) -> str:
    s = re.sub(r"[^\w\s-]", "", (name or "").lower())
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return (s[:48] or "project")


def _project_path(slug: str) -> Path:
    return PROJECTS_DIR / f"{_slugify(slug)}.json"


def list_projects() -> list[dict]:
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    meta: dict[str, dict] = {}
    if INDEX_FILE.is_file():
        try:
            data = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
            for item in data.get("projects") or []:
                if isinstance(item, dict) and item.get("slug"):
                    meta[item["slug"]] = item
        except (json.JSONDecodeError, OSError):
            pass
    slugs: set[str] = set(meta.keys())
    for path in PROJECTS_DIR.glob("*.json"):
        if path.name == "index.json":
            continue
        slugs.add(path.stem)
    out: list[dict] = []
    for slug in sorted(slugs):
        info = meta.get(slug, {})
        store = ProjectJournal(slug)
        out.append({
            "slug": slug,
            "title": info.get("title") or store.data.get("title") or slug,
            "days": len(store.data.get("daily_log") or {}),
            "updated": info.get("updated") or store.data.get("updated"),
        })
    return out


def _update_index(slug: str, *, title: str = "") -> None:
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    projects = {p["slug"]: p for p in list_projects()}
    entry = projects.get(slug, {"slug": slug, "title": title or slug})
    if title:
        entry["title"] = title
    entry["updated"] = datetime.now(timezone.utc).isoformat()
    projects[slug] = entry
    INDEX_FILE.write_text(
        json.dumps({"projects": list(projects.values())}, indent=2),
        encoding="utf-8",
    )


class ProjectJournal:
    """Daily journal for one project."""

    def __init__(self, slug: str):
        self.slug = _slugify(slug)
        self.path = _project_path(self.slug)
        PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _empty(self) -> dict:
        return {
            "version": 1,
            "project": self.slug,
            "title": self.slug,
            "daily_log": {},
            "updated": datetime.now(timezone.utc).isoformat(),
        }

    def _load(self) -> dict:
        if self.path.is_file():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    data.setdefault("daily_log", {})
                    data.setdefault("project", self.slug)
                    return data
            except (json.JSONDecodeError, OSError):
                pass
        return self._empty()

    def _save(self) -> None:
        self.data["updated"] = datetime.now(timezone.utc).isoformat()
        from jarvis.live_data_guard import assert_live_write_allowed

        assert_live_write_allowed(self.path)
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
        _update_index(self.slug, title=self.data.get("title") or self.slug)

    def ensure(self, *, title: str = "") -> dict:
        if title:
            self.data["title"] = title.strip()
        if not self.path.is_file():
            self._save()
        return self.data

    def _ensure_daily(self, day: str) -> dict:
        dl = self.data.setdefault("daily_log", {})
        if day not in dl:
            d = date.fromisoformat(day)
            dl[day] = {
                "date": day,
                "title": d.strftime("%A, %B %d, %Y"),
                "bullets": [],
                "notes": "",
                "learned_at": "",
            }
        return dl[day]

    def daily_add(
        self,
        content: str,
        *,
        bullet_type: str = "note",
        day: str | None = None,
        signifiers: list[str] | None = None,
    ) -> dict:
        d = day or _today()
        page = self._ensure_daily(d)
        loc = f"project:{self.slug}:daily:{d}"
        bullet = _new_bullet(
            content,
            bullet_type if bullet_type in BULLET_TYPES else "note",
            signifiers=signifiers,
            location=loc,
        )
        page["bullets"].append(bullet)
        self._save()
        return bullet

    def daily_set_notes(self, notes: str, *, day: str | None = None) -> dict:
        page = self._ensure_daily(day or _today())
        page["notes"] = (notes or "").strip()
        self._save()
        return page

    def daily_get(self, day: str | None = None) -> dict:
        return self._ensure_daily(day or _today())

    def daily_mark_learned(self, day: str) -> None:
        page = self._ensure_daily(day)
        page["learned_at"] = datetime.now(timezone.utc).isoformat()
        self._save()

    def format_daily(self, day: str | None = None) -> str:
        page = self.daily_get(day)
        d = page.get("date", day or _today())
        title = page.get("title") or d
        lines = [f"**{self.data.get('title') or self.slug}** — {title}", ""]
        bullets = page.get("bullets") or []
        if bullets:
            lines.append("**Log**")
            lines.extend(_format_bullet(b) for b in bullets)
        notes = (page.get("notes") or "").strip()
        if notes:
            lines.extend(["", "**Notes**", notes])
        if not bullets and not notes:
            lines.append("_No entries yet — log something for this project._")
        return "\n".join(lines)

    def page_text(self, day: str | None = None) -> str:
        page = self.daily_get(day)
        d = page.get("date", day or _today())
        parts = [f"Project journal ({self.slug}) — {d}"]
        for b in page.get("bullets") or []:
            parts.append(_format_bullet(b))
        notes = (page.get("notes") or "").strip()
        if notes:
            parts.append(f"Notes: {notes}")
        return "\n".join(parts)

    def recent_days(self, *, limit: int = 7) -> list[str]:
        days = sorted((self.data.get("daily_log") or {}).keys(), reverse=True)
        return days[:limit]

    def search(self, query: str, *, limit: int = 20) -> list[dict]:
        q = (query or "").lower().strip()
        if not q:
            return []
        hits: list[dict] = []
        for day, page in sorted((self.data.get("daily_log") or {}).items(), reverse=True):
            for b in page.get("bullets") or []:
                text = (b.get("content") or "").lower()
                if q in text:
                    hits.append({**b, "day": day, "section": f"project:{self.slug}:{day}"})
                    if len(hits) >= limit:
                        return hits
            if q in (page.get("notes") or "").lower():
                hits.append({
                    "id": f"notes-{day}",
                    "content": page.get("notes", ""),
                    "day": day,
                    "section": f"project:{self.slug}:{day}",
                    "type": "note",
                })
        return hits[:limit]


def resolve_project(
    message: str = "",
    *,
    explicit: str = "",
    session_namespace: str = "",
) -> str:
    """Pick project slug from params, message, or session."""
    if explicit:
        return _slugify(explicit)
    text = (message or "").strip()
    patterns = (
        r"\bproject journal(?:\s+for)?\s+([\w-]+)",
        r"\b([\w-]+)\s+project journal\b",
        r"\blog to\s+([\w-]+)\s+(?:project\s+)?journal\b",
        r"\blearn from\s+([\w-]+)\s+(?:project\s+)?journal\b",
        r"\bfor project\s+([\w-]+)\b",
    )
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            return _slugify(m.group(1))
    if session_namespace and session_namespace not in ("default", "journal", "learned", "observed", "corrections"):
        return _slugify(session_namespace)
    try:
        from jarvis.memory_context import detect_project_namespace

        return detect_project_namespace()
    except Exception:
        return "default"


def parse_project_log_text(message: str) -> str:
    text = (message or "").strip()
    for pat in (
        r"^log to (?:the )?[\w-]+ (?:project )?journal[:\s]+(.+)$",
        r"^project journal[:\s]+(.+)$",
        r"^project log[:\s]+(.+)$",
    ):
        m = re.match(pat, text, re.I | re.S)
        if m:
            return m.group(1).strip()
    m = re.search(r"\bproject journal[:\s]+(.+)$", text, re.I | re.S)
    return m.group(1).strip() if m else ""
