"""Playwright install probe and optional bootstrap."""

from __future__ import annotations

import logging
import time

log = logging.getLogger("jarvis.browser.playwright")

_CACHE: dict = {"ts": 0.0, "stack": {}}
_TTL = 45.0
# A working stack stays cached; a failed probe does not. The chromium probe
# launches a real browser, so it can fail transiently under load — and caching
# that for the full TTL turns one blip into browsing being unavailable for
# nearly a minute.
_NEGATIVE_TTL = 5.0


def playwright_importable() -> bool:
    try:
        import playwright  # noqa: F401

        return True
    except ImportError:
        return False


def chromium_installed() -> bool:
    if not playwright_importable():
        return False
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        return True
    except Exception as exc:
        log.debug("chromium probe failed: %s", exc)
        return False


def browser_stack_ready(*, probe_chromium: bool = True) -> dict[str, bool]:
    now = time.time()
    cached = _CACHE.get("stack")
    if cached:
        healthy = bool(cached.get("playwright") and cached.get("chromium"))
        ttl = _TTL if healthy else _NEGATIVE_TTL
        if now - float(_CACHE.get("ts") or 0) < ttl:
            return dict(cached)
    pw = playwright_importable()
    chrom = chromium_installed() if (pw and probe_chromium) else False
    stack = {"playwright": pw, "chromium": chrom}
    _CACHE["ts"] = now
    _CACHE["stack"] = dict(stack)
    return stack


def ensure_playwright(*, install: bool = False) -> dict[str, bool]:
    stack = browser_stack_ready(probe_chromium=True)
    if stack["playwright"] and stack["chromium"]:
        return stack
    if install:
        try:
            import subprocess
            import sys

            subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=False)
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=False)
            _CACHE["ts"] = 0  # invalidate
        except Exception as exc:
            log.debug("playwright install failed: %s", exc)
    return browser_stack_ready(probe_chromium=True)
