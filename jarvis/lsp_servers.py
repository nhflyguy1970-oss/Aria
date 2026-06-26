"""Language server registry for Jarvis LSP bridge."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ServerSpec:
    id: str
    label: str
    extensions: frozenset[str]
    cmd: tuple[str, ...]
    language_id: str

    def available(self) -> bool:
        if not self.cmd:
            return False
        return bool(shutil.which(self.cmd[0]))


def _enabled() -> bool:
    return os.getenv("JARVIS_LSP", "1").lower() not in ("0", "false", "no", "off")


def _which(*names: str) -> str | None:
    for name in names:
        path = shutil.which(name)
        if path:
            return path
    return None


def _specs() -> list[ServerSpec]:
    specs: list[ServerSpec] = []
    pylsp = _which("pylsp", "python-lsp-server")
    if pylsp:
        specs.append(
            ServerSpec("python", "Python (pylsp)", frozenset({".py"}), (pylsp,), "python")
        )
    tsls = _which("typescript-language-server")
    if tsls:
        specs.append(
            ServerSpec(
                "typescript",
                "TypeScript/JavaScript",
                frozenset({".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}),
                (tsls, "--stdio"),
                "typescript",
            )
        )
    bashls = _which("bash-language-server")
    if bashls:
        specs.append(
            ServerSpec(
                "bash",
                "Bash (bash-language-server)",
                frozenset({".sh", ".bash"}),
                (bashls, "start"),
                "shellscript",
            )
        )
    jsonls = _which("vscode-json-language-server", "json-languageserver")
    if jsonls:
        specs.append(
            ServerSpec("json", "JSON", frozenset({".json"}), (jsonls, "--stdio"), "json")
        )
    return specs


def server_for_path(path: Path) -> ServerSpec | None:
    if not _enabled():
        return None
    ext = path.suffix.lower()
    for spec in _specs():
        if ext in spec.extensions:
            return spec
    return None


def language_id_for(path: Path, spec: ServerSpec) -> str:
    ext = path.suffix.lower()
    if spec.id == "typescript":
        if ext in {".tsx", ".jsx"}:
            return "typescriptreact" if ext == ".tsx" else "javascriptreact"
        if ext in {".js", ".mjs", ".cjs"}:
            return "javascript"
        return "typescript"
    return spec.language_id


def find_lsp_root(path: Path) -> Path:
    from jarvis.config import PROJECT_ROOT

    resolved = path.resolve()
    if resolved == PROJECT_ROOT or PROJECT_ROOT in resolved.parents:
        return PROJECT_ROOT
    markers = ("pyproject.toml", "package.json", "Cargo.toml", "go.mod", ".git")
    for parent in [resolved.parent, *resolved.parents]:
        if any((parent / m).exists() for m in markers):
            return parent
    return resolved.parent


def list_servers() -> list[dict]:
    out = []
    for spec in _specs():
        out.append({
            "id": spec.id,
            "label": spec.label,
            "extensions": sorted(spec.extensions),
            "available": spec.available(),
            "cmd": list(spec.cmd),
        })
    return out
