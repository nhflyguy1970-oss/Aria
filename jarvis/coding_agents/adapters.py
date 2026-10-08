"""Per-agent command lines and output parsers.

Only flags confirmed in the installed CLI's ``--help`` are used (see
``discovery.REQUIRED_FLAGS``). No adapter can emit a permission-bypass flag:
``--dangerously-*``, ``danger-full-access`` and ``bypassPermissions`` do not
appear in this module except in the guard that rejects them.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jarvis.coding_agents.discovery import READ_ONLY, WORKSPACE_WRITE

FORBIDDEN_ARGS = ("--dangerously", "danger-full-access", "bypassPermissions", "--yolo", "--approve-for-me")

_INSTRUCTIONS = """You are working in a disposable copy of the project at the current directory.
Mode: {mode_text}
Do not push, fetch credentials, contact remote services, or touch files outside this directory.
When you finish, end with a short report: what you changed (files), what you ran, and anything you could not do.

Task:
{task}
"""


@dataclass
class AgentReport:
    final_message: str = ""
    session_id: str = ""
    commands: list[dict[str, Any]] = field(default_factory=list)
    files_reported: list[str] = field(default_factory=list)
    usage: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    events: int = 0


def prompt_for(task: str, mode: str) -> str:
    mode_text = (
        "READ-ONLY. Investigate and report; do not modify any file."
        if mode == READ_ONLY
        else "You may edit files in this directory. Keep changes minimal and focused on the task."
    )
    return _INSTRUCTIONS.format(mode_text=mode_text, task=task.strip())


def build_argv(agent: str, binary: str, *, task: str, mode: str, workspace: str, out_dir: str,
               timeout_s: int) -> list[str]:
    prompt = prompt_for(task, mode)
    if agent == "codex":
        argv = [
            binary, "exec", "--json", "--ephemeral", "--color", "never",
            "--cd", workspace,
            "--sandbox", "read-only" if mode == READ_ONLY else "workspace-write",
            "--output-last-message", str(Path(out_dir) / "last_message.txt"),
            prompt,
        ]
    elif agent == "claude_code":
        tools = "Read,Glob,Grep" if mode == READ_ONLY else "Read,Glob,Grep,Edit,Write"
        argv = [
            binary, "--print", "--output-format", "stream-json", "--verbose",
            "--permission-mode", "plan" if mode == READ_ONLY else "acceptEdits",
            "--tools", tools,
            "--no-session-persistence",
            prompt,
        ]
    elif agent == "antigravity":
        argv = [
            binary, "--print", prompt, "--output-format", "stream-json",
            "--mode", "plan" if mode == READ_ONLY else "accept-edits",
            "--sandbox", "--print-timeout", f"{max(30, int(timeout_s))}s",
        ]
    else:
        raise ValueError(f"unknown agent {agent!r}")
    if mode not in (READ_ONLY, WORKSPACE_WRITE):
        raise ValueError(f"unknown mode {mode!r}")
    for arg in argv:
        if arg is not prompt and any(bad in arg for bad in FORBIDDEN_ARGS):
            raise ValueError(f"refusing permission-bypass argument {arg!r}")
    return argv


# ---------------------------------------------------------------- parsing


def _events(stdout: str):
    for line in (stdout or "").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def parse(agent: str, stdout: str, stderr: str, out_dir: str) -> AgentReport:
    rep = AgentReport()
    if agent == "codex":
        _parse_codex(rep, stdout)
        last = Path(out_dir) / "last_message.txt"
        if last.is_file():
            rep.final_message = last.read_text(encoding="utf-8", errors="replace").strip() or rep.final_message
    elif agent == "claude_code":
        _parse_claude(rep, stdout)
    else:
        _parse_generic(rep, stdout)
    if not rep.final_message and stdout and not stdout.lstrip().startswith("{"):
        rep.final_message = stdout.strip()[-4000:]
    err = (stderr or "").strip()
    if err:
        rep.errors.append(err[-800:])
    return rep


def _parse_codex(rep: AgentReport, stdout: str) -> None:
    for ev in _events(stdout):
        rep.events += 1
        kind = ev.get("type") or ""
        item = ev.get("item") or {}
        itype = item.get("type") or item.get("item_type") or ""
        if kind in ("thread.started", "session.created") and not rep.session_id:
            rep.session_id = str(ev.get("thread_id") or ev.get("session_id") or "")
        if kind == "item.completed" and itype == "command_execution":
            rep.commands.append({"command": str(item.get("command") or "")[:300],
                                 "exit_code": item.get("exit_code"), "reported_by": "agent"})
        elif kind == "item.completed" and itype == "file_change":
            for ch in item.get("changes") or []:
                rep.files_reported.append(str(ch.get("path") or ""))
        elif kind == "item.completed" and itype in ("agent_message", "assistant_message"):
            rep.final_message = str(item.get("text") or rep.final_message)
        elif kind == "turn.completed":
            rep.usage = ev.get("usage") or rep.usage
        elif kind in ("error", "turn.failed"):
            rep.errors.append(str(ev.get("message") or ev.get("error") or ev)[:400])


def _parse_claude(rep: AgentReport, stdout: str) -> None:
    for ev in _events(stdout):
        rep.events += 1
        kind = ev.get("type")
        if kind == "system" and ev.get("subtype") == "init":
            rep.session_id = str(ev.get("session_id") or "")
        elif kind == "assistant":
            for block in (ev.get("message") or {}).get("content") or []:
                if block.get("type") != "tool_use":
                    continue
                name = block.get("name") or ""
                inp = block.get("input") or {}
                if name in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
                    rep.files_reported.append(str(inp.get("file_path") or inp.get("notebook_path") or ""))
                elif name == "Bash":
                    rep.commands.append({"command": str(inp.get("command") or "")[:300], "reported_by": "agent"})
        elif kind == "result":
            rep.final_message = str(ev.get("result") or "")
            rep.session_id = str(ev.get("session_id") or rep.session_id)
            rep.usage = {
                "num_turns": ev.get("num_turns"),
                "duration_ms": ev.get("duration_ms"),
                "reported_cost_usd": ev.get("total_cost_usd"),
                "usage": ev.get("usage"),
            }
            if ev.get("is_error") or (ev.get("subtype") not in (None, "success")):
                rep.errors.append(f"result: {ev.get('subtype')}")


def _parse_generic(rep: AgentReport, stdout: str) -> None:
    for ev in _events(stdout):
        rep.events += 1
        for key in ("result", "response", "text", "message", "content"):
            val = ev.get(key)
            if isinstance(val, str) and val.strip():
                rep.final_message = val
        if ev.get("type") in ("error",) or ev.get("is_error"):
            rep.errors.append(str(ev)[:400])
        sid = ev.get("session_id") or ev.get("conversation_id")
        if sid:
            rep.session_id = str(sid)


_CLAIM = re.compile(
    r"(?im)^[^\n]*\b(?:all\s+tests\s+pass|tests?\s+(?:now\s+)?pass(?:es|ed|ing)?|fixed|resolved|implemented|"
    r"verified|works\s+now|completed?|done)\b[^\n]*$"
)


def claims(final_message: str, *, limit: int = 8) -> list[str]:
    """Statements of success in the agent's own report — unverified by definition."""
    found = []
    for m in _CLAIM.finditer(final_message or ""):
        line = m.group(0).strip(" -*•\t")
        if line and line not in found:
            found.append(line[:240])
        if len(found) >= limit:
            break
    return found
