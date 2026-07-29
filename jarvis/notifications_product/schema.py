"""Versioned notification event schema — chrome/attention only; never secrets."""

from __future__ import annotations

import time
import uuid
from copy import deepcopy
from typing import Any

SCHEMA_VERSION = 1

SEVERITY_PRIORITY = {
    "critical": 4,
    "error": 3,
    "warning": 2,
    "info": 1,
    "success": 0,
}

SENSITIVE_KEYS = (
    "password",
    "token",
    "secret",
    "api_key",
    "apikey",
    "authorization",
    "cookie",
)


def _is_sensitive_key(key: str) -> bool:
    low = str(key).lower().replace("-", "_")
    if low in SENSITIVE_KEYS:
        return True
    if low.endswith("_token") or low.endswith("_secret") or low.endswith("_password"):
        return True
    if "api_key" in low or low == "pin":
        return True
    return False



def _uid() -> str:
    return f"ntf_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"


def map_tone(tone: str | None) -> str:
    t = str(tone or "").lower()
    if t in ("err", "error"):
        return "error"
    if t in ("warn", "warning"):
        return "warning"
    if t in ("ok", "success"):
        return "success"
    if t == "critical":
        return "critical"
    return "info"


def empty_event(**overrides: Any) -> dict[str, Any]:
    now = time.time()
    base = {
        "schema_version": SCHEMA_VERSION,
        "id": _uid(),
        "timestamp": now,
        "severity": "info",
        "priority": 1,
        "source": "system",
        "category": "system",
        "type": "event",
        "title": "Notification",
        "summary": "",
        "detail": "",
        "actions": ["mark_read", "dismiss"],
        "deepLink": "",
        "muted": False,
        "snoozedUntil": 0,
        "groupId": "",
        "correlationId": "",
        "digest": True,
        "voice": False,
        "desktop": True,
        "toast": False,
        "read": False,
        "pinned": False,
        "dismissed": False,
        "resolved": False,
        "metadata": {},
        "product": "",
    }
    base.update(overrides)
    return base


def normalize_event(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize any producer payload into the unified schema."""
    raw = raw or {}
    # Strip secrets
    clean = {k: v for k, v in raw.items() if not _is_sensitive_key(k)}
    severity = str(
        clean.get("severity") or map_tone(clean.get("tone")) or "info"
    ).lower()
    if severity not in SEVERITY_PRIORITY:
        severity = "info"
    category = str(clean.get("category") or clean.get("kind") or clean.get("product") or "system").lower()
    source = str(clean.get("source") or category or "system")
    title = str(clean.get("title") or clean.get("message") or "Notification")[:200]
    summary = str(clean.get("summary") or clean.get("message") or clean.get("detail") or "")[:280]
    detail = str(clean.get("detail") or clean.get("summary") or clean.get("message") or "")[:4000]
    deep = str(clean.get("deepLink") or clean.get("deeplink") or clean.get("fix") or "")
    # fix field from models is a deepLink hint, not an action label
    if deep in ("Open Gallery", "Open Browser"):
        deep = category if category in ("gallery", "browser") else deep
    if str(clean.get("fix") or "").startswith("mc:") or str(clean.get("fix") or "").startswith("models:"):
        deep = str(clean.get("fix"))
    ts = clean.get("timestamp") or clean.get("ts") or time.time()
    try:
        ts = float(ts)
        if ts > 1e12:  # ms
            ts = ts / 1000.0
    except Exception:
        ts = time.time()
    actions = clean.get("actions")
    if not isinstance(actions, list) or not actions:
        actions = ["mark_read", "ask_aria", "dismiss"]
        if deep:
            actions.insert(0, "open")
    meta = clean.get("metadata") if isinstance(clean.get("metadata"), dict) else {}
    if isinstance(clean.get("detail"), dict):
        meta = {**meta, **clean["detail"]}
        detail = summary or title
    evt = empty_event(
        id=str(clean.get("id") or _uid()),
        timestamp=ts,
        severity=severity,
        priority=int(clean.get("priority") if clean.get("priority") is not None else SEVERITY_PRIORITY[severity]),
        source=source,
        category=category,
        type=str(clean.get("type") or clean.get("kind") or "event").lower(),
        title=title,
        summary=summary,
        detail=detail,
        actions=list(actions),
        deepLink=deep,
        muted=bool(clean.get("muted")),
        snoozedUntil=int(clean.get("snoozedUntil") or 0) or 0,
        groupId=str(clean.get("groupId") or ""),
        correlationId=str(clean.get("correlationId") or clean.get("groupId") or ""),
        digest=bool(clean.get("digest", True)),
        voice=bool(clean.get("voice", False)),
        desktop=bool(clean.get("desktop", True)),
        toast=bool(clean.get("toast", False)),
        read=bool(clean.get("read")),
        pinned=bool(clean.get("pinned")),
        dismissed=bool(clean.get("dismissed")),
        resolved=bool(clean.get("resolved")),
        metadata=meta,
        product=str(clean.get("product") or category or ""),
    )
    # Legacy mirrors for Activity Center client
    evt["tone"] = (
        "err"
        if severity in ("error", "critical")
        else "warn"
        if severity == "warning"
        else "ok"
        if severity == "success"
        else "info"
    )
    evt["kind"] = category
    evt["ts"] = int(ts * 1000) if ts < 1e12 else int(ts)
    evt["version"] = 2  # Activity Center client schema version
    return evt


def validate_event(evt: dict[str, Any] | None) -> list[str]:
    errors: list[str] = []
    if not isinstance(evt, dict):
        return ["not_an_object"]
    if not str(evt.get("title") or "").strip():
        errors.append("missing_title")
    sev = str(evt.get("severity") or "")
    if sev and sev not in SEVERITY_PRIORITY:
        errors.append("invalid_severity")
    for key in evt:
        if _is_sensitive_key(key):
            errors.append(f"sensitive_field:{key}")
    try:
        if int(evt.get("schema_version") or 0) > SCHEMA_VERSION:
            errors.append("schema_too_new")
    except Exception:
        errors.append("schema_version_invalid")
    return errors


def migrate_event(raw: dict[str, Any] | None) -> dict[str, Any]:
    return normalize_event(raw)


def to_activity_payload(evt: dict[str, Any]) -> dict[str, Any]:
    """Shape expected by Aria Activity Center client store."""
    e = normalize_event(evt)
    return {
        "id": e["id"],
        "version": 2,
        "timestamp": int(e["timestamp"] * 1000) if e["timestamp"] < 1e12 else int(e["timestamp"]),
        "severity": e["severity"],
        "priority": e["priority"],
        "category": e["category"],
        "source": e["source"],
        "type": e["type"],
        "title": e["title"],
        "summary": e["summary"],
        "detail": e["detail"],
        "deepLink": e["deepLink"],
        "actions": e["actions"],
        "read": e["read"],
        "pinned": e["pinned"],
        "muted": e["muted"],
        "dismissed": e["dismissed"],
        "snoozedUntil": e["snoozedUntil"],
        "groupId": e["groupId"] or e["correlationId"],
        "metadata": {
            **(e.get("metadata") or {}),
            "schema_version": SCHEMA_VERSION,
            "product": e.get("product") or "",
            "resolved": e.get("resolved"),
            "digest": e.get("digest"),
            "notifications_id": e["id"],
        },
        "tone": e["tone"],
        "kind": e["kind"],
        "ts": e["ts"],
    }
