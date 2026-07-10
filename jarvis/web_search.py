"""Web search — ddgs (DuckDuckGo) with optional local SearXNG and HTML fallback."""

from __future__ import annotations

import json
import logging
import os
import re
import time
import urllib.parse
import urllib.request
from html import unescape

log = logging.getLogger("jarvis")

_USER_AGENT = "Mozilla/5.0 (compatible; Jarvis/3.2; +https://github.com/jarvis)"


def searxng_url() -> str:
    return os.getenv("JARVIS_SEARXNG_URL", "http://127.0.0.1:8080").rstrip("/")


def searxng_available() -> bool:
    try:
        params = urllib.parse.urlencode({"q": "test", "format": "json"})
        req = urllib.request.Request(
            f"{searxng_url()}/search?{params}",
            headers={"User-Agent": _USER_AGENT},
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def _ddgs_installed() -> bool:
    try:
        import ddgs  # noqa: F401
        return True
    except ImportError:
        return False


def _legacy_ddg_installed() -> bool:
    try:
        import duckduckgo_search  # noqa: F401
        return True
    except ImportError:
        return False


def backend_name() -> str:
    if searxng_available():
        return "SearXNG (local)"
    if _ddgs_installed():
        return "DuckDuckGo (ddgs)"
    if _legacy_ddg_installed():
        return "DuckDuckGo (legacy)"
    return "DuckDuckGo HTML"


def is_available() -> bool:
    """True if any search backend is usable."""
    return searxng_available() or _ddgs_installed() or _legacy_ddg_installed() or True


def search(query: str, limit: int = 5) -> list[dict]:
    if not query.strip():
        return []
    limit = max(1, min(int(limit), 10))

    if searxng_available():
        results = _searxng_search(query, limit)
        if results:
            return results

    for attempt in range(2):
        results = _ddgs_package_search(query, limit, prefer_new=True)
        if results:
            return results
        results = _ddgs_package_search(query, limit, prefer_new=False)
        if results:
            return results
        if attempt == 0:
            time.sleep(0.4)

    results = _ddg_html_search(query, limit)
    if results:
        return results

    return _duckduckgo_api_fallback(query, limit)


def _normalize_hit(title: str, url: str, snippet: str) -> dict:
    return {
        "title": (title or "Result").strip(),
        "url": (url or "").strip(),
        "snippet": (snippet or "")[:400],
    }


def _ddgs_package_search(query: str, limit: int, *, prefer_new: bool) -> list[dict]:
    try:
        if prefer_new:
            from ddgs import DDGS
        else:
            from duckduckgo_search import DDGS
    except ImportError:
        return []

    results: list[dict] = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=limit):
                results.append(_normalize_hit(
                    r.get("title", ""),
                    r.get("href", r.get("link", "")),
                    r.get("body", r.get("snippet", "")),
                ))
    except Exception as exc:
        log.debug("DDG package search failed (%s): %s", "ddgs" if prefer_new else "legacy", exc)
        return []
    return results


def _ddg_html_search(query: str, limit: int) -> list[dict]:
    """POST to DuckDuckGo HTML lite (no API key; reliable fallback)."""
    try:
        body = urllib.parse.urlencode({"q": query}).encode()
        req = urllib.request.Request(
            "https://html.duckduckgo.com/html/",
            data=body,
            headers={
                "User-Agent": _USER_AGENT,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        log.debug("DDG HTML search failed: %s", exc)
        return []

    pairs = re.findall(
        r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
        html,
        flags=re.S,
    )
    snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</', html, flags=re.S)
    results: list[dict] = []
    for i, (url, title_html) in enumerate(pairs[:limit]):
        title = re.sub(r"<[^>]+>", "", title_html)
        title = unescape(title).strip()
        snippet = ""
        if i < len(snippets):
            snippet = re.sub(r"<[^>]+>", "", snippets[i])
            snippet = unescape(snippet).strip()
        if title or url:
            results.append(_normalize_hit(title, url, snippet))
    return results


def _searxng_search(query: str, limit: int) -> list[dict]:
    try:
        params = urllib.parse.urlencode({"q": query, "format": "json", "language": "en"})
        req = urllib.request.Request(
            f"{searxng_url()}/search?{params}",
            headers={"User-Agent": _USER_AGENT},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for r in data.get("results", [])[:limit]:
                results.append(_normalize_hit(
                    r.get("title", ""),
                    r.get("url", ""),
                    r.get("content", r.get("snippet", "")),
                ))
            return results
    except Exception as exc:
        log.debug("SearXNG search failed: %s", exc)
        return []


def _duckduckgo_api_fallback(query: str, limit: int) -> list[dict]:
    try:
        params = urllib.parse.urlencode({"q": query, "format": "json", "no_html": "1"})
        req = urllib.request.Request(
            f"https://api.duckduckgo.com/?{params}",
            headers={"User-Agent": _USER_AGENT},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            results = []
            if data.get("AbstractText"):
                results.append(_normalize_hit(
                    data.get("Heading", query),
                    data.get("AbstractURL", ""),
                    data.get("AbstractText", ""),
                ))
            for t in data.get("RelatedTopics", [])[: limit - 1]:
                if isinstance(t, dict) and t.get("Text"):
                    results.append(_normalize_hit(
                        t.get("Text", "")[:80],
                        t.get("FirstURL", ""),
                        t.get("Text", ""),
                    ))
            return results[:limit]
    except Exception as exc:
        log.debug("DDG instant answer API failed: %s", exc)
        return []


def format_results(results: list[dict]) -> str:
    if not results:
        return (
            "No web results found. Try again in a moment, or run:\n"
            "`./venv/bin/pip install ddgs`"
        )
    lines = [f"**Web search results** ({backend_name()}):\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. **{r.get('title', 'Result')}**")
        if r.get("url"):
            lines.append(f"   {r['url']}")
        if r.get("snippet"):
            lines.append(f"   {r['snippet']}")
        lines.append("")
    return "\n".join(lines)


def format_results_for_llm(results: list[dict]) -> str:
    lines = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "Result")
        url = r.get("url", "")
        snippet = r.get("snippet", "")
        lines.append(f"[{i}] {title}\nURL: {url}\n{snippet}")
    return "\n\n".join(lines)


def auto_search_enabled() -> bool:
    return os.getenv("JARVIS_AUTO_WEB_SEARCH", "1").lower() not in ("0", "false", "no", "off")


_AUTO_PATTERNS = (
    r"\b(who is|who was|what is|what are|when did|when was|where is|how much|how many)\b",
    r"\bhow (?:would|does|can|could) .+ work\b",
    r"\b(would|could|can|should) .+ work (?:for|with)\b",
    r"\b(latest|current|today|tonight|this week|right now|as of)\b",
    r"\b(news|headline|stock price|exchange rate|score|election|release date)\b",
    r"\b(weather|forecast)\b.*\b(in|for|at)\b",
    r"\b(movidius|vpu|tpu|npu|inference chip|accelerator)\b",
    r"\b20[2-3]\d\b",
)


def should_auto_search(message: str) -> bool:
    """Heuristic: factual / current-events questions benefit from web context."""
    from jarvis.runtime_routing import is_runtime_routing_question

    if is_runtime_routing_question(message):
        return False
    text = (message or "").strip()
    if len(text) < 8 or len(text) > 500:
        return False
    lower = text.lower()
    if re.search(r"\b(search (the )?web|web search|look up online|google)\b", lower):
        return False
    if re.search(r"\b(fix|code|python|file|function|class|import|git|memory|remember)\b", lower):
        return False
    if text.endswith("?"):
        return True
    return any(re.search(p, lower) for p in _AUTO_PATTERNS)


def _synthesis_messages(query: str, results: list[dict]) -> tuple[list[dict], str]:
    context = format_results_for_llm(results)
    system = (
        "You answer using ONLY the web search snippets below. "
        "Cite sources as [1], [2] matching the numbered results. "
        "If snippets are insufficient, say what is missing. Be concise and direct."
    )
    user = f"Question: {query}\n\nSearch results:\n{context}"
    sources = "\n".join(
        f"[{i}] {r.get('title', '')} — {r.get('url', '')}"
        for i, r in enumerate(results, 1) if r.get("url")
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ], sources


def synthesize_answer_stream(query: str, results: list[dict]):
    """Stream a summarized answer from search hits."""
    if not results:
        yield format_results([])
        return
    from jarvis import llm

    msgs, sources = _synthesis_messages(query, results)
    body: list[str] = []
    try:
        for chunk in llm.ask_stream(llm.general_model(), msgs):
            body.append(chunk)
            yield chunk
        if sources and "".join(body).strip():
            block = f"\n\n**Sources**\n{sources}"
            yield block
    except Exception as exc:
        log.warning("Web search synthesis failed: %s", exc)
        if not body:
            yield format_results(results)


def synthesize_answer(query: str, results: list[dict]) -> str:
    """Summarize search hits with citations."""
    if not results:
        return format_results([])
    return "".join(synthesize_answer_stream(query, results)).strip() or format_results(results)


def answer_with_web(query: str, limit: int = 5) -> tuple[str, list[dict]]:
    results = search(query, limit=limit)
    if not results:
        return "", []
    return synthesize_answer(query, results), results
