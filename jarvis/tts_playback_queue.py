# Source Generated with Decompyle++
# File: tts_playback_queue.cpython-312.pyc (Python 3.12)

'''Sequential TTS playback queue — generate ahead, play without HTTP gaps.'''
from __future__ import annotations
import logging
import queue
import threading
from pathlib import Path
log = logging.getLogger('jarvis.tts_queue')
_PLAY_QUEUE: 'queue.Queue[str | None]' = queue.Queue()
_IDLE = threading.Event()
_IDLE.set()
_WORKER_STARTED = False
_START_LOCK = threading.Lock()
_PENDING = 0
_PENDING_LOCK = threading.Lock()

def _mark_busy():
    global _PENDING
    _PENDING_LOCK
    _PENDING += 1
    _IDLE.clear()
    None(None, None)
    return None
    with None:
        if not None:
            pass


def _mark_done():
    global _PENDING
    _PENDING_LOCK
    _PENDING = max(0, _PENDING - 1)
    if _PENDING == 0 and _PLAY_QUEUE.empty():
        _IDLE.set()
    None(None, None)
    return None
    with None:
        if not None:
            pass


def _ensure_worker():
    global _WORKER_STARTED
    _START_LOCK
    if _WORKER_STARTED:
        None(None, None)
        return None
    _WORKER_STARTED = True
    threading.Thread(target = _worker, daemon = True, name = 'jarvis-tts-playback').start()
    None(None, None)
    return None
    with None:
        if not None:
            pass


def _worker():
    play_file = play_file
    import jarvis.audio_device
    path = _PLAY_QUEUE.get()
    
    try:
        if path and Path(path).is_file():
            result = play_file(path)
            if str(result).startswith('ERROR'):
                log.warning('TTS queue play failed: %s', result)
        _mark_done()
        _PLAY_QUEUE.task_done()
        continue
    except Exception:
        exc = None
        log.warning('TTS queue worker: %s', exc)
        
        try:
            exc = None
            del exc
            continue
            exc = None
            del exc
            
            try:
                pass
            except:
                _mark_done()
                _PLAY_QUEUE.task_done()





def enqueue_play(path = None):
    '''Queue a WAV for sequential playback (returns immediately).'''
    p = str(path)
    if not Path(p).is_file():
        log.warning('TTS queue skip missing file: %s', p)
        return None
    _ensure_worker()
    _mark_busy()
    _PLAY_QUEUE.put(p)


def clear_tts_queue():
    '''Stop current playback and drop pending chunks.'''
    global _PENDING
    stop_playback = stop_playback
    import jarvis.audio_device
    stop_playback()
    drained = 0
    
    try:
        _PLAY_QUEUE.get_nowait()
        drained += 1
        continue
    except queue.Empty:
        pass

    _PENDING_LOCK
    _PENDING = max(0, _PENDING - drained)
    if _PENDING == 0:
        _IDLE.set()
    None(None, None)
    return None
    with None:
        if not None:
            pass


def wait_tts_idle(timeout = None):
    '''Block until queued playback finishes.'''
    pass
# WARNING: Decompyle incomplete


def tts_queue_busy():
    return not _IDLE.is_set()

