"""Managed LSP sessions — one language server per (server, workspace root)."""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from jarvis.lsp_protocol import LspError, LspProcess, LspTimeout
from jarvis.lsp_servers import ServerSpec, find_lsp_root, language_id_for
from jarvis.syntax_check import Diagnostic

_pool_lock = threading.Lock()
_pool: dict[tuple[str, str], tuple["LspSession", float]] = {}
SESSION_TTL = float(os.getenv("JARVIS_LSP_SESSION_TTL", "120"))


def _uri_to_path(uri: str) -> str:
    if uri.startswith("file://"):
        parsed = urlparse(uri)
        return str(Path(unquote(parsed.path)))
    return uri


def _path_to_uri(path: Path) -> str:
    return path.resolve().as_uri()


def _position(line: int, column: int) -> dict:
    return {"line": max(0, line - 1), "character": max(0, column - 1)}


def _loc_dict(loc: dict | None) -> dict | None:
    if not loc:
        return None
    uri = loc.get("uri") or (loc.get("targetUri") if isinstance(loc, dict) else None)
    if not uri and "targetUri" in loc:
        uri = loc["targetUri"]
    rng = loc.get("range") or loc.get("targetSelectionRange") or {}
    start = rng.get("start") or {}
    return {
        "path": _uri_to_path(uri) if uri else "",
        "uri": uri,
        "line": int(start.get("line", 0)) + 1,
        "column": int(start.get("character", 0)) + 1,
    }


def _diag_from_lsp(path: Path, item: dict, source: str) -> Diagnostic:
    sev = {1: "error", 2: "warning", 3: "info", 4: "info"}.get(int(item.get("severity", 1)), "warning")
    pos = item.get("range", {}).get("start", {})
    return Diagnostic(
        path=str(path),
        line=int(pos.get("line", 0)) + 1,
        column=int(pos.get("character", 0)) + 1,
        severity=sev,
        message=str(item.get("message", "")),
        source=source,
    )


class LspSession:
    def __init__(self, spec: ServerSpec, root: Path):
        self.spec = spec
        self.root = root
        self._proc: LspProcess | None = None
        self._docs: dict[str, int] = {}
        self._diagnostics: dict[str, list[Diagnostic]] = {}

    def start(self) -> None:
        if self._proc:
            return
        self._proc = LspProcess.start(list(self.spec.cmd), cwd=str(self.root))
        self._proc.request(
            "initialize",
            {
                "processId": os.getpid(),
                "rootUri": _path_to_uri(self.root),
                "capabilities": {
                    "textDocument": {
                        "publishDiagnostics": {},
                        "definition": {"linkSupport": True},
                        "references": {},
                        "hover": {"contentFormat": ["markdown", "plaintext"]},
                        "completion": {"completionItem": {"snippetSupport": False}},
                        "documentSymbol": {"hierarchicalDocumentSymbolSupport": True},
                        "formatting": {},
                    }
                },
            },
            timeout=30,
        )
        self._proc.notify("initialized", {})

    def _conn(self) -> LspProcess:
        if not self._proc:
            self.start()
        assert self._proc
        return self._proc

    def open_document(self, path: Path, content: str | None = None) -> str:
        resolved = path.resolve()
        uri = _path_to_uri(resolved)
        if uri in self._docs:
            return uri
        if content is None:
            content = resolved.read_text(encoding="utf-8", errors="replace")
        self._conn().notify(
            "textDocument/didOpen",
            {
                "textDocument": {
                    "uri": uri,
                    "languageId": language_id_for(resolved, self.spec),
                    "version": 1,
                    "text": content,
                }
            },
        )
        self._docs[uri] = 1
        for msg in self._conn().drain_notifications(timeout=3.0):
            if msg.get("method") == "textDocument/publishDiagnostics":
                params = msg.get("params") or {}
                if params.get("uri") == uri:
                    self._diagnostics[uri] = [
                        _diag_from_lsp(resolved, d, self.spec.id) for d in params.get("diagnostics") or []
                    ]
        return uri

    def diagnostics(self, path: Path, content: str | None = None) -> list[Diagnostic]:
        uri = self.open_document(path, content=content)
        if uri not in self._diagnostics:
            for msg in self._conn().drain_notifications(timeout=2.0):
                if msg.get("method") == "textDocument/publishDiagnostics":
                    params = msg.get("params") or {}
                    if params.get("uri") == uri:
                        self._diagnostics[uri] = [
                            _diag_from_lsp(path, d, self.spec.id)
                            for d in params.get("diagnostics") or []
                        ]
        return list(self._diagnostics.get(uri, []))

    def definition(self, path: Path, line: int, column: int = 1) -> list[dict]:
        uri = self.open_document(path)
        result = self._conn().request(
            "textDocument/definition",
            {"textDocument": {"uri": uri}, "position": _position(line, column)},
            timeout=20,
        )
        items = result if isinstance(result, list) else ([result] if result else [])
        return [loc for item in items if (loc := _loc_dict(item))]

    def references(self, path: Path, line: int, column: int = 1) -> list[dict]:
        uri = self.open_document(path)
        result = self._conn().request(
            "textDocument/references",
            {
                "textDocument": {"uri": uri},
                "position": _position(line, column),
                "context": {"includeDeclaration": True},
            },
            timeout=25,
        )
        return [loc for item in (result or []) if (loc := _loc_dict(item))]

    def hover(self, path: Path, line: int, column: int = 1) -> str:
        uri = self.open_document(path)
        result = self._conn().request(
            "textDocument/hover",
            {"textDocument": {"uri": uri}, "position": _position(line, column)},
            timeout=15,
        )
        if not result:
            return ""
        contents = result.get("contents")
        if isinstance(contents, str):
            return contents
        if isinstance(contents, dict):
            return str(contents.get("value", ""))
        if isinstance(contents, list):
            parts = []
            for part in contents:
                if isinstance(part, str):
                    parts.append(part)
                elif isinstance(part, dict):
                    parts.append(str(part.get("value", "")))
            return "\n".join(p for p in parts if p)
        return ""

    def completion(self, path: Path, line: int, column: int = 1) -> list[dict]:
        uri = self.open_document(path)
        result = self._conn().request(
            "textDocument/completion",
            {"textDocument": {"uri": uri}, "position": _position(line, column)},
            timeout=15,
        )
        items = []
        if isinstance(result, list):
            items = result
        elif isinstance(result, dict):
            items = result.get("items") or []
        out = []
        for item in items[:50]:
            label = item.get("label") or item.get("textEdit", {}).get("newText", "")
            out.append({
                "label": label,
                "kind": item.get("kind"),
                "detail": item.get("detail", ""),
                "documentation": item.get("documentation", ""),
            })
        return out

    def document_symbols(self, path: Path) -> list[dict]:
        uri = self.open_document(path)
        result = self._conn().request(
            "textDocument/documentSymbol",
            {"textDocument": {"uri": uri}},
            timeout=20,
        )
        symbols = result or []

        def flatten(sym: dict, prefix: str = "") -> list[dict]:
            name = sym.get("name", "")
            full = f"{prefix}.{name}" if prefix else name
            rng = sym.get("range") or sym.get("selectionRange") or {}
            start = rng.get("start") or {}
            row = {
                "name": full,
                "kind": sym.get("kind"),
                "line": int(start.get("line", 0)) + 1,
                "column": int(start.get("character", 0)) + 1,
            }
            rows = [row]
            for child in sym.get("children") or []:
                rows.extend(flatten(child, full))
            return rows

        out: list[dict] = []
        for sym in symbols:
            out.extend(flatten(sym))
        return out

    def format_document(self, path: Path) -> str:
        uri = self.open_document(path)
        edits = self._conn().request(
            "textDocument/formatting",
            {"textDocument": {"uri": uri}, "options": {"tabSize": 4, "insertSpaces": True}},
            timeout=30,
        )
        content = path.read_text(encoding="utf-8", errors="replace")
        if not edits:
            return content
        return _apply_edits(content, edits)

    def shutdown(self) -> None:
        if self._proc:
            self._proc.shutdown()
            self._proc = None


def _offset_at(text: str, line: int, character: int) -> int:
    lines = text.splitlines(True)
    pos = 0
    for i in range(min(line, len(lines))):
        pos += len(lines[i])
    if line < len(lines):
        pos += min(character, len(lines[line]))
    else:
        pos = len(text)
    return pos


def _apply_edits(content: str, edits: list[dict]) -> str:
    result = content
    ordered = sorted(
        edits,
        key=lambda e: (
            e.get("range", {}).get("start", {}).get("line", 0),
            e.get("range", {}).get("start", {}).get("character", 0),
        ),
        reverse=True,
    )
    for edit in ordered:
        rng = edit.get("range", {})
        start = rng.get("start", {})
        end = rng.get("end", {})
        s = _offset_at(content, int(start.get("line", 0)), int(start.get("character", 0)))
        e = _offset_at(content, int(end.get("line", 0)), int(end.get("character", 0)))
        result = result[:s] + edit.get("newText", "") + result[e:]
    return result


def get_session(path: Path) -> LspSession | None:
    from jarvis.lsp_servers import server_for_path

    spec = server_for_path(path)
    if not spec or not spec.available():
        return None
    root = find_lsp_root(path)
    key = (spec.id, str(root.resolve()))
    now = time.time()
    with _pool_lock:
        stale = [k for k, (_, ts) in _pool.items() if now - ts > SESSION_TTL]
        for k in stale:
            try:
                _pool[k][0].shutdown()
            except Exception:
                pass
            _pool.pop(k, None)
        if key in _pool:
            session, _ = _pool[key]
            _pool[key] = (session, now)
            return session
    session = LspSession(spec, root)
    try:
        session.start()
    except (LspError, LspTimeout, OSError) as e:
        raise LspError(f"Could not start {spec.label}: {e}") from e
    with _pool_lock:
        _pool[key] = (session, now)
    return session


def shutdown_all() -> None:
    with _pool_lock:
        for session, _ in _pool.values():
            try:
                session.shutdown()
            except Exception:
                pass
        _pool.clear()
