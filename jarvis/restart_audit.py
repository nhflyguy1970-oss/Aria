"""Append-only audit log for server restart requests (who/why)."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

logger = logging.getLogger("jarvis.restart_audit")
AUDIT_FILE = DATA_DIR / "logs" / "restart_audit.jsonl"


def log_restart_event(source: str, **extra: Any) -> None:
    """Record a restart trigger. source: api | cli | tray | watchdog | flag | unknown."""
    entry = {
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "source": source,
        **{k: v for k, v in extra.items() if v is not None},
    }
    try:
        AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with AUDIT_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, default=str) + "\n")
    except OSError as exc:
        logger.warning("Could not write restart audit: %s", exc)
    logger.info("Restart requested via %s %s", source, extra or "")
