"""Search + browse bridge and shopping templates."""

from __future__ import annotations

import re
from typing import Any

from jarvis.p2_flags import browser_agent_enabled


def pick_url_from_search(query: str | None = None, *, max_results: int = 5) -> str:
    from jarvis.web_search import search

    results = search(query or "", limit=max_results) or []
    for row in results:
        url = (row.get("url") or row.get("href") or "").strip()
        if url.startswith("http"):
            return url
    return ""


def search_and_browse(query: str | None = None, *, allow_risky: bool = False) -> dict[str, Any]:
    if not browser_agent_enabled():
        return {"ok": False, "message": "Browser agent disabled"}
    url = pick_url_from_search(query)
    if not url:
        return {"ok": False, "message": f"No URL found for: {query}"}
    from jarvis.browser_agent import navigate

    result = navigate(url, allow_risky=allow_risky)
    result["query"] = query
    result["picked_url"] = url
    return result


def parse_shopping_query(message: str | None = None) -> dict[str, Any] | None:
    """Find X under $Y on site Z."""
    text = (message or "").strip()
    if not text:
        return None
    m = re.search(
        r"(?:find|search for|look for)\s+(.+?)\s+(?:under|below|less than)\s+\$?(\d+(?:\.\d+)?)\s+(?:on|at)\s+(.+)$",
        text,
        re.I,
    )
    if not m:
        return None
    return {
        "item": m.group(1).strip(),
        "max_price": float(m.group(2)),
        "site": m.group(3).strip().rstrip("."),
        "query": f"{m.group(1).strip()} site:{m.group(3).strip()}",
    }


def shopping_search(message: str | None = None) -> dict[str, Any]:
    spec = parse_shopping_query(message)
    if not spec:
        return {"ok": False, "message": "Could not parse shopping query"}
    site = spec["site"]
    if not site.startswith("http"):
        host = site.replace("www.", "").split("/")[0]
        if "." not in host:
            host = f"{host}.com"
        site = f"https://{host}"
    query = f"{spec['item']} {site}"
    return search_and_browse(query)


def is_risky_url(url: str | None = None) -> bool:
    from jarvis.browser_agent import _check_url_safe

    ok, _ = _check_url_safe(url or "", allow_risky=False)
    return not ok
