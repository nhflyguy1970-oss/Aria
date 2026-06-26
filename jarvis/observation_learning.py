# Source Generated with Decompyle++
# File: observation_learning.cpython-312.pyc (Python 3.12)

'''Observation learning — notes from terminal output, logs, screenshots, and cameras.'''
from __future__ import annotations
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from jarvis import llm
from jarvis.config import DATA_DIR, PROJECT_ROOT
log = logging.getLogger('jarvis.observation_learning')
OBSERVATION_NAMESPACE = 'observed'
OBSERVATION_TAG = 'observation-learn'
REGISTRY_FILE = DATA_DIR / 'observation_learning.json'
OBSERVATIONS_DIR = DATA_DIR / 'observations'
SOURCE_TYPES = ('terminal', 'log', 'screenshot', 'camera', 'action_log')
_MAX_OBSERVE_CHARS = int(os.getenv('JARVIS_OBSERVE_CHARS', '12000'))
_MAX_NOTES = int(os.getenv('JARVIS_OBSERVE_NOTES', '6'))
_DEFAULT_LOG_LINES = int(os.getenv('JARVIS_OBSERVE_LOG_LINES', '200'))
_OBSERVE_CMD = re.compile('\\b(observe|watch|take notes from|note what you see in)\\b', re.I)
_OBSERVE_LOG = re.compile('\\b(observe|watch|read|tail)\\s+(?:the\\s+)?(?:jarvis\\s+)?(?:server\\s+)?logs?\\b', re.I)
_OBSERVE_TERMINAL = re.compile('\\b(observe|watch|note)\\s+(?:the\\s+)?(?:terminal|command)\\s*(?:output)?\\b', re.I)
_OBSERVE_SCREENSHOT = re.compile('\\b(observe|watch|note)\\s+(?:this\\s+)?(?:screenshot|screen|image|photo)\\b', re.I)
_OBSERVE_CAMERA = re.compile('\\b(observe|watch)\\s+(?:the\\s+)?(?:camera|webcam|feed)\\b', re.I)
_OBSERVE_LAST_CMD = re.compile('\\b(observe|note)\\s+(?:the\\s+)?last\\s+(?:command|terminal)\\b', re.I)
_OBSERVE_RECALL = re.compile('\\b(what did you observe|what have you observed|observation recall|your observations)\\b', re.I)
_OBSERVE_RECALL_QUERY = re.compile('(?:what did you observe(?: about)?|what have you observed(?: about)?|observation recall(?: about)?|your observations(?: about)?)\\s+(.+)$', re.I)
_OBSERVE_VISION_PROMPT = 'You are observing this screen or scene to help an assistant remember what happened. Describe apps/windows visible, errors or warnings, status indicators, and anything operationally important. Be factual and concise.'
ObserveResult = <NODE:12>()

def _utc_now():
    return datetime.now(timezone.utc).isoformat()


def _slugify(text = None):
    if not text:
        text
    s = re.sub('[^\\w\\s-]', '', ''.lower())
    s = re.sub('[\\s_]+', '-', s).strip('-')
    if not s[:48]:
        s[:48]
    return 'observation'


def observations_dir():
    OBSERVATIONS_DIR.mkdir(parents = True, exist_ok = True)
    return OBSERVATIONS_DIR


def _load_registry():
    if not REGISTRY_FILE.is_file():
        return {
            'sources': [] }
    
    try:
        data = json.loads(REGISTRY_FILE.read_text(encoding = 'utf-8'))
        if isinstance(data, dict) and isinstance(data.get('sources'), list):
            return data
        return {
            None: [] }
    except (json.JSONDecodeError, OSError):
        exc = None
        log.warning('Corrupt observation registry: %s', exc)
        exc = None
        del exc
        return {
            'sources': [] }
        exc = None
        del exc



def _save_registry(data = None):
    REGISTRY_FILE.parent.mkdir(parents = True, exist_ok = True)
    assert_live_write_allowed = assert_live_write_allowed
    import jarvis.live_data_guard
    assert_live_write_allowed(REGISTRY_FILE)
    REGISTRY_FILE.write_text(json.dumps(data, indent = 2), encoding = 'utf-8')


def _register_source(*, title, source_type, path, notes):
    data = _load_registry()
    sid = hashlib.sha256(f'''{title}|{source_type}|{path}|{time.time()}'''.encode()).hexdigest()[:12]
    entry = {
        'id': sid,
        'title': title,
        'type': source_type,
        'path': path,
        'notes': notes,
        'observed_at': _utc_now() }
# WARNING: Decompyle incomplete


def list_observation_sources(*, limit):
    return list(_load_registry().get('sources', []))[:limit]


def observation_stats():
    sources = list_observation_sources(limit = 500)
    return {
        'total_sources': sum,
        'total_notes': (lambda .0: pass# WARNING: Decompyle incomplete
)(sources()),
        'namespace': OBSERVATION_NAMESPACE,
        'by_type': _count_by_type(sources) }


def _count_by_type(sources = None):
    counts = { }
    for s in sources:
        if not s.get('type'):
            s.get('type')
        t = 'unknown'.lower()
        counts[t] = counts.get(t, 0) + 1
    return counts


def is_observe_command(message = None):
    if not message:
        message
    return bool(_OBSERVE_CMD.search(''.strip()))


def is_observe_log(message = None):
    if not message:
        message
    return bool(_OBSERVE_LOG.search(''.strip()))


def is_observe_terminal(message = None):
    if not message:
        message
    return bool(_OBSERVE_TERMINAL.search(''.strip()))


def is_observe_screenshot(message = None):
    if not message:
        message
    return bool(_OBSERVE_SCREENSHOT.search(''.strip()))


def is_observe_camera(message = None):
    if not message:
        message
    return bool(_OBSERVE_CAMERA.search(''.strip()))


def is_observe_last_command(message = None):
    if not message:
        message
    return bool(_OBSERVE_LAST_CMD.search(''.strip()))


def is_observation_recall(message = None):
    if not message:
        message
    return bool(_OBSERVE_RECALL.search(''.strip()))


def parse_observation_recall_query(message = None):
    if not message:
        message
    m = _OBSERVE_RECALL_QUERY.search(''.strip())
    if m:
        return m.group(1).strip().rstrip('?.!')
    return None.rstrip('?.!')


def parse_terminal_text(message = None):
    '''Extract pasted terminal output after a colon or fenced block.'''
    if not message:
        message
    text = ''.strip()
    m = re.search('```(?:bash|sh|text|console)?\\n([\\s\\S]+?)```', text)
    if re.search('```(?:bash|sh|text|console)?\\n([\\s\\S]+?)```', text):
        return m.group(1).strip()
    for pat in None:
        m = re.match(pat, text, re.I)
        if not m:
            continue
        
        return None, m.group(1).strip()
    return ''


def _tail_file(path = None, *, max_lines, max_chars):
    if not path.is_file():
        raise FileNotFoundError(f'''Log not found: {path}''')
    
    try:
        lines = path.read_text(encoding = 'utf-8', errors = 'replace').splitlines()
        tail = '\n'.join(lines[-max_lines:])
        if len(tail) > max_chars:
            tail = tail[-max_chars:]
        return tail.strip()
    except OSError:
        exc = None
        raise ValueError(f'''Could not read log: {exc}'''), exc
        exc = None
        del exc



def resolve_log_path(message = None):
    '''Pick a log file from the message or defaults.'''
    if not message:
        message
    lower = ''.lower()
    if not message:
        message
    m = re.search('[`\'\\"]?([\\w./-]+\\.log)[`\'\\"]?', '', re.I)
    if re.search('[`\'\\"]?([\\w./-]+\\.log)[`\'\\"]?', '', re.I):
        candidate = Path(m.group(1)).expanduser()
        if candidate.is_file():
            return candidate
        for base in (None, DATA_DIR, DATA_DIR / 'logs'):
            resolved = (base / candidate).resolve()
            if not resolved.is_file():
                continue
            
            return (None, DATA_DIR, DATA_DIR / 'logs'), resolved
    if 'serve' in lower and p.is_file():
        return p
    from jarvis.logging_config import log_file_path
    primary = log_file_path()
    if primary.is_file():
        return primary
    root_log = None / 'jarvis.log'
    if root_log.is_file():
        return root_log
    raise None('No log file found — set JARVIS_LOG_FILE or check data/logs/')


def _save_observation_text(text = None, *, subdir, title):
    folder = observations_dir() / subdir
    folder.mkdir(parents = True, exist_ok = True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = folder / f'''{_slugify(title)}_{stamp}.txt'''
    dest.write_text(text, encoding = 'utf-8')
    return dest


def extract_observation_notes(text = None, *, source_type, title, max_notes):
    if not text:
        text
    excerpt = ''.strip()
    if not excerpt:
        return []
    if None(excerpt) > _MAX_OBSERVE_CHARS:
        excerpt = excerpt[-_MAX_OBSERVE_CHARS:]
# WARNING: Decompyle incomplete


def _store_notes(memory = None, notes = None, *, source_type, title):
    stored = []
    src_tag = f'''observe-source:{_slugify(title)[:28]}'''
    for note in notes:
        body = note.strip()
        if not body:
            continue
        prefix = f'''[{source_type}] ''' if not body.lower().startswith(f'''[{source_type}]''') else ''
        content = f'''{prefix}{body}'''
        memory.add('note', content, tags = [
            OBSERVATION_TAG,
            src_tag,
            f'''observe-type:{source_type}'''], namespace = OBSERVATION_NAMESPACE)
        stored.append(content)
    return stored
    except ValueError:
        exc = None
        log.debug('Skip observation note: %s', exc)
        exc = None
        del exc
        continue
        exc = None
        del exc


def observe_text(memory = None, text = None, *, source_type, title, save_raw):
    if source_type not in SOURCE_TYPES:
        source_type = 'terminal'
    if not text:
        text
    cleaned = ''.strip()
    if not cleaned:
        return ObserveResult(False, title, source_type, message = 'Nothing to observe.')
    saved_path = None
    if save_raw:
        subdir = {
            'log': 'logs',
            'screenshot': 'screenshots',
            'camera': 'camera' }.get(source_type, source_type)
        saved_path = str(_save_observation_text(cleaned, subdir = subdir, title = title))
    notes = extract_observation_notes(cleaned, source_type = source_type, title = title)
    if not notes:
        return ObserveResult(False, title, source_type, message = 'Nothing substantive to note from that observation.', path = saved_path)
    stored = None(memory, notes, source_type = source_type, title = title)
    sid = _register_source(title = title, source_type = source_type, path = saved_path, notes = len(stored))
    return ObserveResult(True, title, source_type, notes = stored, message = f'''Recorded **{len(stored)}** observation note(s) from **{title}**.''', path = saved_path, source_id = sid)


def observe_log(memory = None, *, message, lines):
    path = resolve_log_path(message)
    if not lines:
        lines
    tail = _tail_file(path, max_lines = _DEFAULT_LOG_LINES)
    title = path.name
    return observe_text(memory, tail, source_type = 'log', title = title)


def observe_action_log(memory = None, *, limit):
    list_actions = list_actions
    import jarvis.action_log
    rows = list_actions(limit = limit)
    if not rows:
        return ObserveResult(False, 'action_log', 'action_log', message = 'Action log is empty.')
    lines = None
    for r in rows:
        ts = r.get('time', '')
        if not r.get('event'):
            r.get('event')
            if not r.get('action'):
                r.get('action')
        event = 'event'
        if not r.get('detail'):
            r.get('detail')
            if not r.get('message'):
                r.get('message')
        detail = ''
        if not r.get('module'):
            r.get('module')
        mod = ''
        lines.append(f'''{ts} [{mod}] {event}: {detail}''')
    blob = '\n'.join(lines)
    return observe_text(memory, blob, source_type = 'action_log', title = 'action_log')


def observe_terminal(memory = None, text = None, *, title):
    return observe_text(memory, text, source_type = 'terminal', title = title)


def observe_screenshot(memory = None, vision = None, path = None):
    p = Path(path).expanduser()
    if not p.is_file():
        return ObserveResult(False, p.name, 'screenshot', message = f'''Image not found: {p}''')
    folder = None() / 'screenshots'
    folder.mkdir(parents = True, exist_ok = True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if not p.suffix:
        p.suffix
    dest = folder / f'''{p.stem}_{stamp}{'.jpg'}'''
    shutil.copy2(p, dest)
    description = vision.analyze(_OBSERVE_VISION_PROMPT, str(dest))
    if description.startswith('ERROR:'):
        return ObserveResult(False, p.stem, 'screenshot', message = description, path = str(dest))
    ocr = None.ocr(str(dest))
    parts = [
        f'''Visual description:\n{description}''']
    if ocr and ocr.startswith('ERROR:') and ocr.strip().lower() not in ('no text', 'no text.'):
        parts.append(f'''Visible text:\n{ocr}''')
    blob = '\n\n'.join(parts)
    result = observe_text(memory, blob, source_type = 'screenshot', title = p.stem, save_raw = False)
    result.path = str(dest)
    if result.ok:
        _register_source(title = p.stem, source_type = 'screenshot', path = str(dest), notes = len(result.notes))
    return result


def capture_camera_frame(*, device):
    '''Grab one frame from a V4L2 device or RTSP URL via ffmpeg.'''
    if not device:
        device
    dev = os.getenv('JARVIS_CAMERA_DEVICE', '/dev/video0').strip()
    folder = observations_dir() / 'camera'
    folder.mkdir(parents = True, exist_ok = True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = folder / f'''camera_{stamp}.jpg'''
    if dev.startswith('rtsp://') and dev.startswith('http://') or dev.startswith('https://'):
        cmd = [
            'ffmpeg',
            '-y',
            '-rtsp_transport',
            'tcp',
            '-i',
            dev,
            '-frames:v',
            '1',
            '-q:v',
            '2',
            str(dest)]
    else:
        cmd = [
            'ffmpeg',
            '-y',
            '-f',
            'v4l2',
            '-i',
            dev,
            '-frames:v',
            '1',
            '-q:v',
            '2',
            str(dest)]
    proc = subprocess.run(cmd, capture_output = True, text = True, timeout = 30)
    if not proc.returncode != 0 or dest.is_file():
        if not proc.stderr:
            proc.stderr
            if not proc.stdout:
                proc.stdout
        err = ''.strip()[-400:]
        if not err:
            err
        raise ValueError(f'''Camera capture failed for {dev}''')
    return dest


def observe_camera(memory = None, vision = None, *, device):
    
    try:
        frame = capture_camera_frame(device = device)
        result = observe_screenshot(memory, vision, str(frame))
        result.source_type = 'camera'
        if result.ok:
            result.title = 'camera'
            result.message = result.message.replace('screenshot', 'camera')
        return result
    except ValueError:
        exc = None
        del exc
        return None
        None = 
        del exc



def list_observations(memory = None, *, query, source_type, limit):
    entries = memory.list_entries(entry_type = 'note', namespace = OBSERVATION_NAMESPACE)
# WARNING: Decompyle incomplete


def observation_context_for_chat(memory = None, message = None, *, limit):
    pass
# WARNING: Decompyle incomplete


def format_observations_markdown(entries = None, *, sources):
    lines = []
    if sources:
        lines.append('**Observation sources**')
        for s in sources[:12]:
            if not s.get('title'):
                s.get('title')
            title = s.get('type', 'source')
            typ = s.get('type', '?')
            if not s.get('notes'):
                s.get('notes')
            notes = 0
            lines.append(f'''- **{title}** ({typ}, {notes} notes)''')
        lines.append('')
    if not entries:
        lines.append('_No observation notes yet._')
        return '\n'.join(lines)
    None.append('**Observation notes**')
    for e in entries:
        lines.append(f'''• {e.get('content', '')}''')
    return '\n'.join(lines)

