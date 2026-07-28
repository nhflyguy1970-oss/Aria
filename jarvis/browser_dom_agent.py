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
{{"action":"select","selector":"...","value":"...","reason":"..."}}
{{"action":"scroll","dy":600}}
{{"action":"wait","ms":500}}
{{"action":"extract"}}
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
    from jarvis.browser_product.session import get_page

    page = get_page()
    if not page:
        return {"ok": False, "error": "No browser page — navigate first"}
    try:
        title = page.title()
        url = page.url
        elements = page.evaluate(
            """() => {
              const out = [];
              const nodes = document.querySelectorAll('a, button, input, textarea, select, [role=button]');
              for (const el of Array.from(nodes).slice(0, 35)) {
                const text = (el.innerText || el.value || el.getAttribute('aria-label') || '').trim().slice(0, 80);
                if (!text && el.tagName !== 'INPUT') continue;
                let sel = '';
                if (el.id) sel = '#' + CSS.escape(el.id);
                else if (el.name) sel = el.tagName.toLowerCase() + '[name=\"' + el.name + '\"]';
                else if (el.getAttribute('aria-label')) sel = el.tagName.toLowerCase() + '[aria-label=\"' + el.getAttribute('aria-label').slice(0,40) + '\"]';
                out.push({
                  tag: el.tagName.toLowerCase(),
                  text,
                  id: el.id || '',
                  name: el.name || '',
                  type: el.type || '',
                  href: el.href ? el.href.slice(0, 120) : '',
                  selector: sel,
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
        if el.get("selector"):
            parts.append(el["selector"])
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
            return {"ok": False, "error": "Invalid DOM plan JSON", "raw": (raw or "")[:300]}
        return {"ok": True, "action": action, "raw": (raw or "")[:400]}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def execute_dom_action(action: dict[str, Any]) -> dict[str, Any]:
    from jarvis.browser_product import session as sess

    if sess.is_paused():
        return {"ok": False, "message": "Agent paused"}
    kind = (action.get("action") or "").lower()
    if kind == "done":
        return {"ok": True, "done": True, "summary": action.get("summary", "")}
    if kind == "fail":
        return {"ok": False, "failed": True, "reason": action.get("reason", ""), "terminal": True}
    if kind == "wait":
        return sess.wait_ms(int(action.get("ms") or 500))
    if kind == "scroll":
        return sess.scroll_by(int(action.get("dy") or 600))
    if kind == "extract":
        return sess.extract_text()
    if kind == "click":
        sel = (action.get("selector") or "").strip()
        if not sel:
            return {"ok": False, "message": "Missing selector"}
        return sess.click_selector(sel)
    if kind == "fill":
        sel = (action.get("selector") or "").strip()
        text = action.get("text") or ""
        if not sel:
            return {"ok": False, "message": "Missing selector"}
        return sess.fill_selector(sel, str(text))
    if kind == "select":
        sel = (action.get("selector") or "").strip()
        value = action.get("value") or ""
        if not sel:
            return {"ok": False, "message": "Missing selector"}
        return sess.select_option(sel, str(value))
    return {"ok": False, "message": f"Unknown action: {kind}"}
