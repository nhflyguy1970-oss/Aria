# Source Generated with Decompyle++
# File: planner_store.cpython-312.pyc (Python 3.12)

'''SQLite planner — life tasks, calendar events, timers, alarms.'''
from __future__ import annotations
import re
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Any
from jarvis.config import DATA_DIR
from jarvis.feature_flags import planner_enabled
DB_PATH = DATA_DIR / 'planner.db'

def _conn():
    DATA_DIR.mkdir(parents = True, exist_ok = True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    conn = _conn()
    conn.executescript('\n            CREATE TABLE IF NOT EXISTS tasks (\n                id TEXT PRIMARY KEY,\n                text TEXT NOT NULL,\n                completed INTEGER DEFAULT 0,\n                created_at TEXT NOT NULL\n            );\n            CREATE TABLE IF NOT EXISTS events (\n                id TEXT PRIMARY KEY,\n                title TEXT NOT NULL,\n                start_time TEXT NOT NULL,\n                end_time TEXT,\n                description TEXT,\n                created_at TEXT NOT NULL\n            );\n            CREATE TABLE IF NOT EXISTS timers (\n                id TEXT PRIMARY KEY,\n                label TEXT,\n                ends_at TEXT NOT NULL,\n                created_at TEXT NOT NULL\n            );\n            CREATE TABLE IF NOT EXISTS alarms (\n                id TEXT PRIMARY KEY,\n                label TEXT,\n                fire_at TEXT NOT NULL,\n                enabled INTEGER DEFAULT 1,\n                fired INTEGER DEFAULT 0,\n                created_at TEXT NOT NULL\n            );\n            ')
    None(None, None)
    return None
    with None:
        if not None:
            pass

_init_db()

def _now_iso():
    return datetime.now().isoformat(timespec = 'seconds')


def _parse_duration(text = None):
    """Return seconds from '10 minutes', '1h', etc."""
    if not text:
        text
    t = ''.lower().strip()
    if not t:
        return None
    total = 0
    for num, unit in re.findall('(\\d+)\\s*(h|hr|hrs|hour|hours|m|min|mins|minute|minutes|s|sec|secs|second|seconds)', t):
        n = int(num)
        if unit.startswith('h'):
            total += n * 3600
            continue
        if unit.startswith('m'):
            total += n * 60
            continue
        total += n
    if total:
        return total
    if None.isdigit():
        return int(t) * 60


def _parse_time_today(text = None, *, base):
    '''Parse 7am, 14:30, 3:30 pm for today (or tomorrow if past).'''
    if not text:
        text
    t = ''.lower().strip()
    if not t:
        return None
    if not base:
        base
    ref = datetime.now()
    m = re.match('^(\\d{1,2})(?::(\\d{2}))?\\s*(am|pm)?$', t.replace('.', ''))
    if not m:
        return None
    hour = int(m.group(1))
    if not m.group(2):
        m.group(2)
    minute = int(0)
    ampm = m.group(3)
    if ampm == 'pm' and hour < 12:
        hour += 12
    if ampm == 'am' and hour == 12:
        hour = 0
    if ampm and hour < 24 and ':' in t:
        pass
    elif ampm and hour <= 12:
        hour = hour if hour >= 7 else hour + 12
    dt = ref.replace(hour = hour, minute = minute, second = 0, microsecond = 0)
# WARNING: Decompyle incomplete


def add_task(text = None):
    if not planner_enabled():
        raise ValueError('Planner is disabled (JARVIS_PLANNER=0).')
    if not text:
        text
    text = ''.strip()
    if not text:
        raise ValueError('Task text required')
    tid = uuid.uuid4().hex[:10]
    created = _now_iso()
    conn = _conn()
    conn.execute('INSERT INTO tasks (id, text, completed, created_at) VALUES (?, ?, 0, ?)', (tid, text, created))
    None(None, None)
    return {
        'id': tid,
        'text': text,
        'completed': False,
        'created_at': created }
    with None:
        if not None:
            pass
    continue


def list_tasks(*, include_completed):
    conn = _conn()
    if include_completed:
        rows = conn.execute('SELECT * FROM tasks ORDER BY created_at ASC').fetchall()
    else:
        rows = conn.execute('SELECT * FROM tasks WHERE completed = 0 ORDER BY created_at ASC').fetchall()
    None(None, None)
# WARNING: Decompyle incomplete


def complete_task(task_id = None):
    conn = _conn()
    cur = conn.execute('UPDATE tasks SET completed = 1 WHERE id = ?', (task_id,))
    if cur.rowcount > 0:
        None(None, None)
        return True
    cur = conn.execute('UPDATE tasks SET completed = 1 WHERE text = ? AND completed = 0', (task_id,))
    None(None, None)
    return 
    with None:
        if not None, cur.rowcount > 0:
            pass


def add_event(title = None, *, when, time_str, duration_min):
    if not title:
        title
    title = ''.strip()
    if not title:
        raise ValueError('Event title required')
    start = datetime.now()
    if when:
        w = when.lower().strip()
        if w == 'tomorrow':
            start = start + timedelta(days = 1)
        elif re.match('\\d{4}-\\d{2}-\\d{2}', w):
            start = datetime.fromisoformat(w)
    if time_str:
        parsed = _parse_time_today(time_str, base = start if when else None)
        if parsed:
            start = parsed
    end = start + timedelta(minutes = max(15, duration_min))
    eid = uuid.uuid4().hex[:10]
    created = _now_iso()
    conn = _conn()
    conn.execute("INSERT INTO events (id, title, start_time, end_time, description, created_at) VALUES (?, ?, ?, ?, '', ?)", (eid, title, start.isoformat(timespec = 'seconds'), end.isoformat(timespec = 'seconds'), created))
    None(None, None)
    return {
        'id': eid,
        'title': title,
        'start_time': start.isoformat(timespec = 'seconds'),
        'end_time': end.isoformat(timespec = 'seconds') }
    with None:
        if not None:
            pass
    continue


def events_for_day(day = None):
    date_type = date
    import datetime
    if not day:
        day
    day = datetime.now().date().isoformat()
    conn = _conn()
    rows = conn.execute('SELECT * FROM events WHERE substr(start_time, 1, 10) = ? ORDER BY start_time', (day,)).fetchall()
    None(None, None)
# WARNING: Decompyle incomplete


def set_timer(duration = None, label = None):
    secs = _parse_duration(duration)
    if secs or secs < 1:
        raise ValueError(f'''Could not parse duration: {duration}''')
    ends = datetime.now() + timedelta(seconds = secs)
    tid = uuid.uuid4().hex[:10]
    created = _now_iso()
    if not label:
        label
    lbl = duration.strip()
    conn = _conn()
    conn.execute('INSERT INTO timers (id, label, ends_at, created_at) VALUES (?, ?, ?, ?)', (tid, lbl, ends.isoformat(timespec = 'seconds'), created))
    None(None, None)
    return {
        'id': tid,
        'label': lbl,
        'ends_at': ends.isoformat(timespec = 'seconds'),
        'remaining_seconds': secs }
    with None:
        if not None:
            pass
    continue


def active_timers():
    now = datetime.now()
    conn = _conn()
    rows = conn.execute('SELECT * FROM timers ORDER BY ends_at').fetchall()
    None(None, None)
    out = []
# WARNING: Decompyle incomplete


def clear_expired_timers():
    now = _now_iso()
    conn = _conn()
    cur = conn.execute('DELETE FROM timers WHERE ends_at <= ?', (now,))
    None(None, None)
    return 
    with None:
        if not None, cur.rowcount:
            pass


def set_alarm(time_str = None, label = None):
    fire = _parse_time_today(time_str)
    if not fire:
        raise ValueError(f'''Could not parse alarm time: {time_str}''')
    aid = uuid.uuid4().hex[:10]
    created = _now_iso()
    if not label:
        label
    lbl = f'''Alarm {time_str}'''.strip()
    conn = _conn()
    conn.execute('INSERT INTO alarms (id, label, fire_at, enabled, fired, created_at) VALUES (?, ?, ?, 1, 0, ?)', (aid, lbl, fire.isoformat(timespec = 'seconds'), created))
    None(None, None)
    return {
        'id': aid,
        'label': lbl,
        'fire_at': fire.isoformat(timespec = 'seconds') }
    with None:
        if not None:
            pass
    continue


def list_alarms(*, include_fired):
    conn = _conn()
    if include_fired:
        rows = conn.execute('SELECT * FROM alarms WHERE enabled = 1 ORDER BY fire_at').fetchall()
    else:
        rows = conn.execute('SELECT * FROM alarms WHERE enabled = 1 AND fired = 0 ORDER BY fire_at').fetchall()
    None(None, None)
# WARNING: Decompyle incomplete


def tick_alarms_and_timers():
    '''Return notifications for expired timers / due alarms; mark fired.'''
    notes = []
    conn = _conn()
    for row in conn.execute('SELECT * FROM timers WHERE ends_at <= ?', (_now_iso(),)).fetchall():
        if not row['label']:
            row['label']
        notes.append({
            'type': 'timer',
            'message': f'''Timer done: {'timer'}''' })
        conn.execute('DELETE FROM timers WHERE id = ?', (row['id'],))
    for row in conn.execute('SELECT * FROM alarms WHERE enabled = 1 AND fired = 0 AND fire_at <= ?', (_now_iso(),)).fetchall():
        if not row['label']:
            row['label']
        notes.append({
            'type': 'alarm',
            'message': f'''Alarm: {'alarm'}''' })
        conn.execute('UPDATE alarms SET fired = 1 WHERE id = ?', (row['id'],))
    None(None, None)
    return notes
    with None:
        if not None:
            pass
    return notes


def planner_snapshot():
    if not planner_enabled():
        return {
            'enabled': False }
    return {
        'enabled': None,
        'tasks': list_tasks(),
        'events_today': events_for_day(),
        'timers': active_timers(),
        'alarms': list_alarms() }


def format_planner_lines():
    snap = planner_snapshot()
    if not snap.get('enabled'):
        return ''
    parts = []
    if not snap.get('tasks'):
        snap.get('tasks')
    tasks = []
# WARNING: Decompyle incomplete

