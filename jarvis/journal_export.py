"""Journal PDF and print-friendly HTML export — notebook-style layout."""

from __future__ import annotations

import calendar as cal_mod
import html
from datetime import date, timedelta
from pathlib import Path

from jarvis.config import JOURNAL_DIR
from jarvis.modules.journal import BulletJournal, _format_bullet, _month_key, _week_key

WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def _weeks_in_month(mk: str) -> list[str]:
    y, m = map(int, mk.split("-"))
    first = date(y, m, 1)
    last = date(y, m, cal_mod.monthrange(y, m)[1])
    weeks: list[str] = []
    seen: set[str] = set()
    d = first
    while d <= last:
        wk = _week_key(d)
        if wk not in seen:
            seen.add(wk)
            weeks.append(wk)
        d += timedelta(days=1)
    return weeks


def _bullet_status_class(b: dict) -> str:
    s = b.get("status", "open")
    if s in ("done", "cancelled", "migrated"):
        return f' class="status-{s}"'
    return ""


def _bullets_html(bullets: list, symbols: dict | None = None) -> str:
    if not bullets:
        return "<p class='empty'>—</p>"

    def render_list(items: list, nested: bool = False) -> str:
        cls = "nested" if nested else ""
        parts = [f"<ul class='bullets {cls}'>"]
        for b in items:
            text = html.escape(_format_bullet(b, symbols).split("\n")[0])
            parts.append(f"<li{_bullet_status_class(b)}>{text}</li>")
            if b.get("children"):
                parts.append(render_list(b["children"], nested=True))
        parts.append("</ul>")
        return "".join(parts)

    return render_list(bullets)


def _key_html(journal: BulletJournal) -> str:
    key = journal.get_key()
    syms = key.get("symbols", {})
    rows = (
        ("task", "Task"),
        ("task_done", "Done"),
        ("task_migrated", "Migrated"),
        ("task_scheduled", "Scheduled"),
        ("task_cancelled", "Cancelled"),
        ("event", "Event"),
        ("note", "Note"),
        ("important", "Important"),
        ("inspiration", "Inspiration"),
        ("explore", "Explore"),
    )
    cells = "".join(
        f"<span><strong>{html.escape(syms.get(k, k))}</strong> {html.escape(label)}</span>"
        for k, label in rows
        if k in syms or k.startswith("task_")
    )
    desc = html.escape(key.get("description", ""))
    return f"<div class='key-grid'>{cells}</div><p class='key-desc'>{desc}</p>"


def _review_list_html(checklist: list | tuple, review: dict) -> str:
    items = "".join(
        f"<li>{'☑' if review.get(item['id']) else '☐'} {html.escape(item['label'])}</li>"
        for item in checklist
    )
    return items or "<li class='empty'>No checklist</li>"


def _calendar_html(cal: dict) -> str:
    weeks = cal.get("weeks") or []
    notes = cal.get("calendar_notes") or {}
    days = cal.get("days") or {}
    events = cal.get("events") or {}
    holidays = cal.get("holidays") or {}
    mk = cal.get("month", "")
    parts = [
        "<table class='cal-grid'><thead><tr>",
        *[f"<th>{d}</th>" for d in WEEKDAYS],
        "</tr></thead><tbody>",
    ]
    for week in weeks:
        parts.append("<tr>")
        for day_num in week:
            if not day_num:
                parts.append("<td class='cal-empty'></td>")
                continue
            info = days.get(str(day_num), {})
            date_str = info.get("date", f"{mk}-{int(day_num):02d}")
            note = notes.get(str(day_num), "")
            evts = events.get(date_str, [])
            hols = holidays.get(date_str, [])
            evt_txt = "; ".join(
                f"{e.get('time', '')} {e.get('content', '')}".strip() for e in evts[:2]
            )
            hol_txt = "; ".join(h.get("name", "") for h in hols[:2])
            cell = f"<span class='cal-num'>{day_num}</span>"
            if hol_txt:
                cell += f"<br><span class='cal-holiday'>{html.escape(hol_txt[:40])}</span>"
            if note:
                cell += f"<br><span class='cal-note'>{html.escape(note[:36])}</span>"
            if evt_txt:
                cell += f"<br><span class='cal-event'>{html.escape(evt_txt[:48])}</span>"
            if info.get("count"):
                cell += f"<br><span class='cal-dots'>{info['count']} entries</span>"
            parts.append(f"<td>{cell}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)


def _habits_html(journal: BulletJournal, mk: str) -> str:
    tracker = journal.habit_tracker(mk)
    days = tracker.get("days") or []
    habits = tracker.get("habits") or []
    if not habits:
        return "<p class='empty'>—</p>"
    head = "<th>Habit</th>" + "".join(
        f"<th>{int(d.split('-')[2])}</th>" for d in days
    )
    rows = []
    for h in habits:
        cells = "".join(
            f"<td>{'●' if h.get('days', {}).get(d) else '·'}</td>" for d in days
        )
        rows.append(
            f"<tr><td>{html.escape(h.get('name', ''))}</td>{cells}"
            f"<td class='habit-total'>{h.get('done_count', 0)}</td></tr>"
        )
    return (
        f"<table class='habit-grid'><thead><tr>{head}<th>Done</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def _future_html(journal: BulletJournal, symbols: dict | None) -> str:
    fl = journal.future_list()
    if not isinstance(fl, dict) or not fl:
        return "<p class='empty'>—</p>"
    parts: list[str] = []
    for fm in sorted(fl.keys()):
        bullets = fl[fm]
        if not bullets:
            continue
        parts.append(f"<h3>{html.escape(fm)}</h3>")
        parts.append(_bullets_html(bullets, symbols))
    return "".join(parts) if parts else "<p class='empty'>—</p>"


def _photos_html(photos: list, photo_url_prefix: str) -> str:
    if not photos:
        return ""
    figs = []
    for p in photos:
        fn = p.get("filename", "")
        if not fn:
            continue
        src = f"{photo_url_prefix}{html.escape(fn)}"
        cap = html.escape(p.get("caption") or "")
        figs.append(
            f"<figure class='photo'><img src='{src}' alt=''/>"
            f"<figcaption>{cap}</figcaption></figure>"
        )
    return f"<div class='photos'>{''.join(figs)}</div>" if figs else ""


def _wellness_html(day_page: dict) -> str:
    mood = day_page.get("mood")
    gratitude = day_page.get("gratitude") or []
    if not mood and not gratitude:
        return ""
    bits = []
    if mood:
        bits.append(f"Mood: {mood}/5")
    if gratitude:
        bits.append("Gratitude: " + "; ".join(html.escape(g) for g in gratitude[:6]))
    return f"<p class='wellness'>{' · '.join(bits)}</p>"


def _weekly_sections_html(journal: BulletJournal, mk: str, symbols: dict | None) -> str:
    from jarvis.modules.journal_bujo import WEEKLY_REVIEW_CHECKLIST

    parts: list[str] = []
    for wk in _weeks_in_month(mk):
        weekly = journal.weekly_get(wk)
        wreview = journal.weekly_review_get(wk)
        review = wreview.get("review") or {}
        items = _review_list_html(WEEKLY_REVIEW_CHECKLIST, review)
        pn = weekly.get("page_number")
        parts.append(
            f"<section class='weekly-block page-break'>"
            f"<h2>Weekly · {html.escape(wk)}"
            f"{f' <span class=pnum>p.{pn}</span>' if pn else ''}</h2>"
            f"{_bullets_html(weekly.get('bullets', []), symbols)}"
            f"<h3>Weekly review</h3>"
            f"<ul class='review-list'>{items}</ul>"
            f"<p>{html.escape(wreview.get('review_notes', ''))}</p>"
            f"</section>"
        )
    return "".join(parts) if parts else "<p class='empty'>No weekly pages this month.</p>"


def month_print_html(
    journal: BulletJournal,
    month: str | None = None,
    *,
    photo_url_prefix: str = "/api/journal/photos/",
) -> str:
    mk = month or _month_key()
    cal = journal.monthly_calendar(mk)
    page = journal.monthly_get(mk)
    symbols = journal.get_key().get("symbols")
    review = journal.monthly_review_get(mk)

    daily_sections = []
    prefix = f"{mk}-"
    for day_str in sorted(journal._data.get("daily_log", {})):
        if not day_str.startswith(prefix):
            continue
        day_page = journal.daily_get(day_str)
        pn = day_page.get("page_number")
        timeline = journal.daily_timeline(day_str)
        tlines = "".join(
            f"<li><time>{html.escape(e['time'])}</time> {html.escape(e['content'])}</li>"
            for e in timeline.get("events", [])
        )
        bullets = _bullets_html(day_page.get("bullets", []), symbols)
        enrich = ""
        w = day_page.get("weather") or {}
        if w.get("summary"):
            from jarvis.journal_weather import format_weather_line

            enrich += f"<p class='weather'><strong>Weather:</strong> {html.escape(format_weather_line(w))}</p>"
        q = day_page.get("quote") or {}
        if q.get("text"):
            enrich += (
                f"<blockquote>{html.escape(q['text'])}"
                f"<cite>{html.escape(q.get('author', ''))}</cite></blockquote>"
            )
        photos = _photos_html(day_page.get("photos") or [], photo_url_prefix)
        wellness = _wellness_html(day_page)
        daily_sections.append(
            f"<section class='daily-page page-break'>"
            f"<h3>{html.escape(day_page.get('title', day_str))}"
            f"{f' <span class=pnum>p.{pn}</span>' if pn else ''}</h3>"
            f"{enrich}{wellness}{photos}"
            f"{'<ul class=timeline>' + tlines + '</ul>' if tlines else ''}"
            f"{bullets}</section>"
        )

    review_items = _review_list_html(review.get("checklist", []), review.get("review", {}))

    css = """
    @page { margin: 0.75in; }
    body { font-family: 'Libre Baskerville', Georgia, serif; max-width: 7in; margin: 0 auto; color: #222; line-height: 1.45; }
    h1 { font-size: 1.6rem; border-bottom: 2px solid #333; padding-bottom: 0.25rem; }
    h2 { font-size: 1.1rem; margin-top: 1.25rem; text-transform: uppercase; letter-spacing: 0.06em; }
    h3 { font-size: 1rem; margin-top: 1rem; }
    .pnum { font-size: 0.75rem; color: #666; }
    .key-grid { display: flex; flex-wrap: wrap; gap: 0.5rem 1rem; font-size: 0.85rem; margin: 0.5rem 0; }
    .key-desc { font-size: 0.8rem; color: #555; }
    .bullets { list-style: none; padding-left: 0; margin: 0.35rem 0; }
    .bullets li { padding: 0.12rem 0; font-family: 'Courier New', monospace; font-size: 0.9rem; }
    .bullets li.status-done, .bullets li.status-cancelled, .bullets li.status-migrated {
      text-decoration: line-through; opacity: 0.72; color: #666;
    }
    .bullets.nested { margin-left: 1.25rem; border-left: 1px solid #ccc; padding-left: 0.65rem; }
    .timeline { list-style: none; padding: 0; margin: 0.35rem 0; font-size: 0.85rem; }
    .timeline time { font-weight: bold; margin-right: 0.35rem; }
    blockquote { margin: 0.35rem 0; padding-left: 0.75rem; border-left: 3px solid #999; font-style: italic; font-size: 0.85rem; }
    .wellness { font-size: 0.85rem; color: #444; margin: 0.35rem 0; }
    .photos { display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0.35rem 0; }
    .photo { margin: 0; max-width: 2.2in; }
    .photo img { max-width: 100%; border: 1px solid #ccc; border-radius: 4px; }
    .photo figcaption { font-size: 0.72rem; color: #555; }
    .cal-grid { width: 100%; border-collapse: collapse; font-size: 0.72rem; margin: 0.5rem 0; }
    .cal-grid th, .cal-grid td { border: 1px solid #ccc; padding: 0.25rem; vertical-align: top; width: 14%; }
    .cal-grid th { background: #f4f4f4; text-align: center; }
    .cal-num { font-weight: bold; }
    .cal-note, .cal-event, .cal-holiday, .cal-dots { display: block; font-size: 0.65rem; color: #555; }
    .cal-holiday { color: #8b4513; font-weight: 600; }
    .cal-event { color: #333; }
    .habit-grid { width: 100%; border-collapse: collapse; font-size: 0.62rem; margin: 0.5rem 0; }
    .habit-grid th, .habit-grid td { border: 1px solid #ccc; padding: 0.15rem; text-align: center; }
    .habit-grid th:first-child, .habit-grid td:first-child { text-align: left; min-width: 4.5rem; }
    .habit-total { font-weight: bold; }
    .page-break { page-break-before: always; }
    .review-list { font-size: 0.9rem; }
    .empty { color: #888; font-style: italic; }
    """

    body = f"""
    <header><h1>{html.escape(cal.get('title', mk))}</h1>
    <p class='pnum'>Monthly spread · {html.escape(mk)}</p></header>

    <section><h2>Symbol Key</h2>{_key_html(journal)}</section>

    <section><h2>Calendar</h2>{_calendar_html(cal)}</section>

    <section><h2>Monthly tasks</h2>{_bullets_html(page.get('bullets', []), symbols)}</section>

    <section><h2>Month-end review</h2>
    <ul class='review-list'>{review_items}</ul>
    <p>{html.escape(review.get('review_notes', ''))}</p></section>

    <section class='page-break'><h2>Future log</h2>{_future_html(journal, symbols)}</section>

    <section><h2>Habit tracker</h2>{_habits_html(journal, mk)}</section>

    {_weekly_sections_html(journal, mk, symbols)}

    <section class='page-break'><h2>Daily logs</h2></section>
    {''.join(daily_sections) or '<p class=empty>No daily pages this month.</p>'}
    """

    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<title>Journal {html.escape(mk)}</title>"
        f"<style>{css}</style></head><body>{body}</body></html>"
    )


def export_month_pdf(journal: BulletJournal, dest: Path, month: str | None = None) -> str:
    try:
        from weasyprint import HTML
    except ImportError:
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_pdf import PdfPages
        except ImportError as e:
            raise RuntimeError(
                "Install weasyprint for styled PDF export: pip install weasyprint "
                "(system: libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libgdk-pixbuf-2.0-0)"
            ) from e
        mk = month or _month_key()
        body = month_print_html(journal, mk, photo_url_prefix="photos/")
        import re
        text = re.sub(r"<[^>]+>", "", html.unescape(body))
        dest.parent.mkdir(parents=True, exist_ok=True)
        with PdfPages(dest) as pdf:
            chunk = 7500
            for i in range(0, len(text), chunk):
                fig, ax = plt.subplots(figsize=(8.5, 11))
                ax.text(0.08, 0.95, text[i : i + chunk], va="top", ha="left", fontsize=8, wrap=True)
                ax.axis("off")
                pdf.savefig(fig, bbox_inches="tight")
                plt.close(fig)
        return str(dest)

    mk = month or _month_key()
    html_doc = month_print_html(journal, mk, photo_url_prefix="photos/")
    dest.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html_doc, base_url=str(JOURNAL_DIR)).write_pdf(str(dest))
    return str(dest)
