"""Chat/action handlers for Browser."""

from __future__ import annotations

from typing import Any

from jarvis.handlers.registry import register_action
from jarvis.response import err as _err
from jarvis.response import ok as _ok


@register_action("browse_web", module="browser", description="Navigate Browser agent to a URL")
def browse_web(assistant, params: dict, message: str = "") -> dict[str, Any]:
    from jarvis import browser_agent as ba
    from jarvis.browser_product.history import record_visit

    url = (params.get("url") or "").strip()
    if not url:
        return _err("URL required — e.g. browse https://example.com", module="browser")
    result = ba.navigate(url, allow_risky=bool(params.get("allow_risky")))
    if result.get("ok"):
        try:
            record_visit(result.get("url") or url, title=result.get("title") or "")
        except Exception:
            pass
        msg = result.get("message") or f"Navigated to {url}"
        extra = {k: v for k, v in result.items() if k not in ("message", "status", "ok", "url")}
        return _ok(
            msg,
            module="browser",
            type="browser_navigate",
            url=result.get("url") or url,
            open_view="browser",
            prefill_url=result.get("url") or url,
            **extra,
        )
    return _err(
        result.get("message") or "Navigation failed",
        module="browser",
        recovery=result.get("recovery"),
        needs_confirm=result.get("needs_confirm"),
    )


@register_action("browser_run_task", module="browser", description="Run Browser agent task on live page")
def browser_run_task(assistant, params: dict, message: str = "") -> dict[str, Any]:
    from jarvis import browser_agent as ba

    goal = (params.get("goal") or params.get("task") or message or "").strip()
    mode = (params.get("mode") or "auto").strip()
    modes = ba._modes_available()
    if mode == "vlm" and not modes.get("vlm"):
        return _err(modes.get("unavailable_reason") or "VLM mode unavailable", module="browser")
    if mode == "dom" and not modes.get("dom"):
        return _err(modes.get("unavailable_reason") or "DOM mode unavailable", module="browser")
    url = (params.get("url") or "").strip()
    if url:
        nav = ba.navigate(url, allow_risky=bool(params.get("allow_risky")))
        if not nav.get("ok"):
            return _err(nav.get("message") or "Navigate failed", module="browser", recovery=nav.get("recovery"))
    result = ba.run_agent_task(
        goal,
        mode=mode,
        max_steps=int(params.get("max_steps") or 8),
        assistant=assistant,
    )
    if result.get("ok"):
        return _ok(
            result.get("message") or "Browser task complete",
            module="browser",
            type="browser_task",
            open_view="browser",
            steps=result.get("steps"),
            prefill_goal=goal,
        )
    return _err(
        result.get("message") or "Browser task failed",
        module="browser",
        recovery=result.get("recovery"),
        steps=result.get("steps"),
    )


@register_action("browser_takeover", module="browser", description="Pause agent for human takeover")
def browser_takeover(assistant, params: dict, message: str = "") -> dict[str, Any]:
    from jarvis import browser_agent as ba

    st = ba.takeover()
    return _ok(
        st.get("message") or "Takeover active",
        module="browser",
        open_view="browser",
        **{k: v for k, v in st.items() if k not in ("message", "ok", "status")},
    )


@register_action("browser_summarize", module="browser", description="Summarize current page", info=True)
def browser_summarize(assistant, params: dict, message: str = "") -> dict[str, Any]:
    from jarvis.browser_product.session import extract_text

    ext = extract_text(limit=5000)
    if not ext.get("ok"):
        return _err(ext.get("message") or "No page loaded", module="browser")
    text = ext.get("text") or ""
    return _ok(
        f"**{ext.get('title') or 'Page'}**\n{ext.get('url')}\n\n{text[:2500]}",
        module="browser",
        open_view="browser",
        url=ext.get("url"),
    )


@register_action("search_and_browse", module="browser", description="Search then open a result")
def search_and_browse(assistant, params: dict, message: str = "") -> dict[str, Any]:
    query = (params.get("query") or message or "").strip()
    if not query:
        return _err("Search query required", module="browser")
    # Prefer web_search then navigate first URL if present
    try:
        from jarvis.handlers.registry import call_action, has_action

        if has_action("web_search"):
            search = call_action(assistant, "web_search", {"query": query}, query)
            msg = search.get("message") or ""
            import re

            m = re.search(r"https?://\S+", msg)
            if m:
                url = m.group(0).rstrip(".,)")
                return browse_web(assistant, {"url": url}, f"browse {url}")
            return search if isinstance(search, dict) else _ok(str(search), module="browser")
    except Exception as exc:
        return _err(f"Search failed: {exc}", module="browser")
    return _err("web_search unavailable", module="browser")


@register_action("browser_save_documents", module="browser", description="Save page text to Documents")
def browser_save_documents(assistant, params: dict, message: str = "") -> dict[str, Any]:
    from jarvis.browser_product.session import extract_text

    ext = extract_text(limit=20000)
    if not ext.get("ok"):
        return _err(ext.get("message") or "No page", module="browser")
    title = params.get("title") or ext.get("title") or "Browser page"
    body = f"Source: {ext.get('url')}\n\n{ext.get('text')}"
    try:
        from jarvis.handlers.registry import call_action, has_action

        if has_action("documents_add") or has_action("document_add"):
            action = "documents_add" if has_action("documents_add") else "document_add"
            return call_action(
                assistant,
                action,
                {"title": title, "text": body, "content": body},
                title,
            )
    except Exception as exc:
        return _err(f"Documents save failed: {exc}", module="browser")
    # Soft fallback: journal-like note
    return _ok(
        f"Page extracted ({len(body)} chars). Documents action unavailable — content ready to paste.\n\n{body[:1500]}",
        module="browser",
        extracted=True,
        url=ext.get("url"),
    )


@register_action("browser_voice", module="browser", description="Voice control for Browser")
def browser_voice(assistant, params: dict, message: str = "") -> dict[str, Any]:
    from jarvis.browser_product.voice_bridge import handle_voice_command

    return handle_voice_command(params.get("text") or message, assistant=assistant)


@register_action("browser_vision_coding", module="browser", description="Browser screenshot → Coding proposal")
def browser_vision_coding(assistant, params: dict, message: str = "") -> dict[str, Any]:
    from jarvis.browser_product.vision_to_coding import vision_to_coding

    result = vision_to_coding(
        assistant,
        hint=params.get("hint") or message,
        image_path=params.get("path") or "",
        use_live_screenshot=not bool(params.get("path")),
    )
    if result.get("ok"):
        return _ok(
            result.get("message") or "Coding proposal ready — review in Coding",
            module="browser",
            open_view="coding",
            proposal_id=result.get("proposal_id"),
            **{k: v for k, v in result.items() if k not in ("message", "ok", "error")},
        )
    return _err(result.get("error") or "Vision→Coding failed", module="browser")
