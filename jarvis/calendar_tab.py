# Source Generated with Decompyle++
# File: calendar_tab.cpython-312.pyc (Python 3.12)

'''Calendar tab — merge journal, holidays, ICS, and work schedule.'''
from __future__ import annotations
from datetime import date
from typing import Any
from jarvis.calendar_ics import fetch_events_for_day, fetch_events_for_month, ics_url
from jarvis.calendar_store import load_work_schedule, work_blocks_for_day

def month_overview(journal = None, month = None):
    _month_key = _month_key
    import jarvis.modules.journal
    if not month:
        month
    mk = _month_key()
    cal = journal.monthly_calendar(mk)
    ics_by_day = fetch_events_for_month(mk)
    if ics_by_day:
        if not cal.get('events'):
            cal.get('events')
        merged = dict({ })
        for day_str, items in ics_by_day.items():
            for item in items:
                if not item.get('time'):
                    item.get('time')
                if not item.get('summary'):
                    item.get('summary')
                merged.setdefault(day_str, []).append({
                    'time': '',
                    'content': '',
                    'source': 'ics' })
        cal['events'] = merged
        cal['ics_events'] = ics_by_day
    cal['ics_url'] = ics_url()
    cal['work_schedule'] = load_work_schedule()
    return cal


def day_detail(journal = None, day = None):
    d = date.fromisoformat(day)
    mk = day[:7]
    monthly = journal.monthly_calendar(mk)
    day_num = str(d.day)
    if not monthly.get('calendar_notes'):
        monthly.get('calendar_notes')
    note = { }.get(day_num, '')
    if not monthly.get('holidays'):
        monthly.get('holidays')
    holidays = { }.get(day, [])
    page = journal.daily_get(day, enrich = False)
    timeline = journal.daily_timeline(day)
    ics = fetch_events_for_day(d)
    work = work_blocks_for_day(d)
    if not page.get('bullets'):
        page.get('bullets')
    bullets = []
    appointments = []
    tasks = []
    for b in bullets:
        item = {
            'id': b.get('id'),
            'type': b.get('type'),
            'content': b.get('content', ''),
            'time': b.get('time'),
            'status': b.get('status') }
        if b.get('type') == 'event':
            appointments.append(item)
            continue
        if not b.get('type') == 'task':
            continue
        tasks.append(item)
    if not timeline.get('events'):
        timeline.get('events')
    return {
        'ok': True,
        'day': day,
        'title': page.get('title', day),
        'holidays': holidays,
        'calendar_note': note,
        'work_blocks': work,
        'ics_events': ics,
        'journal_events': [],
        'appointments': appointments,
        'tasks': tasks,
        'ics_url': ics_url() }

