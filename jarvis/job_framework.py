# Source Generated with Decompyle++
# File: job_framework.cpython-312.pyc (Python 3.12)

'''Unified job queue interface (media, coding, background).'''
from __future__ import annotations
from typing import Any, Callable
QUEUES = ('media', 'coding', 'background', 'audio')

def stats(queue = None):
    if queue == 'media':
        job_stats = job_stats
        import jarvis.media_jobs
        return job_stats()
    if None == 'coding':
        job_stats = job_stats
        import jarvis.coding_jobs
        return job_stats()
    if None == 'background':
        job_stats = job_stats
        import jarvis.coding_jobs
        return job_stats()
    if None == 'audio':
        job_stats = job_stats
        import jarvis.audio_progress
        return job_stats()
    raise None(f'''Unknown queue: {queue}''')


def get_job(queue = None, job_id = None):
    if queue == 'media':
        _get = get_job
        import jarvis.media_jobs
        return _get(job_id)
    if None in ('coding', 'background'):
        _get = get_job
        import jarvis.coding_jobs
        return _get(job_id)
    if None == 'audio':
        _get = get_job
        import jarvis.audio_progress
        return _get(job_id)
    raise None(f'''Unknown queue: {queue}''')


def cancel(queue = None, job_id = None):
    if queue == 'media':
        cancel_job = cancel_job
        import jarvis.media_jobs
        return cancel_job(job_id)
    if None in ('coding', 'background'):
        cancel_job = cancel_job
        import jarvis.coding_jobs
        return cancel_job(job_id)
    if None == 'audio':
        cancel_job = cancel_job
        import jarvis.audio_progress
        return cancel_job(job_id)
    raise None(f'''Unknown queue: {queue}''')


def list_recent(queue = None, limit = None):
    if queue == 'media':
        list_recent = list_recent
        import jarvis.media_jobs
        return list_recent(limit)
    if None in ('coding', 'background'):
        list_recent = list_recent
        import jarvis.coding_jobs
        return list_recent(limit)
    if None == 'audio':
        list_recent = list_recent
        import jarvis.audio_progress
        return list_recent(limit)
    raise None(f'''Unknown queue: {queue}''')


def submit(queue = None, label = None, fn = None):
    if queue == 'media':
        _submit = submit
        import jarvis.media_jobs
        return _submit(label, fn)
    if None in ('coding', 'background'):
        _submit = submit
        import jarvis.coding_jobs
        return _submit(label, fn)
    raise None(f'''Queue {queue} does not support generic submit''')


def submit_assistant_action(assistant = None, action = None, params = None, message = ('action', 'str', 'params', 'dict', 'message', 'str', 'return', 'str')):
    '''Submit based on registry queue metadata.'''
    submit_background = submit_action
    import jarvis.background_jobs
    get_queue = get_queue
    import jarvis.handlers.registry
    submit_media = submit_assistant_action
    import jarvis.media_jobs
    queue = get_queue(action)
    if queue == 'media':
        return submit_media(assistant, action, params, message)
    if None == 'background':
        return submit_background(assistant, action, params, message)
    raise None(f'''Action {action} is not a queued action (queue={queue})''')

