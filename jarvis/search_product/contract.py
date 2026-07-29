"""Shared SearchResult contract — one schema for every corpus."""

from __future__ import annotations

import hashlib
from typing import Any


REQUIRED_FIELDS = (
    "id",
    "source",
    "source_label",
    "title",
    "summary",
    "preview",
    "location",
    "score",
    "confidence",
    "open",
    "metadata",
)


def _clip(text: Any, n: int = 400) -> str:
    s = ("" if text is None else str(text)).strip().replace("\n", " ")
    return s[:n]


def make_result(
    *,
    source: str,
    source_label: str,
    title: str,
    summary: str = "",
    preview: str = "",
    location: str = "",
    score: float = 0.5,
    confidence: float | None = None,
    strategy: str = "keyword",
    open_action: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    highlights: list[str] | None = None,
    icon: str = "",
    result_id: str = "",
) -> dict[str, Any]:
    """Normalize any corpus hit into the shared SearchResult contract."""
    title_s = _clip(title, 160) or "Untitled"
    summary_s = _clip(summary or preview, 280)
    preview_s = _clip(preview or summary, 400)
    loc = _clip(location, 240)
    sc = max(0.0, min(1.0, float(score or 0.0)))
    conf = float(confidence) if confidence is not None else min(0.99, sc * 0.92 + 0.05)
    conf = max(0.0, min(1.0, conf))
    open_payload = dict(open_action or {})
    if "view" not in open_payload and source:
        open_payload.setdefault("view", _default_view(source))
    meta = dict(metadata or {})
    rid = result_id or _stable_id(source, title_s, loc)
    return {
        "id": rid,
        "source": source,
        "source_label": source_label,
        "title": title_s,
        "summary": summary_s,
        "preview": preview_s,
        "location": loc,
        "score": round(sc, 4),
        "confidence": round(conf, 4),
        "strategy": strategy,
        "open": open_payload,
        "metadata": meta,
        "highlights": list(highlights or []),
        "icon": icon or source,
    }


def _stable_id(source: str, title: str, location: str) -> str:
    raw = f"{source}|{title}|{location}".encode("utf-8", errors="ignore")
    return hashlib.sha1(raw).hexdigest()[:16]


def _default_view(source: str) -> str:
    return {
        "documents": "documents",
        "memory": "memory",
        "projects": "projects",
        "journal": "journal",
        "code": "coding",
        "graph": "connections",
        "connections": "connections",
        "audio": "audio",
        "web": "chat",
        "planner": "planner",
        "calendar": "calendar",
        "gallery": "gallery",
        "home_assistant": "workstation",
        "flytying": "flytying",
        "automation": "automation",
        "learned": "documents",
    }.get(source, "search")


def validate_result(hit: dict[str, Any]) -> bool:
    return isinstance(hit, dict) and all(k in hit for k in REQUIRED_FIELDS)


def to_legacy_hit(result: dict[str, Any]) -> dict[str, Any]:
    """Map SearchResult → knowledge.search legacy hit shape for chat/palette compat."""
    return {
        "source_type": result.get("source") or "unknown",
        "source_label": result.get("source_label") or result.get("source"),
        "title": result.get("title") or "untitled",
        "excerpt": result.get("preview") or result.get("summary") or "",
        "location": result.get("location") or "",
        "strategy": result.get("strategy") or "federated",
        "score": float(result.get("score") or 0.5),
        "raw": {
            "id": result.get("id"),
            "open": result.get("open"),
            "confidence": result.get("confidence"),
            "metadata": result.get("metadata") or {},
        },
    }


def from_legacy_hit(hit: dict[str, Any], *, source: str = "", source_label: str = "") -> dict[str, Any]:
    src = source or str(hit.get("source_type") or "unknown")
    label = source_label or str(hit.get("source_label") or src)
    return make_result(
        source=src,
        source_label=label,
        title=str(hit.get("title") or "untitled"),
        summary=str(hit.get("excerpt") or ""),
        preview=str(hit.get("excerpt") or ""),
        location=str(hit.get("location") or ""),
        score=float(hit.get("score") or 0.5),
        strategy=str(hit.get("strategy") or "legacy"),
        open_action={"view": _default_view(src), "query": "", "location": hit.get("location")},
        metadata={"legacy": True, "raw": hit.get("raw")},
    )
