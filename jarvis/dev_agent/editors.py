"""Editors — how proposed code changes are produced.

Kept separate from the loop so the loop is testable with a deterministic editor
and so the production path reuses ARIA's existing CodingAgent rather than a new
model integration.
"""

from __future__ import annotations

import logging
from typing import Any

from jarvis.dev_agent.workspace import Workspace

log = logging.getLogger("jarvis.dev_agent.editors")


def static_editor(files: list[dict[str, str]], summary: str = "static edit"):
    """Deterministic editor for tests and scripted changes."""

    def _edit(task: dict[str, Any], ws: Workspace, context: dict[str, Any]) -> dict[str, Any]:
        return {"files": files, "summary": summary}

    return _edit


def model_editor(assistant: Any = None):
    """Production editor backed by ARIA's existing CodingAgent."""

    def _edit(task: dict[str, Any], ws: Workspace, context: dict[str, Any]) -> dict[str, Any]:
        try:
            from jarvis.coding_agent import CodingAgent

            agent = CodingAgent(ws.root)
            result = agent.diagnose("", task["objective"])
            files = []
            for item in getattr(result, "files", []) or []:
                path = item.get("path") if isinstance(item, dict) else None
                content = item.get("content") if isinstance(item, dict) else None
                if path and content is not None:
                    files.append({"path": path, "content": content})
            return {"files": files, "summary": getattr(result, "message", "") or "model edit"}
        except Exception as exc:  # noqa: BLE001 - a model failure is data, not a crash
            log.warning("model editor unavailable: %s", exc)
            return {"files": [], "summary": f"model unavailable: {type(exc).__name__}: {exc}"}

    return _edit
