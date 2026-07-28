"""Browser fast routes."""

from __future__ import annotations

import re

from jarvis.router_table import RouteRule


def _search_browse_query(message: str) -> str:
    text = (message or "").strip()
    m = re.search(
        r"(?:search (?:the )?web for|find)\s+(.+?)(?:\s+and\s+(?:open|browse).*)?$",
        text,
        re.I,
    )
    if m:
        return m.group(1).strip(" .")
    return text


def browser_routes() -> list[RouteRule]:
    return [
        RouteRule(
            "browse_web",
            12,
            "browse url",
            lambda m, lower, _s: bool(re.search(r"\b(open|browse|go to)\s+(https?://|www\.)", lower)),
            lambda m: {
                "url": (
                    re.search(r"(https?://\S+|www\.\S+)", m, re.I).group(1).rstrip(".,)")
                    if re.search(r"(https?://\S+|www\.\S+)", m, re.I)
                    else ""
                )
            },
        ),
        RouteRule(
            "search_and_browse",
            12,
            "search browse",
            lambda m, lower, _s: bool(
                re.search(r"\b(search (the )?web for|find .+ and (open|browse))\b", lower)
            ),
            lambda m: {"query": _search_browse_query(m)},
        ),
        RouteRule(
            "browser_takeover",
            8,
            "browser takeover",
            lambda m, lower, _s: bool(re.search(r"\b(take over|takeover) (the )?browser\b", lower)),
        ),
        RouteRule(
            "browser_run_task",
            10,
            "browser agent task",
            lambda m, lower, _s: bool(
                re.search(r"\b(click|find|fill|press|select)\b.+\b(on the )?(page|site|browser)\b", lower)
                or re.search(r"\bbrowser agent\b", lower)
            ),
            lambda m: {"goal": m.strip()},
        ),
        RouteRule(
            "browser_summarize",
            9,
            "summarize page",
            lambda m, lower, _s: bool(re.search(r"\bsummarize (this |the )?page\b", lower)),
        ),
        RouteRule(
            "browser_voice",
            7,
            "voice browser",
            lambda m, lower, _s: bool(re.search(r"\b(pause|resume|stop) (the )?browser\b", lower)),
            lambda m: {"text": m.strip()},
        ),
    ]
