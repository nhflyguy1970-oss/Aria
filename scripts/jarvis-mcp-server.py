#!/usr/bin/env python3
"""Jarvis MCP server for Cursor — official MCP SDK stdio transport."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "jarvis",
    instructions="Jarvis tools: coding (read/search/propose/apply) plus briefing, environment, HA, journal, documents, and queued image generation.",
)


def _run(name: str, **kwargs) -> str:
    from jarvis.config import PROJECT_ROOT
    from jarvis.cursor_bridge import handle_mcp_tool

    result = handle_mcp_tool(name, kwargs, PROJECT_ROOT)
    return json.dumps(result, indent=2)


@mcp.tool()
def jarvis_read_file(path: str) -> str:
    """Read a file from the Jarvis project."""
    return _run("jarvis_read_file", path=path)


@mcp.tool()
def jarvis_search_code(query: str, limit: int = 8) -> str:
    """Semantic search over the Jarvis codebase."""
    return _run("jarvis_search_code", query=query, limit=limit)


@mcp.tool()
def jarvis_check_syntax(path: str, content: str = "") -> str:
    """Run syntax/lint checks on a file."""
    args = {"path": path}
    if content:
        args["content"] = content
    return _run("jarvis_check_syntax", **args)


@mcp.tool()
def jarvis_code_context(path: str, task: str = "") -> str:
    """Gather related context for a file before editing."""
    return _run("jarvis_code_context", path=path, task=task)


@mcp.tool()
def jarvis_run_script(path: str) -> str:
    """Run a Python script in the project sandbox."""
    return _run("jarvis_run_script", path=path)


@mcp.tool()
def jarvis_build_index() -> str:
    """Rebuild semantic code search index."""
    return _run("jarvis_build_index")


@mcp.tool()
def jarvis_list_files(limit: int = 100) -> str:
    """List project source files."""
    return _run("jarvis_list_files", limit=limit)


@mcp.tool()
def jarvis_propose_fix(path: str, task: str = "") -> str:
    """Generate a fix proposal for a Python file. Returns proposal_id for jarvis_apply_proposal."""
    return _run("jarvis_propose_fix", path=path, task=task)


@mcp.tool()
def jarvis_propose_create(description: str, path: str = "") -> str:
    """Generate a new Python script + pytest proposal."""
    return _run("jarvis_propose_create", description=description, path=path)


@mcp.tool()
def jarvis_apply_proposal(proposal_id: str = "", force: bool = False) -> str:
    """Apply a pending Jarvis code proposal."""
    return _run("jarvis_apply_proposal", proposal_id=proposal_id, force=force)


@mcp.tool()
def jarvis_undo_apply() -> str:
    """Undo the last applied code proposal."""
    return _run("jarvis_undo_apply")


@mcp.tool()
def jarvis_find_references(symbol: str, limit: int = 30) -> str:
    """Find grep-based references to a symbol in the codebase."""
    return _run("jarvis_find_references", symbol=symbol, limit=limit)


@mcp.tool()
def jarvis_run_command(command: str) -> str:
    """Run an allowlisted project command (pytest, python, ruff, npm test, etc.)."""
    return _run("jarvis_run_command", command=command)


@mcp.tool()
def jarvis_get_editor_context() -> str:
    """Get active file + selection synced from Cursor (requires Jarvis Editor Bridge extension)."""
    return _run("jarvis_get_editor_context")


@mcp.tool()
def jarvis_briefing() -> str:
    """Get today's morning briefing markdown."""
    return _run_domain("jarvis_briefing")


@mcp.tool()
def jarvis_environment() -> str:
    """Machine + Jarvis environment snapshot (profile, VRAM, services)."""
    return _run_domain("jarvis_environment")


@mcp.tool()
def jarvis_journal_log(text: str) -> str:
    """Add a bullet to today's journal."""
    return _run_domain("jarvis_journal_log", text=text)


@mcp.tool()
def jarvis_document_search(query: str) -> str:
    """Semantic/keyword search over data/documents/ library."""
    return _run_domain("jarvis_document_search", query=query)


@mcp.tool()
def jarvis_ha_toggle(entity_id: str, action: str = "toggle") -> str:
    """Toggle/on/off a Home Assistant entity by entity_id."""
    return _run_domain("jarvis_ha_toggle", entity_id=entity_id, action=action)


@mcp.tool()
def jarvis_ha_scene(scene: str) -> str:
    """Activate a Home Assistant scene."""
    return _run_domain("jarvis_ha_scene", scene=scene)


@mcp.tool()
def jarvis_generate_image(prompt: str) -> str:
    """Queue an image generation job (returns job_id)."""
    return _run_domain("jarvis_generate_image", prompt=prompt)


@mcp.tool()
def jarvis_chat(message: str) -> str:
    """Send a message to Jarvis chat (full router)."""
    return _run_domain("jarvis_chat", message=message)


def _run_domain(name: str, **kwargs) -> str:
    from jarvis.jarvis_mcp import handle_jarvis_mcp_tool

    result = handle_jarvis_mcp_tool(name, kwargs)
    return json.dumps(result, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
