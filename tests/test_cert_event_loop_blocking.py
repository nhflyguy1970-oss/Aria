"""An async route handler that blocks is a production outage, not a slow page.

FastAPI runs `async def` handlers on the event loop itself and plain `def`
handlers in a threadpool. A handler declared `async def` that never awaits and
calls a local model, or OCR, therefore holds the whole server for as long as
that work takes: every other request stalls behind it, and ARIA's own health
watchdog restarts the server as unresponsive — which also re-locks the owner
vault. That happened twice in production before these handlers were fixed.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROUTES = Path(__file__).resolve().parents[1] / "jarvis" / "gui" / "extra_routes.py"

# Handlers that reach a local model or OCR, and so must never sit on the loop.
MUST_BE_SYNC = {
    "journal_assist_reflect",
    "journal_assist_writing",
    "journal_assist_vision",
    "journal_reflect",
}

ROUTE_METHODS = {"get", "post", "put", "delete", "patch", "head", "options"}


def _handlers(tree: ast.AST) -> dict[str, ast.AST]:
    found = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                func = dec.func if isinstance(dec, ast.Call) else dec
                if isinstance(func, ast.Attribute) and func.attr in ROUTE_METHODS:
                    found[node.name] = node
    return found


def test_blocking_handlers_are_not_async():
    handlers = _handlers(ast.parse(ROUTES.read_text(encoding="utf-8")))
    missing = MUST_BE_SYNC - handlers.keys()
    assert not missing, f"handler(s) disappeared, update this test: {sorted(missing)}"
    offenders = [n for n in sorted(MUST_BE_SYNC) if isinstance(handlers[n], ast.AsyncFunctionDef)]
    assert not offenders, (
        "these handlers call a model or OCR and must be plain `def` so FastAPI "
        f"runs them off the event loop: {offenders}"
    )


def test_the_reflect_handler_still_returns_a_reflection():
    """The fix must not have changed what the endpoint does."""
    handlers = _handlers(ast.parse(ROUTES.read_text(encoding="utf-8")))
    body = ast.unparse(handlers["journal_assist_reflect"])
    assert "reflect_assistant" in body
    assert "scope" in body
