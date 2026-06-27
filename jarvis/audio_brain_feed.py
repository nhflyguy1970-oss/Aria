"""Debounced auto-feed from audio transcripts into brain memory."""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path

log = logging.getLogger("jarvis.audio_brain_feed")

_LOCK = threading.Lock()
_LAST_FEED: dict[str, float] = {}
_DEBOUNCE_SEC = float(__import__("os").getenv("JARVIS_AUDIO_FEED_DEBOUNCE", "60"))


def _enabled() -> bool:
    from jarvis.brain_memory import auto_audio_learn_enabled

    return auto_audio_learn_enabled()


def maybe_feed_transcript(memory, transcript: str, audio_path: str = "") -> None:
    """Schedule debounced transcript → brain learning (non-blocking)."""
    text = (transcript or "").strip()
    if not _enabled() or memory is None or len(text) < 20:
        return
    key = f"{Path(audio_path).name}:{text[:80]}"
    now = time.monotonic()
    with _LOCK:
        if now - _LAST_FEED.get(key, 0.0) < _DEBOUNCE_SEC:
            return
        _LAST_FEED[key] = now

    threading.Thread(
        target=_feed_worker,
        args=(memory, text, audio_path),
        daemon=True,
        name="audio-brain-feed",
    ).start()


def _feed_worker(memory, transcript: str, audio_path: str) -> None:
    try:
        from jarvis.journal_learning import extract_and_store

        label = Path(audio_path).name if audio_path else "recording"
        extract_and_store(
            memory,
            f"Audio transcript ({label}):\n{transcript[:2500]}",
            project="main",
        )
    except Exception as exc:
        log.debug("Audio brain feed skipped: %s", exc)
