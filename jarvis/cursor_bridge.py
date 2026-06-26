"""Cursor / IDE bridge — REST helpers and MCP tool definitions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jarvis import fs
from jarvis.code_context import format_context, gather_context
from jarvis.code_index import build_index, invalidate_cache
from jarvis.code_index import search as code_search
from jarvis.lsp import check_any
from jarvis.syntax_check import diagnostics_to_dicts, format_diagnostics


def get_file_context(path: str, base: Path, *, task: str = "") -> dict[str, Any]:
    ctx = gather_context(path, base, task=task)
    return {
        "path": path,
        "primary": ctx.get("primary", ""),
        "related": ctx.get("related", []),
        "tests": ctx.get("tests", []),
        "formatted": format_context(ctx),
    }


def search_codebase(query: str, limit: int = 8) -> list[dict]:
    return code_search(query, limit=limit)


def check_syntax(path: str, base: Path, *, content: str | None = None) -> dict[str, Any]:
    resolved = fs.resolve_path(path, base=base)
    diags = check_any(resolved, content=content, deep=True)
    return {
        "path": path,
        "ok": not any(d.severity == "error" for d in diags),
        "diagnostics": diagnostics_to_dicts(diags),
        "summary": format_diagnostics(diags),
    }


def list_project_files(base: Path, limit: int = 200) -> list[str]:
    _, files = fs.scan_project(base)
    return files[:limit]


def run_script_bridge(path: str, base: Path) -> dict[str, Any]:
    from jarvis.project_runner import run_script, runner_info
    resolved = fs.resolve_path(path, base=base)
    result = run_script(resolved, base, timeout=60)
    return {
        "ok": result.returncode == 0,
        "stdout": (result.stdout or "")[:4000],
        "stderr": (result.stderr or "")[:2000],
        "runner": runner_info(base),
    }


def build_code_index(root: Path | None = None) -> dict[str, Any]:
    invalidate_cache()
    chunks = build_index(root)
    return {"ok": True, "chunks": len(chunks)}


_assistant_inst = None  # legacy — use assistant_instance


def _assistant():
    from jarvis.assistant_instance import get_assistant

    return get_assistant()


def propose_fix(path: str, task: str, base: Path, *, mode: str = "fix") -> dict[str, Any]:
    """Generate a fix/improve proposal without applying."""
    _ = base
    a = _assistant()
    if mode == "fix":
        result = a._coding_fix({"path": path, "task": task}, task or f"fix {path}")
    else:
        result = a._coding_improve({"path": path}, task or f"improve {path}")
    return {
        "ok": result.get("ok", False),
        "proposal_id": result.get("proposal_id"),
        "message": result.get("message", ""),
        "syntax_ok": result.get("syntax_ok"),
        "diff": result.get("diff", ""),
    }


def propose_create(description: str, path: str, base: Path) -> dict[str, Any]:
    _ = base
    a = _assistant()
    result = a._coding_create({"description": description, "path": path}, description)
    return {
        "ok": result.get("ok", False),
        "proposal_id": result.get("proposal_id"),
        "message": result.get("message", ""),
        "syntax_ok": result.get("syntax_ok"),
    }


def apply_proposal_bridge(proposal_id: str, base: Path, *, force: bool = False) -> dict[str, Any]:
    _ = base
    a = _assistant()
    return a.apply_proposal(proposal_id or None, force=force)


MCP_TOOLS = [
    {
        "name": "jarvis_read_file",
        "description": "Read a file from the Jarvis project",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "jarvis_search_code",
        "description": "Semantic search over the Jarvis codebase",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
            "required": ["query"],
        },
    },
    {
        "name": "jarvis_check_syntax",
        "description": "Run syntax/lint checks on a file",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "jarvis_code_context",
        "description": "Gather related context for a file before editing",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}, "task": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "jarvis_run_script",
        "description": "Run a Python script in the project sandbox",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "jarvis_build_index",
        "description": "Rebuild semantic code search index",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "jarvis_list_files",
        "description": "List project source files",
        "inputSchema": {
            "type": "object",
            "properties": {"limit": {"type": "integer"}},
        },
    },
    {
        "name": "jarvis_propose_fix",
        "description": "Generate a fix proposal for a Python file (returns proposal_id; use jarvis_apply_proposal to save)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "task": {"type": "string"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "jarvis_propose_create",
        "description": "Generate a new Python script + pytest proposal",
        "inputSchema": {
            "type": "object",
            "properties": {
                "description": {"type": "string"},
                "path": {"type": "string"},
            },
            "required": ["description"],
        },
    },
    {
        "name": "jarvis_apply_proposal",
        "description": "Apply a pending Jarvis code proposal by proposal_id",
        "inputSchema": {
            "type": "object",
            "properties": {
                "proposal_id": {"type": "string"},
                "force": {"type": "boolean"},
            },
        },
    },
    {
        "name": "jarvis_undo_apply",
        "description": "Undo the last applied code proposal (restore backups / delete new files)",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "jarvis_get_editor_context",
        "description": "Active file and selection from Cursor (Jarvis Editor Bridge extension)",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


_DOMAIN_MCP_TOOLS = frozenset({
    "jarvis_briefing",
    "jarvis_environment",
    "jarvis_journal_log",
    "jarvis_document_search",
    "jarvis_ha_toggle",
    "jarvis_ha_scene",
    "jarvis_generate_image",
    "jarvis_chat",
})


def handle_mcp_tool(name: str, arguments: dict, base: Path) -> dict[str, Any]:
    """Dispatch MCP tool call."""
    if name in _DOMAIN_MCP_TOOLS:
        from jarvis.jarvis_mcp import handle_jarvis_mcp_tool

        return handle_jarvis_mcp_tool(name, arguments)
    if name == "jarvis_read_file":
        path = arguments.get("path", "")
        content = fs.read_file(path, base=base)
        return {"path": path, "content": content}
    if name == "jarvis_search_code":
        hits = search_codebase(arguments.get("query", ""), limit=int(arguments.get("limit", 8)))
        return {"results": hits}
    if name == "jarvis_check_syntax":
        return check_syntax(
            arguments.get("path", ""),
            base,
            content=arguments.get("content"),
        )
    if name == "jarvis_code_context":
        return get_file_context(arguments.get("path", ""), base, task=arguments.get("task", ""))
    if name == "jarvis_run_script":
        return run_script_bridge(arguments.get("path", ""), base)
    if name == "jarvis_build_index":
        return build_code_index(base)
    if name == "jarvis_list_files":
        return {"files": list_project_files(base, limit=int(arguments.get("limit", 100)))}
    if name == "jarvis_propose_fix":
        return propose_fix(
            arguments.get("path", ""),
            arguments.get("task", ""),
            base,
            mode="fix",
        )
    if name == "jarvis_propose_create":
        return propose_create(
            arguments.get("description", ""),
            arguments.get("path", ""),
            base,
        )
    if name == "jarvis_apply_proposal":
        return apply_proposal_bridge(
            arguments.get("proposal_id", ""),
            base,
            force=bool(arguments.get("force")),
        )
    if name == "jarvis_undo_apply":
        from jarvis.assistant import perform_undo_apply
        return perform_undo_apply(_assistant())
    if name == "jarvis_find_references":
        from jarvis.code_context import find_references
        symbol = arguments.get("symbol", "")
        hits = find_references(symbol, base, limit=int(arguments.get("limit", 30)))
        return {"symbol": symbol, "references": hits}
    if name == "jarvis_run_command":
        from jarvis.project_runner import run_project_command
        cmd = arguments.get("command", "")
        try:
            result = run_project_command(cmd, base, timeout=120)
            return {
                "ok": result.returncode == 0,
                "stdout": (result.stdout or "")[:4000],
                "stderr": (result.stderr or "")[:2000],
                "returncode": result.returncode,
            }
        except ValueError as e:
            return {"ok": False, "error": str(e)}
    if name == "jarvis_get_editor_context":
        from jarvis.editor_context import get_context, load_context
        ctx = get_context() or load_context()
        return {
            "fresh": get_context() is not None,
            "relative_file": ctx.relative_file,
            "has_selection": ctx.has_selection(),
            "formatted": ctx.format_for_prompt(),
            "open_files": ctx.open_files,
        }
    return {"error": f"Unknown tool: {name}"}
