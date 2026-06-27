"""Debounced auto-learn from ingested documents when brain mode / flag is on."""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path

log = logging.getLogger("jarvis.document_brain_feed")

_LOCK = threading.Lock()
_LAST_LEARN: dict[str, float] = {}
_DEBOUNCE_SEC = float(__import__("os").getenv("JARVIS_DOCUMENT_LEARN_DEBOUNCE", "60"))


def auto_document_learn_enabled() -> bool:
    from jarvis.brain_memory import auto_document_learn_enabled as _enabled

    return _enabled()


def maybe_auto_learn_document(memory, path: str, *, title: str = "") -> None:
    """Schedule debounced learn_from_file after ingest/upload (non-blocking)."""
    if not auto_document_learn_enabled() or memory is None:
        return
    resolved = str(Path(path).resolve())
    now = time.monotonic()
    with _LOCK:
        last = _LAST_LEARN.get(resolved, 0.0)
        if now - last < _DEBOUNCE_SEC:
            return
        _LAST_LEARN[resolved] = now

    def _run() -> None:
        try:
            from jarvis.document_learning import learn_from_file

            result = learn_from_file(memory, resolved, ingest=False)
            if result.ok:
                log.info("Auto-learned %s lesson(s) from %s", len(result.lessons), title or path)
            else:
                log.debug("Auto document learn skipped for %s: %s", path, result.message)
        except Exception as exc:
            log.debug("Auto document learn failed for %s: %s", path, exc)

    threading.Thread(target=_run, daemon=True, name="doc-auto-learn").start()
