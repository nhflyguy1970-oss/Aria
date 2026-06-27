"""Playwright DOM agent — page snapshot → LLM → click/fill/navigate."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

log = logging.getLogger("jarvis.browser.dom")

_DOM_PROMPT = """You are a browser automation agent. Given the page snapshot and user goal, reply with ONLY one JSON object:
{{"action":"click","selector":"css selector","reason":"..."}}
{{"action":"fill","selector":"...","text":"...","reason":"..."}}
{{"action":"wait","ms":500}}
{{"action":"done","summary":"..."}}
{{"action":"fail","reason":"..."}}
Prefer stable selectors (#id, [name=], aria-label). Goal: {goal}

Page snapshot:
{snapshot}"""


def _parse_action(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if "```" in text:
        text = re.sub(r"```\w*\n?", "", text)
        text = text.replace("```", "")
    start = text.find("{")
    end = text.rfind("}") + 1
    if start < 0:
        return None
    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError:
        return None


def get_page_snapshot() -> dict[str, Any]:
    from jarvis.browser_agent import _PAGE

    if not _PAGE:
        return {"ok": False, "error": "No browser page"}
    try:
        title = _PAGE.title()
        url = _PAGE.url
        elements = _PAGE.evaluate(
            """() => {
              const out = [];
              const nodes = document.querySelectorAll('a, button, input, textarea, select, [role=button]');
              for (const el of Array.from(nodes).slice(0, 35)) {
                const text = (el.innerText || el.value || el.getAttribute('aria-label') || '').trim().slice(0, 80);
                if (!text && el.tagName !== 'INPUT') continue;
                out.push({
                  tag: el.tagName.toLowerCase(),
                  text,
                  id: el.id || '',
                  name: el.name || '',
                  type: el.type || '',
                  href: el.href ? el.href.slice(0, 120) : '',
                });
              }
              return out;
            }"""
        )
        return {"ok": True, "title": title, "url": url, "elements": elements or []}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _format_snapshot(snap: dict[str, Any]) -> str:
    lines = [f"URL: {snap.get('url', '')}", f"Title: {snap.get('title', '')}", "Elements:"]
    for el in snap.get("elements") or []:
        parts = [el.get("tag", "?")]
        if el.get("id"):
            parts.append(f"#{el['id']}")
        if el.get("name"):
            parts.append(f"name={el['name']}")
        if el.get("text"):
            parts.append(f'"{el["text"]}"')
        lines.append("- " + " ".join(parts))
    return "\n".join(lines)[:6000]


def dom_plan_step(goal: str, snapshot: dict[str, Any]) -> dict[str, Any]:
    from jarvis import llm

    prompt = _DOM_PROMPT.format(goal=goal[:300], snapshot=_format_snapshot(snapshot))
    try:
        raw = llm.ask_with_system(
            llm.general_model(),
            "You output only JSON browser actions.",
            prompt,
            options={"temperature": 0, "num_predict": 200},
        )
        action = _parse_action(raw)
        if not action:
            return {"ok": False, "error": "Invalid DOM plan JSON", "raw": raw[:300]}
        return {"ok": True, "action": action, "raw": raw[:400]}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def execute_dom_action(action: dict[str, Any]) -> dict[str, Any]:
    from jarvis.browser_agent import _PAGE, _agent_paused, click_selector

    if _agent_paused():
        return {"ok": False, "message": "Agent paused"}
    kind = (action.get("action") or "").lower()
    if kind == "done":
        return {"ok": True, "done": True, "summary": action.get("summary", "")}
    if kind == "fail":
        return {"ok": False, "failed": True, "reason": action.get("reason", "")}
    if kind == "wait":
        import time

        time.sleep(min(5.0, max(0.1, int(action.get("ms") or 500) / 1000.0)))
        return {"ok": True, "waited": True}
    if kind == "click":
        sel = (action.get("selector") or "").strip()
        if not sel:
            return {"ok": False, "message": "Missing selector"}
        return click_selector(sel)
    if kind == "fill":
        sel = (action.get("selector") or "").strip()
        text = action.get("text") or ""
        if not _PAGE or not sel:
            return {"ok": False, "message": "Missing page or selector"}
        try:
            _PAGE.fill(sel, str(text), timeout=10000)
            return {"ok": True, "selector": sel, "filled": True}
        except Exception as exc:
            return {"ok": False, "message": str(exc)}
    return {"ok": False, "message": f"Unknown action: {kind}"}
