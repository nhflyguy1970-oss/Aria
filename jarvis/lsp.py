"""Diagnostics facade — syntax_check + IDE-grade LSP."""

from __future__ import annotations

from pathlib import Path

from jarvis.syntax_check import Diagnostic, available_tools, check_file


def check_python(path: Path, content: str | None = None) -> list[str]:
    diags = check_any(path, content=content, deep=True)
    return [d.format() for d in diags]


def check_javascript(path: Path, content: str | None = None) -> list[str]:
    diags = check_file(path, content=content, deep=False)
    return [d.format() for d in diags]


def check_any(path: Path, content: str | None = None, *, deep: bool = True) -> list[Diagnostic]:
    diags = check_file(path, content=content, deep=deep)
    if not deep:
        return diags
    try:
        from jarvis.lsp_client import check_file_lsp, lsp_enabled

        if lsp_enabled():
            seen = {d.format() for d in diags}
            for d in check_file_lsp(path, content=content):
                if d.format() not in seen:
                    diags.append(d)
    except Exception:
        pass
    return diags


def tools_status() -> dict[str, bool]:
    tools = available_tools()
    try:
        from jarvis.lsp_client import pylsp_available, servers_status

        status = servers_status()
        tools["lsp"] = status.get("enabled", False) and status.get("any_available", False)
        tools["pylsp"] = pylsp_available()
        for srv in status.get("servers") or []:
            tools[f"lsp_{srv['id']}"] = bool(srv.get("available"))
    except Exception:
        tools["lsp"] = False
        tools["pylsp"] = False
    return tools
