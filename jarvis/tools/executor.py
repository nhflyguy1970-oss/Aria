"""Tool executor — run tools, capture results, store in memory."""

from __future__ import annotations

import logging
import time
from typing import Any

from jarvis.tools.registry import ToolDescriptor, get_tool, list_tools

logger = logging.getLogger("jarvis.tools.executor")

_CODING_KEYWORDS = ("fix", "bug", "refactor", "implement", "code", "test", "lint", "pr")
_AGENT_KEYWORDS = ("autonomous", "long running", "multi-file", "scaffold", "build app")


def select_tool(task: str, *, prefer: str = "") -> ToolDescriptor | None:
    """Pick the best available tool for a task."""
    task_lower = (task or "").lower()
    tools = [t for t in list_tools() if t.autoselect and t.available()]

    if prefer:
        chosen = get_tool(prefer)
        if chosen and chosen.available():
            return chosen

    try:
        from jarvis.personalization.store import preferred_tool

        pref = preferred_tool()
        if pref:
            tool = get_tool(pref)
            if tool and tool.available():
                return tool
    except Exception:
        pass

    if any(k in task_lower for k in _AGENT_KEYWORDS):
        for tid in ("openhands", "goose", "hermes"):
            tool = get_tool(tid)
            if tool and tool.available():
                return tool

    if any(k in task_lower for k in _CODING_KEYWORDS):
        for tid in ("aria_engineering", "claude_code", "cursor", "continue", "gemini_cli", "opencode"):
            tool = get_tool(tid)
            if tool and tool.available():
                return tool

    return tools[0] if tools else None


def execute_tool(
    tool_id: str,
    params: dict[str, Any],
    *,
    memory_sink: bool = True,
) -> dict[str, Any]:
    """Execute a managed tool and optionally persist results."""
    tool = get_tool(tool_id)
    if tool is None:
        return {"ok": False, "error": f"Unknown tool: {tool_id}"}
    if not tool.available():
        return {"ok": False, "error": f"Tool unavailable: {tool.label}"}

    if tool_id == "aria_engineering":
        return _run_aria_engineering(params)

    if tool.run is None:
        from jarvis.tools.runner import build_command

        if build_command(tool_id, params) is None:
            return {"ok": False, "error": f"Tool {tool_id} has no run implementation"}

    started = time.time()
    if params.get("background"):
        from jarvis.tools.runner import start_background

        run = start_background(tool_id, params)
        return {
            "ok": run.status != "failed",
            "tool": tool_id,
            "run_id": run.id,
            "status": run.status,
            "message": f"Started background run `{run.id}`",
        }

    from jarvis.tools.runner import run_sync

    result = run_sync(tool_id, params, timeout=int(params.get("timeout") or 600))
    if result.get("ok") is None and tool.run:
        result = tool.run(params)
    result["tool"] = tool_id
    result["label"] = tool.label
    result["elapsed_ms"] = int((time.time() - started) * 1000)

    if memory_sink and result.get("ok"):
        _remember_tool_result(tool, params, result)
        try:
            from jarvis.personalization.learner import learn_from_tool_result

            learn_from_tool_result(tool_id, result)
        except Exception:
            pass

    return result


def _run_aria_engineering(params: dict[str, Any]) -> dict[str, Any]:
    """Delegate to built-in engineering behavior."""
    task = str(params.get("task") or params.get("prompt") or "").strip()
    if not task:
        return {"ok": False, "error": "task required"}
    try:
        from jarvis.assistant_instance import get_assistant

        assistant = get_assistant()
        result = assistant.process(task, action="coding_task")
        return {
            "ok": bool(result.get("ok")),
            "tool": "aria_engineering",
            "message": result.get("message") or "",
            "stdout": (result.get("message") or "")[:8000],
            "data": result,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc), "tool": "aria_engineering"}


def _remember_tool_result(tool: ToolDescriptor, params: dict[str, Any], result: dict[str, Any]) -> None:
    try:
        from jarvis.assistant_instance import get_assistant

        assistant = get_assistant()
        task = str(params.get("task") or params.get("prompt") or "")[:200]
        summary = (result.get("stdout") or result.get("message") or "")[:500]
        if hasattr(assistant, "memory") and assistant.memory:
            assistant.memory.add(
                f"[tool:{tool.id}] {task}\n{summary}",
                entry_type="tool_result",
                namespace="tools",
                metadata={"tool": tool.id, "ok": result.get("ok")},
            )
    except Exception as exc:
        logger.debug("Tool memory sink failed: %s", exc)


def tool_status() -> dict[str, Any]:
    tools = list_tools()
    available = [t for t in tools if t.available()]
    return {
        "ok": True,
        "total": len(tools),
        "available": len(available),
        "tools": [t.to_dict() for t in tools],
    }


def format_tool_status() -> str:
    status = tool_status()
    lines = [
        "## Coding Tools",
        f"**{status.get('available', 0)}/{status.get('total', 0)}** available",
        "",
    ]
    for tool in status.get("tools") or []:
        mark = "●" if tool.get("available") else "○"
        lines.append(f"{mark} **{tool.get('label')}** (`{tool.get('id')}`)")
    return "\n".join(lines)
