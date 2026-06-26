# Source Generated with Decompyle++
# File: skill_database.cpython-312.pyc (Python 3.12)

'''Reusable procedure skills — install, repair, and ops playbooks.'''
from __future__ import annotations
import json
import logging
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from jarvis.config import DATA_DIR, PROJECT_ROOT
log = logging.getLogger('jarvis.skills')
SKILLS_DIR = DATA_DIR / 'skills'
INDEX_FILE = SKILLS_DIR / 'index.json'
DEFAULTS_DIR = Path(__file__).resolve().parent / 'skill_defaults'
SKILL_TAG = 'skill-db'
_STEP_TYPES = frozenset({
    'note',
    'check',
    'script',
    'command'})

def _utc_now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def slugify(text = None):
    if not text:
        text
    s = re.sub('[^\\w\\s-]', '', ''.lower())
    s = re.sub('[\\s_]+', '-', s).strip('-')
    if not s[:80]:
        s[:80]
    return 'skill'


def exec_enabled():
    return os.getenv('JARVIS_SKILL_EXEC', '').lower() in ('1', 'true', 'yes')


def _load_index():
    if not INDEX_FILE.is_file():
        return {
            'skills': { } }
    
    try:
        data = json.loads(INDEX_FILE.read_text(encoding = 'utf-8'))
        if isinstance(data, dict):
            data.setdefault('skills', { })
            return data
        return {
            'skills': { } }
    except (json.JSONDecodeError, OSError):
        exc = None
        log.warning('Corrupt skills index: %s', exc)
        exc = None
        del exc
        return {
            'skills': { } }
        exc = None
        del exc



def _save_index(data = None):
    SKILLS_DIR.mkdir(parents = True, exist_ok = True)
    assert_live_write_allowed = assert_live_write_allowed
    import jarvis.live_data_guard
    assert_live_write_allowed(INDEX_FILE)
    INDEX_FILE.write_text(json.dumps(data, indent = 2), encoding = 'utf-8')


def _skill_path(slug = None):
    return SKILLS_DIR / f'''{slugify(slug)}.json'''


def ensure_default_skills():
    '''Copy bundled defaults into data/skills/ when missing.'''
    SKILLS_DIR.mkdir(parents = True, exist_ok = True)
    installed = []
    if not DEFAULTS_DIR.is_dir():
        return installed
    index = None()
    for path in sorted(DEFAULTS_DIR.glob('*.json')):
        raw = json.loads(path.read_text(encoding = 'utf-8'))
        if not raw.get('slug'):
            raw.get('slug')
        slug = slugify(path.stem)
        dest = _skill_path(slug)
        if dest.is_file():
            continue
        skill = _normalize_skill(raw, slug = slug)
        _write_skill_file(skill)
        if not skill.get('tags'):
            skill.get('tags')
        index['skills'][slug] = {
            'name': skill['name'],
            'tags': [],
            'updated': skill.get('updated') }
        installed.append(slug)
    if installed:
        _save_index(index)
    return installed
    except (json.JSONDecodeError, OSError):
        continue


def _normalize_skill(data = None, *, slug):
    if not slug:
        slug
        if not data.get('slug'):
            data.get('slug')
            if not data.get('name'):
                data.get('name')
    slug = slugify('skill')
    steps = []
    if not data.get('steps'):
        data.get('steps')
    for i, step in enumerate([]):
        if isinstance(step, str):
            steps.append({
                'type': 'command',
                'title': f'''Step {i + 1}''',
                'command': step })
            continue
        if not isinstance(step, dict):
            continue
        if not step.get('type'):
            step.get('type')
        stype = 'command'.strip().lower()
        if stype not in _STEP_TYPES:
            stype = 'command'
        if not step.get('title'):
            step.get('title')
        if not step.get('command'):
            step.get('command')
        if not step.get('script'):
            step.get('script')
        if not step.get('text'):
            step.get('text')
            if not step.get('note'):
                step.get('note')
        steps.append({
            'type': stype,
            'title': f'''Step {i + 1}'''.strip(),
            'command': ''.strip(),
            'script': ''.strip(),
            'text': ''.strip() })
    now = _utc_now()
    if not data.get('name'):
        data.get('name')
    if not data.get('description'):
        data.get('description')
    if not data.get('tags'):
        data.get('tags')
# WARNING: Decompyle incomplete


def _write_skill_file(skill = None):
    SKILLS_DIR.mkdir(parents = True, exist_ok = True)
    path = _skill_path(skill['slug'])
    assert_live_write_allowed = assert_live_write_allowed
    import jarvis.live_data_guard
    assert_live_write_allowed(path)
    path.write_text(json.dumps(skill, indent = 2), encoding = 'utf-8')


def save_skill(name = None, *, description, steps, tags, slug):
    ensure_default_skills()
    if not slug:
        slug
    if not steps:
        steps
    if not tags:
        tags
    skill = _normalize_skill({
        'slug': name,
        'name': name,
        'description': description,
        'steps': [],
        'tags': [] })
    existing = load_skill(skill['slug'])
    if existing:
        if not existing.get('created_at'):
            existing.get('created_at')
        skill['created_at'] = skill['created_at']
        if not existing.get('version'):
            existing.get('version')
        skill['version'] = int(1) + 1
    _write_skill_file(skill)
    index = _load_index()
    if not skill.get('tags'):
        skill.get('tags')
    index['skills'][skill['slug']] = {
        'name': skill['name'],
        'tags': [],
        'updated': skill['updated'] }
    _save_index(index)
    return skill


def load_skill(slug = None):
    ensure_default_skills()
    path = _skill_path(slug)
    if not path.is_file():
        return None
    
    try:
        data = json.loads(path.read_text(encoding = 'utf-8'))
        if isinstance(data, dict):
            return data
        return None
    except (json.JSONDecodeError, OSError):
        return None



def delete_skill(slug = None):
    path = _skill_path(slug)
    if not path.is_file():
        return False
    path.unlink()
    index = _load_index()
    index.get('skills', { }).pop(slugify(slug), None)
    _save_index(index)
    return True


def list_skills(*, query):
    pass
# WARNING: Decompyle incomplete


def resolve_skill(query = None):
    if not query:
        query
    q = ''.strip()
    if not q:
        return None
    slug = slugify(q)
    direct = load_skill(slug)
    if direct:
        return direct
    hits = None(query = q)
    if hits:
        return hits[0]
    alt = None(q.replace(' skill', ''))
    return load_skill(alt)


def format_skill_markdown(skill = None):
    if not skill.get('description'):
        skill.get('description')
    lines = [
        f'''**{skill.get('name')}** (`{skill.get('slug')}`)''',
        '',
        '_No description._',
        '',
        '**Steps**']
    if not skill.get('steps'):
        skill.get('steps')
    for i, step in enumerate([], 1):
        stype = step.get('type', 'command')
        if not step.get('title'):
            step.get('title')
        title = f'''Step {i}'''
        if stype == 'note':
            if not step.get('text'):
                step.get('text')
            lines.append(f'''{i}. _{title}_ — {step.get('command')}''')
            continue
        if stype == 'script':
            lines.append(f'''{i}. **{title}** — `{step.get('script')}`''')
            continue
        if not step.get('command'):
            step.get('command')
            if not step.get('script'):
                step.get('script')
        cmd = ''
        lines.append(f'''{i}. **{title}** (`{stype}`) — `{cmd}`''')
    if not skill.get('tags'):
        skill.get('tags')
    tags = []
    if tags:
        lines.extend([
            '',
            f'''Tags: {', '.join(tags)}'''])
    return '\n'.join(lines)


def _blocked_command(cmd = None):
    pass
# WARNING: Decompyle incomplete


def _resolve_script(script = None):
    rel = script.strip().lstrip('./')
    if not rel.startswith('scripts/'):
        return None
    path = (PROJECT_ROOT / rel).resolve()
    
    try:
        path.relative_to((PROJECT_ROOT / 'scripts').resolve())
        if path.is_file():
            return path
        return None
    except ValueError:
        return None



def run_skill_step(step = None, *, dry_run, timeout):
    if not step.get('type'):
        step.get('type')
    stype = 'command'.lower()
    if not step.get('title'):
        step.get('title')
    title = 'Step'
    if stype == 'note':
        if not step.get('text'):
            step.get('text')
        return {
            'ok': True,
            'type': 'note',
            'title': title,
            'output': '' }
    if None == 'script':
        if not step.get('script'):
            step.get('script')
        script = ''
        path = _resolve_script(script)
        if not path:
            return {
                'ok': False,
                'type': 'script',
                'title': title,
                'error': f'''Script not allowed or missing: {script}''' }
        if None:
            return {
                'ok': True,
                'type': 'script',
                'title': title,
                'dry_run': True,
                'command': str(path) }
        
        try:
            proc = subprocess.run([
                'bash',
                str(path)], capture_output = True, text = True, timeout = timeout, cwd = str(PROJECT_ROOT))
            if not proc.stdout:
                proc.stdout
            if not proc.stderr:
                proc.stderr
            out = ('' + '').strip()[:4000]
            return {
                'ok': proc.returncode == 0,
                'type': 'script',
                'title': title,
                'command': str(path),
                'exit_code': proc.returncode,
                'output': out }
            if not step.get('command'):
                step.get('command')
            cmd = ''.strip()
            if not cmd:
                return {
                    'ok': True,
                    'type': stype,
                    'title': title,
                    'output': '(empty)' }
            blocked = None(cmd)
            if blocked:
                return {
                    'ok': False,
                    'type': stype,
                    'title': title,
                    'error': blocked }
            if None:
                return {
                    'ok': True,
                    'type': stype,
                    'title': title,
                    'dry_run': True,
                    'command': cmd }
            if not None():
                return {
                    'ok': False,
                    'type': stype,
                    'title': title,
                    'error': 'Skill execution disabled. Set JARVIS_SKILL_EXEC=1 in data/jarvis.env.' }
            
            try:
                proc = subprocess.run(cmd, shell = True, capture_output = True, text = True, timeout = timeout, cwd = str(PROJECT_ROOT))
                if not proc.stdout:
                    proc.stdout
                if not proc.stderr:
                    proc.stderr
                out = ('' + '').strip()[:4000]
                if not proc.returncode == 0:
                    proc.returncode == 0
                ok = stype == 'check'
                return {
                    'ok': ok,
                    'type': stype,
                    'title': title,
                    'command': cmd,
                    'exit_code': proc.returncode,
                    'output': out }
                except (OSError, subprocess.TimeoutExpired):
                    exc = None
                    del exc
                    return None
                    None = 
                    del exc
            except (OSError, subprocess.TimeoutExpired):
                exc = None
                del exc
                return None
                None = 
                del exc




def run_skill(slug = None, *, dry_run, stop_on_error):
    skill = resolve_skill(slug)
    if not skill:
        return {
            'ok': False,
            'message': f'''No skill matching **{slug}**.''',
            'slug': slugify(slug) }
    results = None
    if not skill.get('steps'):
        skill.get('steps')
    for step in []:
        result = run_skill_step(step, dry_run = dry_run)
        results.append(result)
        if result.get('ok'):
            continue
        if not stop_on_error:
            continue
        if not step.get('type'):
            step.get('type')
        if not 'command' != 'check':
            continue
        []
# WARNING: Decompyle incomplete


def _format_run_summary(skill = None, results = None, *, dry_run, ok):
    mode = 'Preview' if dry_run else 'Run'
    status = 'completed' if ok else 'stopped with errors'
    lines = [
        f'''**{mode}:** skill **{skill['name']}** (`{skill['slug']}`) — {status}''',
        '']
    for i, r in enumerate(results, 1):
        if not r.get('title'):
            r.get('title')
        title = f'''Step {i}'''
        if r.get('type') == 'note':
            lines.append(f'''{i}. {title}: {r.get('output', '')}''')
            continue
        if not r.get('command'):
            r.get('command')
        cmd = ''
        if r.get('dry_run'):
            lines.append(f'''{i}. **{title}** — would run: `{cmd}`''')
            continue
        if r.get('error'):
            lines.append(f'''{i}. **{title}** — error: {r['error']}''')
            continue
        code = r.get('exit_code', 0)
        mark = 'OK' if r.get('ok') else f'''exit {code}'''
        lines.append(f'''{i}. **{title}** — {mark}''')
        if not r.get('output'):
            continue
        lines.append(f'''```\n{r['output'][:1200]}\n```''')
    if dry_run:
        lines.extend([
            '',
            '_Dry run only. Say **run docker repair skill confirm** to execute, or set `JARVIS_SKILL_EXEC=1`._'])
    return '\n'.join(lines)


def parse_skill_run_query(message = None):
    '''Return (skill query, confirm/exec).'''
    if not message:
        message
    text = ''.strip()
    confirm = bool(re.search('\\b(confirm|execute|for real|actually run)\\b', text, re.I))
    for pat in ('\\brun\\s+(?:the\\s+)?(.+?)\\s+skill\\b', '\\brun\\s+skill[:\\s]+(.+)', '\\bskill\\s+run[:\\s]+(.+)'):
        m = re.search(pat, text, re.I)
        if not m:
            continue
        q = m.group(1).strip()
        q = re.sub('\\b(confirm|execute|for real|actually run)\\b', '', q, flags = re.I).strip()
        
        return ('\\brun\\s+(?:the\\s+)?(.+?)\\s+skill\\b', '\\brun\\s+skill[:\\s]+(.+)', '\\bskill\\s+run[:\\s]+(.+)'), (q, confirm)
    return ('', confirm)


def parse_skill_save_message(message = None):
    if not message:
        message
    text = ''.strip()
    for pat in ('^(?:save|define|create)\\s+skill[:\\s]+(.+)$', '^skill[:\\s]+save[:\\s]+(.+)$'):
        m = re.match(pat, text, re.I | re.S)
        if not m:
            continue
        body = m.group(1).strip()
        if ' — ' in body:
            (name, rest) = body.split(' — ', 1)
        elif not ' - ' in body and body.startswith('-'):
            (name, rest) = body.split(' - ', 1)
        elif ':' in body:
            (name, rest) = body.split(':', 1)
        else:
            rest = ''
            name = body
        name = name.strip()
        rest = rest.strip()
        steps = []
        description = ''
        for line in rest.splitlines():
            line = line.strip()
            if not line:
                continue
            if re.match('^\\d+[\\).\\]]\\s+', line):
                step_text = re.sub('^\\d+[\\).\\]]\\s+', '', line).strip()
                steps.append({
                    'type': 'command',
                    'title': f'''Step {len(steps) + 1}''',
                    'command': step_text })
                continue
            if line.lower().startswith('desc:'):
                description = line[5:].strip()
                continue
            if not description and steps:
                description = line
                continue
            steps.append({
                'type': 'command',
                'title': f'''Step {len(steps) + 1}''',
                'command': line })
        
        return None, {
            'name': name,
            'description': description,
            'steps': steps }


def skills_context_for_query(query = None, *, max_chars):
    '''Inject matching skill summaries into chat context.'''
    hits = list_skills(query = query)[:2]
    if not hits:
        return ''
    parts = [
        'Matching procedure skills (say **run NAME skill** to preview/run):']
    for skill in hits:
        parts.append(f'''- **{skill['name']}** (`{skill['slug']}`): {skill.get('description', '')[:200]}''')
    text = '\n'.join(parts)
    return text[:max_chars]

