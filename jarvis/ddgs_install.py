"""duckduckgo-search / ddgs install probe and optional bootstrap."""

from __future__ import annotations

import logging
import subprocess
import sys

log = logging.getLogger("jarvis.ddgs.install")


def ddgs_importable() -> bool:
    try:
        import ddgs  # noqa: F401

        return True
    except ImportError:
        pass
    try:
        import duckduckgo_search  # noqa: F401

        return True
    except ImportError:
        return False


def ddgs_stack_ready() -> dict:
    from jarvis.feature_flags import curated_news_enabled

    has_ddgs = False
    has_legacy = False
    try:
        import ddgs  # noqa: F401

        has_ddgs = True
    except ImportError:
        pass
    try:
        import duckduckgo_search  # noqa: F401

        has_legacy = True
    except ImportError:
        pass
    ready = has_ddgs or has_legacy
    return {
        "enabled": curated_news_enabled(),
        "ddgs": has_ddgs,
        "duckduckgo_search": has_legacy,
        "available": ready,
    }


def ensure_ddgs(*, install: bool | None = None) -> dict:
    """Return readiness; optionally pip install duckduckgo-search + ddgs."""
    if install is None:
        install = False

    if not ddgs_importable() and install:
        log.info("Installing duckduckgo-search and ddgs…")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "duckduckgo-search>=6.0.0",
                "ddgs>=9.0.0",
            ],
            check=False,
            capture_output=True,
            timeout=300,
        )

    stack = ddgs_stack_ready()
    ready = stack["available"]
    hint = "Ready for curated news" if ready else "Run: pip install duckduckgo-search ddgs"
    return {"ok": ready, **stack, "hint": hint}
