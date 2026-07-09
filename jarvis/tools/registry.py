"""Tool registry — coding CLIs and agent executors Aria manages."""

from __future__ import annotations

import logging
import os
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.tools")

RunFn = Callable[[dict[str, Any]], dict[str, Any]]
HealthFn = Callable[[], bool]


@dataclass
class ToolDescriptor:
    id: str
    label: str
    category: str
    description: str = ""
    binary: str = ""
    managed: bool = True
    autoselect: bool = True
    config_keys: list[str] = field(default_factory=list)
    health: HealthFn = field(default=lambda: False, repr=False)
    run: RunFn | None = field(default=None, repr=False)

    def available(self) -> bool:
        try:
            return bool(self.health())
        except Exception:
            return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "category": self.category,
            "description": self.description,
            "binary": self.binary,
            "managed": self.managed,
            "autoselect": self.autoselect,
            "available": self.available(),
            "config_keys": list(self.config_keys),
        }


_REGISTRY: dict[str, ToolDescriptor] = {}
_built = False


def register_tool(tool: ToolDescriptor) -> ToolDescriptor:
    _REGISTRY[tool.id] = tool
    return tool


def get_tool(tool_id: str) -> ToolDescriptor | None:
    _ensure_builtins()
    return _REGISTRY.get(tool_id)


def list_tools(*, category: str | None = None) -> list[ToolDescriptor]:
    _ensure_builtins()
    items = list(_REGISTRY.values())
    if category:
        items = [t for t in items if t.category == category]
    return sorted(items, key=lambda t: t.label.lower())


def _which(name: str) -> bool:
    return bool(shutil.which(name))


def _run_cli(binary: str, args: list[str], *, cwd: str = "", timeout: int = 300) -> dict[str, Any]:
    import subprocess

    if not shutil.which(binary):
        return {"ok": False, "error": f"{binary} not installed"}
    try:
        proc = subprocess.run(
            [binary, *args],
            cwd=cwd or None,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=os.environ.copy(),
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": (proc.stdout or "")[:8000],
            "stderr": (proc.stderr or "")[:2000],
            "binary": binary,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"{binary} timed out after {timeout}s"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _ensure_builtins() -> None:
    global _built
    if _built:
        return

    register_tool(
        ToolDescriptor(
            id="aria_engineering",
            label="Aria Engineering",
            category="coding",
            description="Built-in coding agent (LSP, git, proposals)",
            binary="internal",
            health=lambda: True,
        )
    )

    register_tool(
        ToolDescriptor(
            id="cursor",
            label="Cursor MCP",
            category="coding",
            description="Cursor IDE bridge via MCP",
            binary="cursor",
            health=lambda: _which("cursor") or bool(os.getenv("CURSOR_API_KEY")),
            config_keys=["CURSOR_API_KEY"],
        )
    )

    register_tool(
        ToolDescriptor(
            id="continue",
            label="Continue",
            category="coding",
            description="Continue IDE extension CLI",
            binary="cn",
            health=lambda: _which("cn") or _which("continue"),
            run=lambda p: _run_cli(
                shutil.which("cn") or shutil.which("continue") or "cn",
                ["--prompt", str(p.get("task") or p.get("prompt") or "")],
                cwd=str(p.get("cwd") or ""),
            ),
        )
    )

    for tid, binary, label in (
        ("claude_code", "claude", "Claude Code CLI"),
        ("gemini_cli", "gemini", "Gemini CLI"),
        ("opencode", "opencode", "OpenCode"),
        ("goose", "goose", "Goose"),
        ("hermes", "hermes", "Hermes"),
    ):
        register_tool(
            ToolDescriptor(
                id=tid,
                label=label,
                category="coding",
                binary=binary,
                health=lambda b=binary: _which(b),
                run=lambda p, b=binary: _run_cli(
                    b,
                    [str(p.get("task") or p.get("prompt") or "")],
                    cwd=str(p.get("cwd") or ""),
                    timeout=int(p.get("timeout") or 600),
                ),
            )
        )

    register_tool(
        ToolDescriptor(
            id="openhands",
            label="OpenHands",
            category="agent",
            description="Autonomous coding agent",
            binary="openhands",
            health=lambda: _which("openhands") or _docker_running("openhands"),
            run=lambda p: _run_openhands(p),
            config_keys=["JARVIS_OPENHANDS_URL"],
        )
    )

    _built = True


def _docker_running(container: str) -> bool:
    if not shutil.which("docker"):
        return False
    import subprocess

    try:
        proc = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", container],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return proc.returncode == 0 and proc.stdout.strip() == "true"
    except Exception:
        return False


def _run_openhands(params: dict[str, Any]) -> dict[str, Any]:
    binary = shutil.which("openhands")
    if binary:
        return _run_cli(
            "openhands",
            [str(params.get("task") or params.get("prompt") or "")],
            cwd=str(params.get("cwd") or ""),
            timeout=int(params.get("timeout") or 1800),
        )
    return {"ok": False, "error": "OpenHands not installed (binary or container)"}
