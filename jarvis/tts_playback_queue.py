"""Sequential TTS playback queue — generate ahead, play without HTTP gaps."""

from __future__ import annotations

import logging
import queue
import threading
from pathlib import Path

log = logging.getLogger("jarvis.tts_queue")

_PLAY_QUEUE: queue.Queue[str | None] = queue.Queue()
_IDLE = threading.Event()
_IDLE.set()
_WORKER_STARTED = False
_START_LOCK = threading.Lock()
_PENDING = 0
_PENDING_LOCK = threading.Lock()


def _mark_busy() -> None:
    global _PENDING
    with _PENDING_LOCK:
        _PENDING += 1
        _IDLE.clear()


def _mark_done() -> None:
    global _PENDING
    with _PENDING_LOCK:
        _PENDING = max(0, _PENDING - 1)
        if _PENDING == 0 and _PLAY_QUEUE.empty():
            _IDLE.set()


def _ensure_worker() -> None:
    global _WORKER_STARTED
    with _START_LOCK:
        if _WORKER_STARTED:
            return
        _WORKER_STARTED = True
        threading.Thread(target=_worker, daemon=True, name="jarvis-tts-playback").start()


def _worker() -> None:
    from jarvis.audio_device import play_file

    while True:
        path = _PLAY_QUEUE.get()
        try:
            if path and Path(path).is_file():
                result = play_file(path)
                if str(result).startswith("ERROR"):
                    log.warning("TTS queue play failed: %s", result)
        except Exception as exc:
            log.warning("TTS queue worker: %s", exc)
        finally:
            _mark_done()
            _PLAY_QUEUE.task_done()


def enqueue_play(path: str | Path) -> None:
    """Queue a WAV for sequential playback (returns immediately)."""
    p = str(path)
    if not Path(p).is_file():
        log.warning("TTS queue skip missing file: %s", p)
        return
    _ensure_worker()
    _mark_busy()
    _PLAY_QUEUE.put(p)


def clear_tts_queue() -> None:
    """Stop current playback and drop pending chunks."""
    from jarvis.audio_device import stop_playback

    global _PENDING
    stop_playback()
    drained = 0
    while True:
        try:
            _PLAY_QUEUE.get_nowait()
            drained += 1
        except queue.Empty:
            break
    with _PENDING_LOCK:
        _PENDING = max(0, _PENDING - drained)
        if _PENDING == 0:
            _IDLE.set()


def wait_tts_idle(timeout: float | None = 30.0) -> bool:
    """Block until queued playback finishes."""
    if timeout is None:
        _IDLE.wait()
        return True
    return _IDLE.wait(timeout)


def tts_queue_busy() -> bool:
    return not _IDLE.is_set()
