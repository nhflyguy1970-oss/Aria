# Source Generated with Decompyle++
# File: project_journal_daily.cpython-312.pyc (Python 3.12)

'''Daily auto-create and update for project journals.'''
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
log = logging.getLogger('jarvis.project_journal_daily')
STATE_FILE = PROJECTS_DIR / '_daily_state.json'

def daily_enabled():
    return os.getenv('JARVIS_PROJECT_JOURNAL_DAILY', '1').lower() not in ('0', 'false', 'off', 'no')


def morning_hour():
    
    try:
        return int(os.getenv('JARVIS_PROJECT_JOURNAL_MORNING_HOUR', '8'))
    except ValueError:
        return 8



def evening_hour():
    
    try:
        return int(os.getenv('JARVIS_PROJECT_JOURNAL_EVENING_HOUR', '21'))
    except ValueError:
        return 21



def auto_learn_after_evening():
    project_journal_auto_learn_enabled = project_journal_auto_learn_enabled
    import jarvis.brain_memory
    return project_journal_auto_learn_enabled()


def _load_state():
    if not STATE_FILE.is_file():
        return {
            'days': { } }
    
    try:
        data = json.loads(STATE_FILE.read_text(encoding = 'utf-8'))
        if isinstance(data, dict):
            data.setdefault('days', { })
            return data
        return {
            'days': { } }
    except (json.JSONDecodeError, OSError):
        exc = None
        log.warning('Corrupt project journal daily state: %s', exc)
        exc = None
        del exc
        return {
            'days': { } }
        exc = None
        del exc



def _save_state(data = None):
    PROJECTS_DIR.mkdir(parents = True, exist_ok = True)
    assert_live_write_allowed = assert_live_write_allowed
    import jarvis.live_data_guard
    assert_live_write_allowed(STATE_FILE)
    STATE_FILE.write_text(json.dumps(data, indent = 2), encoding = 'utf-8')


def _day_state(day = None):
    data = _load_state()
    days = data.setdefault('days', { })
    if day not in days:
        days[day] = { }
    return days[day]


def _mark_ran(slug = None, day = None, phase = None):
    data = _load_state()
    day_map = data.setdefault('days', { }).setdefault(day, { })
    if not day_map.get(slug):
        day_map.get(slug)
    day_map[slug] = { }
    if isinstance(day_map[slug], str):
        day_map[slug] = {
            'legacy': day_map[slug] }
    day_map[slug][phase] = datetime.now(timezone.utc).isoformat()
    _save_state(data)


def _already_ran(slug = None, day = None, phase = None):
    data = _load_state()
    entry = data.get('days', { }).get(day, { }).get(slug)
    if not entry:
        return False
    if isinstance(entry, str):
        return True
    return bool(entry.get(phase))


def discover_project_slugs():
    slugs = set()
    env = os.getenv('JARVIS_PROJECT_JOURNAL_PROJECTS', '').strip()
    if env:
        (lambda .0: pass# WARNING: Decompyle incomplete
)(env.split(',')())
    
    try:
        slugs.add(resolve_project(session_namespace = ''))
        for p in list_projects():
            slugs.add(p['slug'])
        return (lambda .0: pass# WARNING: Decompyle incomplete
)(slugs())
    except Exception:
        continue



def _git_repo_root():
    
    try:
        proc = subprocess.run([
            'git',
            '-C',
            str(PROJECT_ROOT),
            'rev-parse',
            '--show-toplevel'], capture_output = True, text = True, timeout = 10)
        if proc.returncode == 0:
            return Path(proc.stdout.strip())
        if (PROJECT_ROOT / '.git').exists():
            return PROJECT_ROOT
        return None
    except (OSError, subprocess.TimeoutExpired):
        continue



def _git_activity(day = None, *, root):
    if not root:
        root
    repo = _git_repo_root()
    if not repo:
        return ''
    since = f'''{day} 00:00:00'''
    lines = []
    
    try:
        proc = subprocess.run([
            'git',
            '-C',
            str(repo),
            'log',
            f'''--since={since}''',
            '--oneline',
            '-20'], capture_output = True, text = True, timeout = 20)
        if proc.returncode == 0 and proc.stdout.strip():
            lines.append('Git commits today:\n' + proc.stdout.strip())
        proc = subprocess.run([
            'git',
            '-C',
            str(repo),
            'status',
            '-sb'], capture_output = True, text = True, timeout = 15)
        if proc.returncode == 0 and proc.stdout.strip():
            lines.append('Git status:\n' + proc.stdout.strip())
        return '\n\n'.join(lines)
    except (OSError, subprocess.TimeoutExpired):
        exc = None
        log.debug('Git activity skipped: %s', exc)
        exc = None
        del exc
        continue
        exc = None
        del exc



def _actions_today(day = None, *, project):
    list_actions = list_actions
    import jarvis.action_log
    if not day:
        day
    d = _today()
    if not project:
        project
    slug = ''.strip().lower()
    rows = list_actions(limit = 80, project = slug) if slug else list_actions(limit = 80)
    out = []
    for row in rows:
        if not row.get('time'):
            row.get('time')
        ts = ''[:10]
        if ts != d:
            continue
        out.append(row)
        if not len(out) >= 40:
            continue
        rows
    return list(reversed(out))


def _format_actions(rows = None):
    if not rows:
        return ''
    lines = [
        'ARIA activity today:']
    for r in rows:
        if not r.get('action'):
            r.get('action')
            if not r.get('event'):
                r.get('event')
        action = 'event'
        if not r.get('module'):
            r.get('module')
        mod = ''
        if not r.get('detail'):
            r.get('detail')
        detail = ''[:120]
        ok = r.get('ok', True)
        status = '' if ok else ' [failed]'
        lines.append(f'''- [{mod}] {action}{status}: {detail}'''.strip())
    return '\n'.join(lines)


def gather_daily_context(slug = None, day = None):
    if not day:
        day
    d = _today()
    parts = [
        f'''Project: {slug}''',
        f'''Date: {d}''']
    git = _git_activity(d)
    if git:
        parts.append(git)
    actions = _format_actions(_actions_today(d, project = slug))
    if actions:
        parts.append(actions)
# WARNING: Decompyle incomplete


def _rule_based_summary(context = None, *, phase, slug):
    bullets = []
    notes = ''
    if phase == 'morning':
        bullets.append(f'''Daily project journal opened for {slug}.''')
        if 'Git status' in context:
            first_line = ''
            for line in context.splitlines():
                if not line.strip():
                    continue
                if line.startswith('Project:'):
                    continue
                if line.startswith('Date:'):
                    continue
                first_line = line.strip()[:160]
                context.splitlines()
            if first_line:
                bullets.append(f'''Starting point: {first_line}''')
        return (bullets, notes)
# WARNING: Decompyle incomplete


def _llm_summary(context = None, *, phase, slug):
    llm = llm
    import jarvis
    label = 'morning kickoff' if phase == 'morning' else 'evening wrap-up'
    prompt = f'''Write a short {label} for the **{slug}** project daily journal. Return JSON only: {{"bullets": ["bullet1", "bullet2"], "notes": "optional paragraph"}}. 2-4 concise bullets about status, progress, blockers, or next steps. Use facts from the context only.\n\n{context[:8000]}'''
# WARNING: Decompyle incomplete


def _apply_auto_section(journal = None, day = None, *, phase, bullets, notes):
    pass
# WARNING: Decompyle incomplete


def update_project_journal_daily(slug = None, *, day, phase, force, memory):
    """Create or update today's project journal page for a phase."""
    if not daily_enabled() and force:
        return {
            'ok': False,
            'slug': slug,
            'message': 'Daily project journals disabled.' }
    if not None:
        pass
    d = _today()
    journal = ProjectJournal(slug)
    journal.ensure(title = slug)
    if force and _already_ran(slug, d, phase):
        return {
            'ok': True,
            'slug': slug,
            'phase': phase,
            'skipped': True,
            'message': 'Already updated.' }
    context = None(slug, d)
    summary = _llm_summary(context, phase = phase, slug = slug)
    if not summary:
        summary = _rule_based_summary(context, phase = phase, slug = slug)
    (bullets, notes) = summary
    _apply_auto_section(journal, d, phase = phase, bullets = bullets, notes = notes)
    _mark_ran(slug, d, phase)
    learned = 0
# WARNING: Decompyle incomplete


def update_all_project_journals(*, phase, force, memory):
    results = []
    for slug in discover_project_slugs():
        results.append(update_project_journal_daily(slug, phase = phase, force = force, memory = memory))
    return results
    except Exception:
        exc = None
        log.warning('Project journal daily failed for %s: %s', slug, exc)
        results.append({
            'ok': False,
            'slug': slug,
            'message': str(exc) })
        exc = None
        del exc
        continue
        exc = None
        del exc


def run_scheduled_daily(now = None, *, memory):
    '''Run morning/evening updates when the clock hits configured hours.'''
    if not daily_enabled():
        return []
    if not None:
        pass
    now = datetime.now()
    results = []
    if now.hour == morning_hour() and now.minute < 10:
        results.extend(update_all_project_journals(phase = 'morning', memory = memory))
    if now.hour == evening_hour() and now.minute < 10:
        results.extend(update_all_project_journals(phase = 'evening', memory = memory))
    return results


def run_startup_daily(*, memory):
    """On server start: ensure today's journals exist (morning); evening if past evening hour."""
    if not daily_enabled():
        return []
    now = None.now()
    results = []
    results.extend(update_all_project_journals(phase = 'morning', memory = memory))
    if now.hour >= evening_hour():
        results.extend(update_all_project_journals(phase = 'evening', memory = memory))
    return results

