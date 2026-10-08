"""Append-only source history for chat branches.

A Conversation's `messages` list is the bounded context sent to models, and it
is pruned to MAX_MESSAGES / MAX_CONTEXT_CHARS. Before this archive existed the
same pruned list was all chat_branches.json kept, so every turn that fell out
of the context window was gone for good.

This module keeps the complete record separately: one JSON line per event, per
branch, written before the context is pruned. It records what was said, not
whether it was true — promoting anything from here into memory remains the job
of ACM and its candidate review.

Events:
  message    a user or assistant turn, verbatim
  seed       a turn copied from the branch store when the archive was first
             opened — older turns that had already been pruned are not
             recoverable from there and are not invented
  retracted  the last user turn was withdrawn from the context (cancel/stale)
  truncated  the last assistant turn was cut short in the context (barge-in)
  cleared    the user cleared the branch's visible history
  deleted    the branch was deleted

Nothing here rewrites or removes earlier lines.
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger("jarvis.conversation_archive")

ARCHIVE_DIRNAME = "conversation_archive"
ARCHIVED_ROLES = ("user", "assistant")

_lock = threading.Lock()
_status: dict[str, Any] = {"writes": 0, "errors": 0, "last_error": None}


def _safe_name(branch_id: str) -> str:
    name = re.sub(r"[^A-Za-z0-9_.-]", "_", branch_id or "main").strip(".")
    return name or "main"


class ConversationArchive:
    """The durable, append-only history of one branch."""

    def __init__(self, branch_id: str, root: Path | str):
        self.branch_id = branch_id or "main"
        self.root = Path(root)
        self.path = self.root / f"{_safe_name(self.branch_id)}.jsonl"

    def exists(self) -> bool:
        return self.path.is_file()

    def _append(self, event: dict[str, Any]) -> str:
        from jarvis.live_data_guard import assert_live_write_allowed

        event = {
            "id": uuid.uuid4().hex,
            "ts": datetime.now(timezone.utc).isoformat(),
            "branch": self.branch_id,
            **event,
        }
        line = json.dumps(event, ensure_ascii=False) + "\n"
        try:
            assert_live_write_allowed(self.path)
            with _lock:
                self.root.mkdir(parents=True, exist_ok=True)
                with open(self.path, "a", encoding="utf-8") as fh:
                    fh.write(line)
                    fh.flush()
                    os.fsync(fh.fileno())
                _status["writes"] += 1
        except Exception as exc:  # noqa: BLE001 - chat must continue; the loss must not be silent
            _status["errors"] += 1
            _status["last_error"] = f"{type(exc).__name__}: {exc}"
            log.error("Conversation archive write failed for %s: %s", self.path, exc)
            return ""
        return event["id"]

    def record(self, role: str, content: str) -> str:
        """Record one turn verbatim. Returns its event id ("" if it could not be written)."""
        if role not in ARCHIVED_ROLES:
            return ""
        return self._append({"kind": "message", "role": role, "content": str(content or "")})

    def mark(self, kind: str, **detail: Any) -> str:
        return self._append({"kind": kind, **detail})

    def seed(self, messages: list[dict[str, Any]], *, origin: str) -> int:
        """Copy turns from an existing store into a new archive, labelled by origin."""
        count = 0
        for message in messages:
            if message.get("role") not in ARCHIVED_ROLES:
                continue
            self._append(
                {
                    "kind": "seed",
                    "role": message.get("role"),
                    "content": str(message.get("content") or ""),
                    "origin": origin,
                }
            )
            count += 1
        return count

    def read(self) -> list[dict[str, Any]]:
        """Every event, oldest first. A corrupt line is reported, never dropped silently."""
        if not self.path.is_file():
            return []
        events: list[dict[str, Any]] = []
        with open(self.path, encoding="utf-8") as fh:
            for number, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    events.append({"kind": "unreadable", "line": number})
        return events

    def turns(self) -> list[dict[str, Any]]:
        """The user/assistant turns (seeded and live), oldest first."""
        return [e for e in self.read() if e.get("kind") in ("message", "seed")]


def status() -> dict[str, Any]:
    """Write counters for health/diagnostics: errors here mean history is at risk."""
    return dict(_status)
