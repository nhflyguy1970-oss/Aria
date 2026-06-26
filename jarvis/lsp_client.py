"""LSP client — diagnostics and IDE features via language servers."""

from __future__ import annotations

from pathlib import Path

from jarvis.lsp_protocol import LspError
from jarvis.lsp_servers import list_servers, server_for_path
from jarvis.lsp_session import LspSession, get_session, shutdown_all
from jarvis.syntax_check import Diagnostic


def lsp_enabled() -> bool:
    from jarvis.lsp_servers import _enabled

    return _enabled()


def pylsp_available() -> bool:
    if not lsp_enabled():
        return False
    return server_for_path(Path("x.py")) is not None


def check_python_lsp(path: Path, *, timeout: int = 25) -> list[Diagnostic]:
    """Backward-compatible pylsp diagnostics for a Python file."""
    _ = timeout
    return check_file_lsp(path)


def check_file_lsp(path: Path, content: str | None = None) -> list[Diagnostic]:
    try:
        session = get_session(path)
        if not session:
            return []
        return session.diagnostics(path, content=content)
    except LspError:
        return []


def go_to_definition(path: Path, line: int, column: int = 1) -> list[dict]:
    session = get_session(path)
    if not session:
        raise LspError(f"No language server for {path.suffix}")
    return session.definition(path, line, column)


def find_references(path: Path, line: int, column: int = 1) -> list[dict]:
    session = get_session(path)
    if not session:
        raise LspError(f"No language server for {path.suffix}")
    return session.references(path, line, column)


def hover(path: Path, line: int, column: int = 1) -> str:
    session = get_session(path)
    if not session:
        raise LspError(f"No language server for {path.suffix}")
    return session.hover(path, line, column)


def completion(path: Path, line: int, column: int = 1) -> list[dict]:
    session = get_session(path)
    if not session:
        raise LspError(f"No language server for {path.suffix}")
    return session.completion(path, line, column)


def document_symbols(path: Path) -> list[dict]:
    session = get_session(path)
    if not session:
        raise LspError(f"No language server for {path.suffix}")
    return session.document_symbols(path)


def format_document(path: Path) -> str:
    session = get_session(path)
    if not session:
        raise LspError(f"No language server for {path.suffix}")
    return session.format_document(path)


def servers_status() -> dict:
    servers = list_servers()
    return {
        "enabled": lsp_enabled(),
        "servers": servers,
        "any_available": any(s["available"] for s in servers),
    }
