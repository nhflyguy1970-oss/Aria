"""LSP bridge helpers for API, assistant, and Cursor integration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jarvis import fs
from jarvis.lsp import check_any
from jarvis.lsp_client import (
    completion,
    document_symbols,
    find_references,
    format_document,
    go_to_definition,
    hover,
    servers_status,
)
from jarvis.lsp_protocol import LspError
from jarvis.syntax_check import diagnostics_to_dicts, format_diagnostics


def _resolve(path: str, base: Path) -> Path:
    return fs.resolve_path(path, base=base)


def lsp_status() -> dict[str, Any]:
    return servers_status()


def lsp_diagnostics(path: str, base: Path, *, deep: bool = True) -> dict[str, Any]:
    resolved = _resolve(path, base)
    if not resolved.is_file():
        return {"ok": False, "message": f"File not found: {path}"}
    diags = check_any(resolved, deep=deep)
    return {
        "ok": True,
        "path": path,
        "syntax_ok": not any(d.severity == "error" for d in diags),
        "diagnostics": diagnostics_to_dicts(diags),
        "summary": format_diagnostics(diags),
    }


def lsp_definition(path: str, base: Path, line: int, column: int = 1) -> dict[str, Any]:
    resolved = _resolve(path, base)
    try:
        locations = go_to_definition(resolved, line, column)
    except LspError as e:
        return {"ok": False, "message": str(e)}
    return {"ok": True, "path": path, "locations": locations}


def lsp_references(path: str, base: Path, line: int, column: int = 1) -> dict[str, Any]:
    resolved = _resolve(path, base)
    try:
        locations = find_references(resolved, line, column)
    except LspError as e:
        return {"ok": False, "message": str(e)}
    return {"ok": True, "path": path, "references": locations}


def lsp_hover(path: str, base: Path, line: int, column: int = 1) -> dict[str, Any]:
    resolved = _resolve(path, base)
    try:
        text = hover(resolved, line, column)
    except LspError as e:
        return {"ok": False, "message": str(e)}
    return {"ok": True, "path": path, "hover": text}


def lsp_completion(path: str, base: Path, line: int, column: int = 1) -> dict[str, Any]:
    resolved = _resolve(path, base)
    try:
        items = completion(resolved, line, column)
    except LspError as e:
        return {"ok": False, "message": str(e)}
    return {"ok": True, "path": path, "items": items}


def lsp_symbols(path: str, base: Path) -> dict[str, Any]:
    resolved = _resolve(path, base)
    try:
        symbols = document_symbols(resolved)
    except LspError as e:
        return {"ok": False, "message": str(e)}
    return {"ok": True, "path": path, "symbols": symbols}


def lsp_format(path: str, base: Path, *, write: bool = False) -> dict[str, Any]:
    resolved = _resolve(path, base)
    try:
        formatted = format_document(resolved)
    except LspError as e:
        return {"ok": False, "message": str(e)}
    if write and formatted != resolved.read_text(encoding="utf-8", errors="replace"):
        resolved.write_text(formatted, encoding="utf-8")
    return {"ok": True, "path": path, "formatted": formatted, "written": write}
