"""Playwright install probe and optional bootstrap."""

from __future__ import annotations

import logging

log = logging.getLogger("jarvis.browser.playwright")


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


def browser_stack_ready() -> dict[str, bool]:
    pw = playwright_importable()
    return {"playwright": pw, "chromium": chromium_installed() if pw else False}


def ensure_playwright(*, install: bool = False) -> dict[str, bool]:
    stack = browser_stack_ready()
    if stack["playwright"] and stack["chromium"]:
        return stack
    if install:
        try:
            import subprocess
            import sys

            subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=False)
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=False)
        except Exception as exc:
            log.debug("playwright install failed: %s", exc)
    return browser_stack_ready()
