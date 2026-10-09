"""Standalone, read-only installed worker inside the OCI sandbox (stdlib only)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from pathlib import Path

from transport import bridge


def emit(value):
    print(json.dumps(value), flush=True)


def main():
    request = json.loads(Path(sys.argv[1]).read_text())

    # PID 1 exiting tears down the entire private process namespace, including
    # detached children. This ceiling survives loss of the host supervisor.
    def expired():
        emit({"type": "error", "message": "isolated execution wall timeout"})
        os._exit(124)

    timer = threading.Timer(max(1, min(3600, int(request.get("timeout_s", 900)))), expired)
    timer.daemon = True
    timer.start()
    server, proxy = bridge("/run/aria-subscription.sock")
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
        os.environ[key] = proxy
    os.environ["NO_PROXY"] = ""
    if request["agent"] != "codex":
        process = subprocess.Popen(request["argv"], stdout=subprocess.PIPE, text=True)
        for line in process.stdout:
            print(line, end="", flush=True)
        process.wait()
        server.shutdown()
        return process.returncode
    process = subprocess.Popen(
        [
            request["binary"],
            "app-server",
            "--listen",
            "stdio://",
            "-c",
            "memories.use_memories=false",
            "-c",
            "memories.generate_memories=false",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    sequence = 0

    def send(method, params=None, identity=None):
        message = {"method": method}
        if params is not None:
            message["params"] = params
        if identity is not None:
            message["id"] = identity
        process.stdin.write(json.dumps(message) + "\n")
        process.stdin.flush()

    def incoming():
        line = process.stdout.readline()
        if not line:
            raise RuntimeError("app-server exited before a terminal response")
        return json.loads(line)

    def call(method, params):
        nonlocal sequence
        sequence += 1
        send(method, params, sequence)
        while True:
            message = incoming()
            if message.get("id") == sequence:
                if "error" in message:
                    raise RuntimeError(str(message["error"]))
                return message["result"]

    try:
        call(
            "initialize",
            {
                "clientInfo": {"name": "aria-phase6", "version": "1"},
                "capabilities": {"experimentalApi": True},
            },
        )
        send("initialized")
        # Certification commands exercise the real installed app-server without
        # a model request. This file is supplied only by the trusted controller.
        if "command" in request:
            result = call(
                "command/exec",
                {
                    "command": request["command"],
                    "cwd": request["cwd"],
                    "sandboxPolicy": {"type": "externalSandbox", "networkAccess": "enabled"},
                    "timeoutMs": 10000,
                },
            )
            emit({"type": "certification.command", "result": result})
            return result["exitCode"]
        account = call("account/read", {"refreshToken": False}).get("account") or {}
        if account.get("type") != "chatgpt":
            raise RuntimeError(
                "subscription authentication is not confirmed; refusing a model request"
            )
        thread = call(
            "thread/start",
            {
                "cwd": request["cwd"],
                "ephemeral": True,
                "approvalPolicy": "never",
                "sandbox": "read-only",
            },
        )["thread"]["id"]
        emit({"type": "thread.started", "thread_id": thread})
        call(
            "turn/start",
            {
                "threadId": thread,
                "cwd": request["cwd"],
                "approvalPolicy": "never",
                "sandboxPolicy": {"type": "externalSandbox", "networkAccess": "enabled"},
                "input": [{"type": "text", "text": request["prompt"], "text_elements": []}],
            },
        )
        final = ""
        while True:
            message = incoming()
            method, params = message.get("method", ""), message.get("params") or {}
            if "id" in message and method:
                # No server request grants authority beyond the approved task.
                process.stdin.write(
                    json.dumps({"id": message["id"], "result": {"decision": "decline"}}) + "\n"
                )
                process.stdin.flush()
            if method == "item/completed":
                item = params.get("item") or {}
                kind = item.get("type")
                if kind == "agentMessage":
                    final = item.get("text", "")
                    emit(
                        {"type": "item.completed", "item": {"type": "agent_message", "text": final}}
                    )
                elif kind == "commandExecution":
                    emit(
                        {
                            "type": "item.completed",
                            "item": {
                                "type": "command_execution",
                                "command": item.get("command"),
                                "aggregated_output": item.get("aggregatedOutput"),
                                "exit_code": item.get("exitCode"),
                            },
                        }
                    )
                elif kind == "fileChange":
                    emit(
                        {
                            "type": "item.completed",
                            "item": {"type": "file_change", "changes": item.get("changes", [])},
                        }
                    )
            elif method == "item/agentMessage/delta":
                emit({"type": "item.delta", "delta": params.get("delta", "")})
            elif method == "thread/tokenUsage/updated":
                usage = (
                    (params.get("tokenUsage") or {}).get("total")
                    or (params.get("tokenUsage") or {}).get("last")
                    or {}
                )
                emit(
                    {
                        "type": "usage.updated",
                        "usage": {
                            "input_tokens": usage.get("inputTokens"),
                            "cached_input_tokens": usage.get("cachedInputTokens"),
                            "output_tokens": usage.get("outputTokens"),
                        },
                    }
                )
            elif method == "error":
                emit(
                    {
                        "type": "error",
                        "message": (params.get("error") or {}).get("message", "provider error"),
                    }
                )
            elif method == "turn/completed":
                turn = params.get("turn") or {}
                if turn.get("status") != "completed":
                    emit(
                        {
                            "type": "turn.failed",
                            "error": turn.get("error") or {"message": turn.get("status")},
                        }
                    )
                    return 1
                Path(request["out_dir"], "last_message.txt").write_text(final)
                emit({"type": "turn.completed"})
                return 0
    finally:
        process.kill()
        process.wait(timeout=5)
        server.shutdown()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        emit({"type": "error", "message": str(exc)})
        raise SystemExit(1)
