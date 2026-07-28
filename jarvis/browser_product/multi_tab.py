"""Experimental multi-tab research — operator controlled."""

from __future__ import annotations

import time
from typing import Any

_TABS: list[dict[str, Any]] = []


def plan_research(goal: str, urls: list[str] | None = None) -> dict[str, Any]:
    urls = [u.strip() for u in (urls or []) if u.strip()][:5]
    tabs = [
        {
            "id": f"tab-{i+1}",
            "url": u,
            "status": "planned",
            "findings": "",
        }
        for i, u in enumerate(urls)
    ]
    if not tabs:
        tabs = [{"id": "tab-1", "url": "", "status": "planned", "findings": "", "note": "Add URLs"}]
    plan = {
        "goal": goal,
        "tabs": tabs,
        "created_at": time.time(),
        "message": "Multi-tab plan ready — operator must approve each navigation",
        "auto_run": False,
    }
    global _TABS
    _TABS = tabs
    return {"ok": True, **plan}


def list_tabs() -> dict[str, Any]:
    return {"ok": True, "tabs": list(_TABS)}


def run_tab(tab_id: str, *, allow_risky: bool = False, extract: bool = True) -> dict[str, Any]:
    """Navigate one planned tab — never fleets without operator calling per tab."""
    from jarvis import browser_agent as ba

    tab = next((t for t in _TABS if t.get("id") == tab_id), None)
    if not tab:
        return {"ok": False, "error": "Tab not found"}
    url = tab.get("url") or ""
    if not url:
        return {"ok": False, "error": "Tab has no URL"}
    nav = ba.navigate(url, allow_risky=allow_risky)
    if not nav.get("ok"):
        tab["status"] = "failed"
        tab["findings"] = nav.get("message") or ""
        return nav
    tab["status"] = "visited"
    findings = ""
    if extract:
        from jarvis.browser_product.session import extract_text

        ext = extract_text(limit=4000)
        findings = ext.get("text") or ""
        tab["findings"] = findings[:2000]
    return {"ok": True, "tab": tab, "navigate": nav}


def merge_findings() -> dict[str, Any]:
    parts = []
    for t in _TABS:
        if t.get("findings"):
            parts.append(f"## {t.get('url')}\n{t['findings'][:1500]}")
    merged = "\n\n".join(parts) or "(no findings yet)"
    return {"ok": True, "merged": merged, "tab_count": len(_TABS)}
