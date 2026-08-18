"""Browser session registry — identity, ownership, lifecycle, bounds.

ARIA already owns exactly one Playwright browser thread
(jarvis.browser_product.session). This layer does not launch a second browser:
it tracks logical sessions over that single stack, so a mission or agent can be
attributed, bounded and isolated without spawning browser processes per task.

Isolation is by ownership, not by process: a session records who owns it, and
the engine refuses cross-owner use. That is deliberate — uncontrolled profile
proliferation is what produced the thousands of Playwright files in earlier
milestones.
"""

from __future__ import annotations

import threading
import time
import uuid
from typing import Any

from jarvis.computer_use.actions import LIMITS

# lifecycle
OPEN = "open"
CLOSED = "closed"
FAILED = "failed"

_lock = threading.RLock()
_sessions: dict[str, dict[str, Any]] = {}


class SessionError(RuntimeError):
    """Session does not exist, is closed, or belongs to another owner."""


def create(*, owner: str = "", task_id: str = "", label: str = "") -> dict[str, Any]:
    with _lock:
        sid = f"cus_{uuid.uuid4().hex[:10]}"
        now = time.time()
        _sessions[sid] = {
            "id": sid,
            "owner": owner or "unattributed",
            "task_id": task_id,
            "label": label,
            "state": OPEN,
            "url": "",
            "title": "",
            "created_at": now,
            "last_activity": now,
            "actions": 0,
            "screenshots": 0,
            "error": None,
        }
        return dict(_sessions[sid])


def get(session_id: str) -> dict[str, Any] | None:
    with _lock:
        s = _sessions.get(session_id)
        return dict(s) if s else None


def list_sessions(*, include_closed: bool = False) -> list[dict[str, Any]]:
    with _lock:
        items = [dict(s) for s in _sessions.values()]
    items.sort(key=lambda s: s["created_at"])
    return [s for s in items if include_closed or s["state"] == OPEN]


def require(session_id: str, *, owner: str = "") -> dict[str, Any]:
    """Fetch a usable session, enforcing ownership and bounds."""
    with _lock:
        session = _sessions.get(session_id)
        if not session:
            raise SessionError(f"No such browser session: {session_id}")
        if session["state"] != OPEN:
            raise SessionError(f"Browser session is {session['state']}: {session_id}")
        if owner and session["owner"] not in ("unattributed", owner):
            raise SessionError(
                f"Session {session_id} belongs to {session['owner']!r}, not {owner!r}"
            )
        if time.time() - session["created_at"] > LIMITS["session_ttl_s"]:
            session["state"] = CLOSED
            session["error"] = "session expired"
            raise SessionError(f"Browser session expired: {session_id}")
        if session["actions"] >= LIMITS["max_actions_per_session"]:
            raise SessionError(
                f"Session {session_id} reached max_actions_per_session "
                f"({LIMITS['max_actions_per_session']})"
            )
        return dict(session)


def record_action(session_id: str, *, action: str, url: str = "", title: str = "") -> None:
    with _lock:
        session = _sessions.get(session_id)
        if not session:
            return
        session["actions"] += 1
        if action == "screenshot":
            session["screenshots"] += 1
        if url:
            session["url"] = url
        if title:
            session["title"] = title
        session["last_activity"] = time.time()


def may_screenshot(session_id: str) -> bool:
    with _lock:
        session = _sessions.get(session_id)
        if not session:
            return False
        return session["screenshots"] < LIMITS["max_screenshots_per_session"]


def fail(session_id: str, error: str) -> None:
    with _lock:
        session = _sessions.get(session_id)
        if session:
            session["state"] = FAILED
            session["error"] = error[:500]
            session["last_activity"] = time.time()


def close(session_id: str) -> bool:
    with _lock:
        session = _sessions.get(session_id)
        if not session or session["state"] == CLOSED:
            return False
        session["state"] = CLOSED
        session["last_activity"] = time.time()
        return True


def reset() -> None:
    """Drop registry state (tests / process restart)."""
    with _lock:
        _sessions.clear()


def reap_expired() -> list[str]:
    """Close sessions past their TTL so a dead task cannot hold one forever."""
    closed = []
    now = time.time()
    with _lock:
        for sid, session in _sessions.items():
            if session["state"] == OPEN and now - session["created_at"] > LIMITS["session_ttl_s"]:
                session["state"] = CLOSED
                session["error"] = "session expired"
                closed.append(sid)
    return closed
