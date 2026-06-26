# Source Generated with Decompyle++
# File: comfyui_settings_jobs.cpython-312.pyc (Python 3.12)

'''Background ComfyUI settings changes (mode/checkpoint restart can take ~2 min).'''
from __future__ import annotations
import threading
import time
import uuid
from typing import Any, Callable
from jarvis.metrics import note_comfyui_settings_job
_lock = threading.Lock()
_jobs: 'dict[str, dict[str, Any]]' = { }

def _run_job(job_id = None, fn = None):
    
    try:
        result = fn()
        ok = bool(result.get('ok', True))
        note_comfyui_settings_job(ok = ok)
        _lock
        job = _jobs.get(job_id)
        if job:
            job['done'] = True
            job['result'] = result
            if not result.get('message'):
                result.get('message')
            job['message'] = 'Complete' if result.get('ok') else 'Failed'
            job['pct'] = 100
        None(None, None)
        return None
    except Exception:
        exc = None
        result = {
            'ok': False,
            'message': str(exc) }
        note_comfyui_settings_job(ok = False)
        exc = None
        del exc
        continue
        exc = None
        del exc
        with None:
            if not None:
                pass
        return None



def submit(label = None, fn = None):
    job_id = uuid.uuid4().hex[:12]
    _lock
    _jobs[job_id] = {
        'id': job_id,
        'label': label,
        'pct': 0,
        'message': 'Queued…',
        'done': False,
        'result': None,
        'started': time.time() }
    None(None, None)
    threading.Thread(target = _run_job, args = (job_id, fn), daemon = True, name = f'''comfyui-settings-{job_id[:6]}''').start()
    _lock
    job = _jobs.get(job_id)
    if job:
        job['message'] = 'Applying settings…'
        job['pct'] = 10
    None(None, None)
    return job_id
    with None:
        if not None:
            pass
    continue
    with None:
        if not None:
            pass
    return job_id


def get_job(job_id = None):
    _lock
    job = _jobs.get(job_id)
    None(None, None)
    return 
    with None:
        if not None, dict(job) if job else None:
            pass

