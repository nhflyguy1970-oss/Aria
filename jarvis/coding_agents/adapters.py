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
            # Per-invocation only (the owner's config is untouched): Codex's own
            # cross-session memories would mix other projects into this run.
            "-c", "memories.use_memories=false", "-c", "memories.generate_memories=false",
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
        if last.is_file() and not last.is_symlink() and last.resolve().parent == Path(out_dir).resolve() and last.stat().st_size <= 4_000_000:
            rep.final_message = last.read_text(encoding="utf-8", errors="replace").strip() or rep.final_message
    elif agent == "claude_code":
        _parse_claude(rep, stdout)
    elif agent == "antigravity":
        _parse_agy(rep, stdout)
    else:
        _parse_generic(rep, stdout)
    if not rep.final_message and stdout and not stdout.lstrip().startswith("{"):
        rep.final_message = stdout.strip()[-4000:]
    err = "\n".join(line for line in (stderr or "").splitlines()
                    if line.strip() and not line.startswith("Reading additional input from stdin")).strip()
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
        elif kind in ("turn.completed", "usage.updated"):
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


_AGY_EDIT_TOOLS = ("write_to_file", "replace_file_content", "multi_replace_file_content", "sed_file", "notebook_edit")


def _parse_agy(rep: AgentReport, stdout: str) -> None:
    """agy 1.x stream-json: {"event": kind, kind: {...}}; final {"event": "result"}."""
    text_parts: list[str] = []
    for ev in _events(stdout):
        rep.events += 1
        kind = ev.get("event") or ""
        body = ev.get(kind) if isinstance(ev.get(kind), dict) else {}
        if kind == "init":
            rep.usage["permission_mode"] = body.get("permission_mode")
        elif kind == "step_update":
            rep.session_id = rep.session_id or str(body.get("conversation_id") or "")
            if body.get("step_type") == "agent_response" and body.get("text_delta"):
                text_parts.append(str(body["text_delta"]))
            if body.get("step_type") == "tool" and body.get("state") in ("DONE", "ERROR"):
                info = body.get("tool_info") or {}
                params = info.get("parameters") or {}
                name = str(body.get("tool_name") or info.get("name") or "")
                if name == "run_command":
                    rep.commands.append({"command": str(params.get("CommandLine") or "")[:300],
                                         "exit_code": None if body.get("state") == "DONE" else "error",
                                         "reported_by": "agent"})
                elif name in _AGY_EDIT_TOOLS:
                    rep.files_reported.append(str(params.get("TargetFile") or params.get("AbsolutePath")
                                                  or params.get("FilePath") or ""))
                if body.get("state") == "ERROR":
                    rep.errors.append(f"{name}: {str((info.get('error') or {}).get('message') or '')[:200]}")
        elif kind == "result":
            rep.session_id = str(body.get("conversation_id") or rep.session_id)
            rep.final_message = str(body.get("response") or "")
            rep.usage.update({"usage": body.get("usage"), "duration_s": body.get("duration_seconds"),
                              "num_turns": body.get("num_turns"), "status": body.get("status")})
            if str(body.get("status") or "").upper() not in ("SUCCESS", ""):
                rep.errors.append(f"result: {body.get('status')}")
    if not rep.final_message and text_parts:
        rep.final_message = "".join(text_parts)


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


def error_class(report: AgentReport, *, exit_code: int, timed_out: bool = False, cancelled: bool = False) -> str:
    if cancelled:
        return "cancelled"
    if timed_out:
        return "timeout"
    text = (" ".join(report.errors) + " " + report.final_message).lower()
    if any(word in text for word in ("weekly limit", "usage limit", "quota exceeded", "resource_exhausted", "usage_limit_reached", "quota exhausted", "rate_limit", "rate limit", "seven_day")):
        return "subscription_quota"
    if any(word in text for word in ("authentication", "not logged in", "login required", "please log in", "unauthorized")):
        return "authentication"
    if any(word in text for word in ("namespace", "sandbox", "operation not permitted")) and exit_code:
        return "isolation_compatibility"
    if any(word in text for word in ("connection", "network", "provider", "tls")) and exit_code:
        return "transport"
    return "execution" if exit_code or report.errors else ""
