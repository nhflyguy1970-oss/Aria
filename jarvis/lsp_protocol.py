"""LSP JSON-RPC over stdio (Content-Length framing)."""

from __future__ import annotations

import json
import select
import subprocess
import time
from dataclasses import dataclass
from typing import Any


class LspError(Exception):
    def __init__(self, message: str, *, code: int | None = None):
        super().__init__(message)
        self.code = code


class LspTimeout(LspError):
    pass


@dataclass
class LspProcess:
    proc: subprocess.Popen
    cmd: list[str]
    _req_id: int = 0

    @classmethod
    def start(cls, cmd: list[str], *, cwd: str | None = None) -> LspProcess:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=cwd,
            bufsize=0,
        )
        if not proc.stdin or not proc.stdout:
            raise LspError(f"Failed to start LSP: {cmd}")
        return cls(proc=proc, cmd=cmd)

    def send(self, message: dict) -> None:
        body = json.dumps(message, separators=(",", ":")).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        assert self.proc.stdin
        self.proc.stdin.write(header + body)
        self.proc.stdin.flush()

    def read(self, timeout: float = 1.0) -> dict | None:
        assert self.proc.stdout
        ready, _, _ = select.select([self.proc.stdout], [], [], max(0.0, timeout))
        if not ready:
            return None
        stream = self.proc.stdout
        headers: dict[str, str] = {}
        while True:
            line = stream.readline()
            if not line:
                return None
            decoded = line.decode("utf-8", errors="replace").strip()
            if not decoded:
                break
            if ":" in decoded:
                key, value = decoded.split(":", 1)
                headers[key.strip().lower()] = value.strip()
        length = int(headers.get("content-length", "0") or "0")
        if length <= 0:
            return None
        body = stream.read(length)
        if not body:
            return None
        return json.loads(body.decode("utf-8"))

    def request(self, method: str, params: dict | None, *, timeout: float = 30.0) -> Any:
        self._req_id += 1
        req_id = self._req_id
        self.send({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params or {}})
        deadline = time.time() + timeout
        while time.time() < deadline:
            msg = self.read(timeout=min(0.5, deadline - time.time()))
            if not msg:
                if self.proc.poll() is not None:
                    raise LspError(f"LSP exited: {' '.join(self.cmd)}")
                continue
            if msg.get("id") == req_id:
                if "error" in msg:
                    err = msg["error"]
                    raise LspError(str(err.get("message", err)), code=err.get("code"))
                return msg.get("result")
        raise LspTimeout(f"Timed out waiting for {method}")

    def notify(self, method: str, params: dict | None) -> None:
        self.send({"jsonrpc": "2.0", "method": method, "params": params or {}})

    def drain_notifications(self, *, timeout: float = 2.0) -> list[dict]:
        out: list[dict] = []
        deadline = time.time() + timeout
        while time.time() < deadline:
            msg = self.read(timeout=min(0.25, deadline - time.time()))
            if not msg:
                continue
            if "method" in msg and "id" not in msg:
                out.append(msg)
        return out

    def shutdown(self) -> None:
        try:
            self.request("shutdown", {}, timeout=5)
            self.notify("exit", {})
        except Exception:
            pass
        try:
            self.proc.terminate()
            self.proc.wait(timeout=2)
        except Exception:
            self.proc.kill()
