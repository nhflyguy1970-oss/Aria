"""Serialize GPU-heavy audio work (Whisper, MusicGen, song studio)."""

from __future__ import annotations

import logging
import os
import threading
import time
from contextlib import contextmanager

log = logging.getLogger("jarvis.audio_work")

_lock = threading.Lock()
_holder: str | None = None
_since = 0.0


@contextmanager
def audio_gpu_slot(label: str = "audio"):
    """One GPU-heavy audio pipeline at a time (Whisper + MusicGen + songs)."""
    global _holder, _since
    timeout = float(os.getenv("JARVIS_AUDIO_GPU_WAIT_SEC", "900"))
    deadline = time.time() + timeout
    while time.time() < deadline:
        with _lock:
            if _holder is None:
                _holder = label
                _since = time.time()
                break
        time.sleep(0.25)
    else:
        raise TimeoutError(f"Audio GPU busy (current: {_holder or 'unknown'})")
    try:
        yield
    finally:
        with _lock:
            if _holder == label:
                _holder = None


def audio_gpu_status() -> dict:
    with _lock:
        return {
            "busy": _holder is not None,
            "label": _holder or "",
            "since": _since if _holder else 0.0,
        }
