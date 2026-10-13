#!/usr/bin/env python3
"""Simulated coding-agent CLI for tests and the harness dry-run.

Installed under the names ``codex``, ``claude`` and ``agy`` in a temp bin
directory; ``behaviour.json`` next to it scripts what it does. It answers
``--version``, ``--help`` (listing the flags the real CLIs have) and the
auth-status commands, and otherwise acts as one agent run in its cwd:

  {"edits": {"path": "content"}, "write_outside": "/abs/path", "sleep": 0,
   "exit": 0, "message": "final report", "commands": ["pytest -q"],
   "touch_config": "/abs/path", "logged_in": true, "auth": "chatgpt"}
"""

import json
import os
import sys
import time
from pathlib import Path

HERE = Path(os.path.abspath(sys.argv[0])).parent  # the symlink's dir, where behaviour.json is
NAME = Path(sys.argv[0]).name
B = json.loads((HERE / "behaviour.json").read_text()) if (HERE / "behaviour.json").exists() else {}
args = sys.argv[1:]

HELP = {
    "codex": "Usage: codex exec --json --sandbox --cd --ephemeral --output-last-message --color -c, --config",
    "claude": "Usage: claude --print --output-format --permission-mode --tools --no-session-persistence --verbose",
    "agy": "Usage of agy: --print --output-format --mode --sandbox --print-timeout",
}

if "--version" in args:
    print({"codex": "codex-cli 0.0-fake", "claude": "0.0-fake (Claude Code)", "agy": "0.0-fake"}[NAME])
    sys.exit(0)
if "--help" in args:
    print(HELP[NAME])
    sys.exit(0)
if NAME == "codex" and args[:2] == ["login", "status"]:
    print("Logged in using ChatGPT" if B.get("logged_in", True) else "Not logged in")
    sys.exit(0)
if NAME == "claude" and args[:2] == ["auth", "status"]:
    print(json.dumps({"loggedIn": B.get("logged_in", True), "authMethod": B.get("auth", "claude.ai"),
                      "subscriptionType": "pro", "email": "someone@example.com"}))
    sys.exit(0)

# ---- one run
if B.get("marker"):
    try:
        with open(B["marker"], "a") as fh:
            fh.write(f"{NAME} {time.time()}\n")
    except OSError:
        pass
for rel, content in (B.get("edits") or {}).items():
    p = Path.cwd() / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
outside_error = ""
for target in filter(None, [B.get("write_outside"), B.get("touch_config")]):
    try:
        with open(target, "a") as fh:
            fh.write("agent was here\n")
    except OSError as exc:
        outside_error = f"{type(exc).__name__}"
if B.get("read_outside"):
    try:
        B["message"] = "READ:" + open(B["read_outside"]).read().strip()
    except OSError as exc:
        B["message"] = f"READFAIL:{type(exc).__name__}"
if B.get("connect_host"):
    import socket
    try:
        with socket.create_connection(tuple(B["connect_host"]), timeout=1):
            B["message"] = "NETWORK_ESCAPE"
    except OSError as exc:
        B["message"] = f"NETFAIL:{type(exc).__name__}"
if B.get("sleep"):
    time.sleep(float(B["sleep"]))
if B.get("refresh_auth_file"):
    Path(B["refresh_auth_file"]).write_text(json.dumps({"access_token": B["refreshed_token"]}))
msg = B.get("message", "Done. All tests pass.")
if NAME == "codex":
    out = None
    if "--output-last-message" in args:
        out = args[args.index("--output-last-message") + 1]
    print(json.dumps({"type": "thread.started", "thread_id": "fake-thread"}))
    for c in B.get("commands") or []:
        print(json.dumps({"type": "item.completed", "item": {"type": "command_execution", "command": c, "exit_code": 0}}))
    for rel in B.get("edits") or {}:
        print(json.dumps({"type": "item.completed", "item": {"type": "file_change", "changes": [{"path": rel}]}}))
    print(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": msg}}))
    print(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 100, "output_tokens": 20}}))
    if out:
        Path(out).write_text(msg)
elif NAME == "claude":
    print(json.dumps({"type": "system", "subtype": "init", "session_id": "fake-session"}))
    for rel in B.get("edits") or {}:
        print(json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Edit", "input": {"file_path": rel}}]}}))
    print(json.dumps({"type": "result", "subtype": "success", "result": msg, "session_id": "fake-session",
                      "num_turns": 2, "total_cost_usd": 0.0}))
else:  # agy 1.x stream-json
    print(json.dumps({"event": "init", "init": {"cwd": os.getcwd(), "permission_mode": "always-proceed"}}))
    for rel in B.get("edits") or {}:
        print(json.dumps({"event": "step_update", "step_update": {
            "conversation_id": "fake-conv", "state": "DONE", "step_type": "tool", "tool_name": "write_to_file",
            "tool_info": {"name": "write_to_file", "parameters": {"TargetFile": str(Path.cwd() / rel)}}}}))
    print(json.dumps({"event": "result", "result": {"conversation_id": "fake-conv", "status": "SUCCESS",
                                                   "response": msg, "usage": {"total_tokens": 10}}}))
if outside_error:
    print(f"outside write blocked: {outside_error}", file=sys.stderr)
sys.exit(int(B.get("exit", 0)))
