"""Daily auto-create and update for project journals."""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from jarvis.config import PROJECT_ROOT
from jarvis.modules.journal import _today
from jarvis.project_journal import PROJECTS_DIR, ProjectJournal, list_projects, resolve_project

log = logging.getLogger("jarvis.project_journal_daily")

STATE_FILE = PROJECTS_DIR / "_daily_state.json"


def daily_enabled() -> bool:
    return os.getenv("JARVIS_PROJECT_JOURNAL_DAILY", "1").lower() not in ("0", "false", "off", "no")


def morning_hour() -> int:
    try:
        return int(os.getenv("JARVIS_PROJECT_JOURNAL_MORNING_HOUR", "8"))
    except ValueError:
        return 8


def evening_hour() -> int:
    try:
        return int(os.getenv("JARVIS_PROJECT_JOURNAL_EVENING_HOUR", "21"))
    except ValueError:
        return 21


def auto_learn_after_evening() -> bool:
    return os.getenv("JARVIS_PROJECT_JOURNAL_AUTO_LEARN", "").lower() in ("1", "true", "yes")


def _load_state() -> dict[str, Any]:
    if not STATE_FILE.is_file():
        return {"days": {}}
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("days", {})
            return data
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("Corrupt project journal daily state: %s", exc)
    return {"days": {}}


def _save_state(data: dict[str, Any]) -> None:
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    from jarvis.live_data_guard import assert_live_write_allowed

    assert_live_write_allowed(STATE_FILE)
    STATE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _day_state(day: str) -> dict[str, dict[str, str]]:
    data = _load_state()
    days = data.setdefault("days", {})
    if day not in days:
        days[day] = {}
    return days[day]


def _mark_ran(slug: str, day: str, phase: str) -> None:
    data = _load_state()
    day_map = data.setdefault("days", {}).setdefault(day, {})
    day_map[slug] = day_map.get(slug) or {}
    if isinstance(day_map[slug], str):
        day_map[slug] = {"legacy": day_map[slug]}
    day_map[slug][phase] = datetime.now(timezone.utc).isoformat()
    _save_state(data)


def _already_ran(slug: str, day: str, phase: str) -> bool:
    data = _load_state()
    entry = data.get("days", {}).get(day, {}).get(slug)
    if not entry:
        return False
    if isinstance(entry, str):
        return True
    return bool(entry.get(phase))


def discover_project_slugs() -> list[str]:
    slugs: set[str] = set()
    env = os.getenv("JARVIS_PROJECT_JOURNAL_PROJECTS", "").strip()
    if env:
        slugs.update(s.strip() for s in env.split(",") if s.strip())
    try:
        slugs.add(resolve_project(session_namespace=""))
    except Exception:
        pass
    for p in list_projects():
        slugs.add(p["slug"])
    return sorted(s for s in slugs if s and s != "default")


def _git_repo_root() -> Path | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(PROJECT_ROOT), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode == 0:
            return Path(proc.stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        pass
    return PROJECT_ROOT if (PROJECT_ROOT / ".git").exists() else None


def _git_activity(day: str, *, root: Path | None = None) -> str:
    repo = root or _git_repo_root()
    if not repo:
        return ""
    since = f"{day} 00:00:00"
    lines: list[str] = []
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "log", f"--since={since}", "--oneline", "-20"],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            lines.append("Git commits today:\n" + proc.stdout.strip())
        proc = subprocess.run(
            ["git", "-C", str(repo), "status", "-sb"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            lines.append("Git status:\n" + proc.stdout.strip())
    except (OSError, subprocess.TimeoutExpired) as exc:
        log.debug("Git activity skipped: %s", exc)
    return "\n\n".join(lines)


def _actions_today(day: str | None = None) -> list[dict]:
    from jarvis.action_log import _load

    d = day or _today()
    rows = []
    for row in reversed(_load()):
        ts = (row.get("time") or "")[:10]
        if ts != d:
            continue
        rows.append(row)
        if len(rows) >= 40:
            break
    return list(reversed(rows))


def _format_actions(rows: list[dict]) -> str:
    if not rows:
        return ""
    lines = ["ARIA activity today:"]
    for r in rows:
        action = r.get("action") or r.get("event") or "event"
        mod = r.get("module") or ""
        detail = (r.get("detail") or "")[:120]
        ok = r.get("ok", True)
        status = "" if ok else " [failed]"
        lines.append(f"- [{mod}] {action}{status}: {detail}".strip())
    return "\n".join(lines)


def gather_daily_context(slug: str, day: str | None = None) -> str:
    d = day or _today()
    parts = [f"Project: {slug}", f"Date: {d}"]
    git = _git_activity(d)
    if git:
        parts.append(git)
    actions = _format_actions(_actions_today(d))
    if actions:
        parts.append(actions)
    try:
        from jarvis.coding_tasks import TaskManager

        tasks = TaskManager().list_open()[:8]
        if tasks:
            lines = ["Open coding tasks:"]
            for t in tasks:
                lines.append(f"- {t.get('title') or t.get('description') or t}")
            parts.append("\n".join(lines))
    except Exception:
        pass
    return "\n\n".join(parts)


def _rule_based_summary(context: str, *, phase: str, slug: str) -> tuple[list[str], str]:
    bullets: list[str] = []
    notes = ""
    if phase == "morning":
        bullets.append(f"Daily project journal opened for {slug}.")
        if "Git status" in context:
            first_line = ""
            for line in context.splitlines():
                if line.strip() and not line.startswith("Project:") and not line.startswith("Date:"):
                    first_line = line.strip()[:160]
                    break
            if first_line:
                bullets.append(f"Starting point: {first_line}")
    else:
        if "Git commits today" in context:
            m = re.search(r"Git commits today:\n(.+)", context, re.S)
            if m:
                commits = [ln.strip() for ln in m.group(1).splitlines() if ln.strip()][:5]
                if commits:
                    bullets.append(f"Commits today: {len(commits)} ({commits[0][:80]}…)" if len(commits[0]) > 80 else f"Commits today: {len(commits)} — {commits[0]}")
        actions = _actions_today()
        if actions:
            bullets.append(f"ARIA handled {len(actions)} action(s) today.")
        notes = "End-of-day auto summary by ARIA."
    return bullets, notes


def _llm_summary(context: str, *, phase: str, slug: str) -> tuple[list[str], str] | None:
    from jarvis import llm

    label = "morning kickoff" if phase == "morning" else "evening wrap-up"
    prompt = (
        f"Write a short {label} for the **{slug}** project daily journal. "
        "Return JSON only: {\"bullets\": [\"bullet1\", \"bullet2\"], \"notes\": \"optional paragraph\"}. "
        "2-4 concise bullets about status, progress, blockers, or next steps. "
        "Use facts from the context only.\n\n"
        f"{context[:8000]}"
    )
    try:
        raw = llm.ask(llm.general_model(), [{"role": "user", "content": prompt}])
        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```\w*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        data = json.loads(raw)
        bullets = [str(b).strip() for b in data.get("bullets", []) if str(b).strip()]
        notes = (data.get("notes") or "").strip()
        if bullets:
            return bullets[:6], notes[:1200]
    except Exception as exc:
        log.debug("LLM project journal summary failed: %s", exc)
    return None


def _apply_auto_section(
    journal: ProjectJournal,
    day: str,
    *,
    phase: str,
    bullets: list[str],
    notes: str = "",
) -> None:
    page = journal.daily_get(day)
    auto = page.setdefault("auto", {})
    prefix = "Morning" if phase == "morning" else "Evening"
    stamped = [f"[{prefix}] {b}" if not b.startswith("[") else b for b in bullets if b.strip()]
    auto[phase] = {
        "bullets": stamped,
        "notes": notes.strip(),
        "at": datetime.now(timezone.utc).isoformat(),
    }
    for text in stamped:
        if not any((b.get("content") or "") == text for b in page.get("bullets") or []):
            journal.daily_add(text, bullet_type="note", day=day)
    if notes and phase == "evening":
        existing = (page.get("notes") or "").strip()
        block = f"{prefix} summary: {notes}"
        page["notes"] = f"{existing}\n\n{block}".strip() if existing else block
    journal._save()


def update_project_journal_daily(
    slug: str,
    *,
    day: str | None = None,
    phase: str = "morning",
    force: bool = False,
    memory=None,
) -> dict[str, Any]:
    """Create or update today's project journal page for a phase."""
    if not daily_enabled() and not force:
        return {"ok": False, "slug": slug, "message": "Daily project journals disabled."}

    d = day or _today()
    journal = ProjectJournal(slug)
    journal.ensure(title=slug)

    if not force and _already_ran(slug, d, phase):
        return {"ok": True, "slug": slug, "phase": phase, "skipped": True, "message": "Already updated."}

    context = gather_daily_context(slug, d)
    summary = _llm_summary(context, phase=phase, slug=slug)
    if not summary:
        summary = _rule_based_summary(context, phase=phase, slug=slug)
    bullets, notes = summary

    _apply_auto_section(journal, d, phase=phase, bullets=bullets, notes=notes)
    _mark_ran(slug, d, phase)

    learned = 0
    if phase == "evening" and auto_learn_after_evening() and memory is not None:
        try:
            from jarvis.journal_learning import learn_from_project_journal

            lr = learn_from_project_journal(memory, slug, day=d, namespace=slug)
            if lr.get("ok"):
                learned = len(lr.get("facts") or [])
        except Exception as exc:
            log.debug("Auto-learn project journal skipped: %s", exc)

    return {
        "ok": True,
        "slug": slug,
        "day": d,
        "phase": phase,
        "bullets": bullets,
        "learned": learned,
        "message": f"Updated **{slug}** project journal ({phase}).",
    }


def update_all_project_journals(
    *,
    phase: str = "morning",
    force: bool = False,
    memory=None,
) -> list[dict[str, Any]]:
    results = []
    for slug in discover_project_slugs():
        try:
            results.append(update_project_journal_daily(slug, phase=phase, force=force, memory=memory))
        except Exception as exc:
            log.warning("Project journal daily failed for %s: %s", slug, exc)
            results.append({"ok": False, "slug": slug, "message": str(exc)})
    return results


def run_scheduled_daily(now: datetime | None = None, *, memory=None) -> list[dict[str, Any]]:
    """Run morning/evening updates when the clock hits configured hours."""
    if not daily_enabled():
        return []
    now = now or datetime.now()
    results: list[dict[str, Any]] = []
    if now.hour == morning_hour() and now.minute < 10:
        results.extend(update_all_project_journals(phase="morning", memory=memory))
    if now.hour == evening_hour() and now.minute < 10:
        results.extend(update_all_project_journals(phase="evening", memory=memory))
    return results


def run_startup_daily(*, memory=None) -> list[dict[str, Any]]:
    """On server start: ensure today's journals exist (morning); evening if past evening hour."""
    if not daily_enabled():
        return []
    now = datetime.now()
    results: list[dict[str, Any]] = []
    results.extend(update_all_project_journals(phase="morning", memory=memory))
    if now.hour >= evening_hour():
        results.extend(update_all_project_journals(phase="evening", memory=memory))
    return results
