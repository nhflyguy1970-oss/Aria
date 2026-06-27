"""AI-curated news briefing (DDG + optional LLM pick)."""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any

from jarvis.feature_flags import curated_news_enabled

log = logging.getLogger("jarvis")

_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL = 15 * 60
_DDGS_SKIP_REASON = "duckduckgo-search not installed"


def _ddgs_available() -> bool:
    from jarvis.ddgs_install import ddgs_importable

    return ddgs_importable()


def _fetch_raw_ddgs() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS

        ddgs = DDGS()
        for query, category in (
            ("top news", "Top Stories"),
            ("technology news", "Technology"),
            ("stock market news", "Markets"),
            ("science breakthrough", "Science"),
            ("culture arts news", "Culture"),
        ):
            for r in ddgs.news(query, max_results=5):
                rows.append(
                    {
                        "title": r.get("title") or "",
                        "url": r.get("url") or "",
                        "body": (r.get("body") or "")[:240],
                        "source": r.get("source") or "",
                        "category": category,
                    }
                )
    except Exception as exc:
        log.debug("curated news DDGS fetch failed: %s", exc)
    return rows


def _fetch_raw_rss_fallback() -> list[dict[str, str]]:
    """Google News RSS fallback when DDGS is unavailable (mirrors briefing_news)."""
    from jarvis.briefing_news import _fetch_bytes, _filter_quality_headlines, _google_news_rss, _parse_google_news_rss

    payload = _fetch_bytes(_google_news_rss()) or b""
    hits = _filter_quality_headlines(
        _parse_google_news_rss(payload, limit=12),
        max_age_days=3,
    )
    return [
        {
            "title": item.get("title") or "",
            "url": item.get("url") or "",
            "body": "",
            "source": item.get("source") or "",
            "category": "Top Stories",
        }
        for item in hits
    ]


def _fetch_raw() -> tuple[list[dict[str, str]], str | None]:
    if not _ddgs_available():
        rss = _fetch_raw_rss_fallback()
        if rss:
            return rss, f"{_DDGS_SKIP_REASON} (RSS fallback)"
        return [], _DDGS_SKIP_REASON
    rows = _fetch_raw_ddgs()
    if rows:
        return rows, None
    rss = _fetch_raw_rss_fallback()
    if rss:
        return rss, "DDGS returned no results (RSS fallback)"
    return [], None


def _curate_with_llm(raw: list[dict[str, str]], *, limit: int = 6) -> list[dict[str, str]]:
    if not raw:
        return []
    try:
        from jarvis.llm import ask_with_system

        titles = "\n".join(
            f"{i+1}. [{r.get('category')}] {r.get('title')} — {r.get('body', '')[:120]}"
            for i, r in enumerate(raw[:15])
        )
        prompt = (
            "Pick the best news stories for a daily briefing. "
            f"Return JSON array of up to {limit} objects with keys: index (1-based from list), reason (short). "
            "Prefer diverse, substantive stories.\n\n" + titles
        )
        text = ask_with_system(
            os.getenv("JARVIS_CHAT_MODEL", "qwen3:4b"),
            "You return only valid JSON arrays.",
            prompt,
            temperature=0.3,
        )
        start = text.find("[")
        end = text.rfind("]") + 1
        if start < 0 or end <= start:
            return raw[:limit]
        picks = json.loads(text[start:end])
        out: list[dict[str, str]] = []
        for pick in picks:
            idx = int(pick.get("index", 0)) - 1
            if 0 <= idx < len(raw):
                item = dict(raw[idx])
                item["reason"] = pick.get("reason", "")
                out.append(item)
        return out or raw[:limit]
    except Exception as exc:
        log.debug("curated news LLM failed: %s", exc)
        return raw[:limit]


def get_curated_headlines(
    *,
    use_ai: bool = True,
    force_refresh: bool = False,
    category: str = "",
) -> dict[str, Any]:
    if not curated_news_enabled():
        return {"enabled": False, "headlines": [], "curated": False}

    cat_key = (category or "").strip().lower()
    key = f"{'ai' if use_ai else 'raw'}:{cat_key or 'all'}"
    if not force_refresh and key in _CACHE:
        ts, data = _CACHE[key]
        if time.time() - ts < _CACHE_TTL:
            return dict(data)

    raw, skipped = _fetch_raw()
    if cat_key and cat_key != "all":
        label = cat_key.title()
        if label == "Top Stories":
            filtered = [r for r in raw if r.get("category") == "Top Stories"]
        else:
            filtered = [r for r in raw if (r.get("category") or "").lower() == cat_key]
        raw = filtered or raw
    headlines = _curate_with_llm(raw, limit=6) if use_ai and raw else raw[:8]
    breaking = headlines[0] if headlines else None
    payload: dict[str, Any] = {
        "enabled": True,
        "curated": bool(use_ai),
        "category": category or "all",
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "headlines": headlines,
        "breaking": breaking,
        "categories": ["Top Stories", "Technology", "Markets", "Science", "Culture"],
        "skipped": skipped,
        "ddgs_available": _ddgs_available(),
    }
    _CACHE[key] = (time.time(), payload)
    return dict(payload)


def format_curated_markdown(*, use_ai: bool = True) -> str:
    data = get_curated_headlines(use_ai=use_ai)
    if not data.get("enabled"):
        return "Curated news is disabled."
    if data.get("skipped") and not data.get("headlines"):
        return f"Curated news unavailable: {data['skipped']}"
    lines = ["## Curated briefing"]
    for i, h in enumerate(data.get("headlines") or [], 1):
        title = h.get("title", "Story")
        cat = h.get("category", "")
        reason = h.get("reason", "")
        url = h.get("url", "")
        line = f"{i}. **{title}**"
        if cat:
            line += f" _{cat}_"
        if reason:
            line += f" — {reason}"
        if url:
            line += f" ([link]({url}))"
        lines.append(line)
    if len(lines) == 1:
        if data.get("skipped"):
            lines.append(f"_{data['skipped']}_")
        else:
            lines.append("_No headlines fetched._")
    return "\n".join(lines)
