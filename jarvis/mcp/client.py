"""MCP client sessions — the real protocol, via the official SDK.

Nothing here reimplements MCP. Connection, handshake, capability negotiation
and framing all come from `mcp`; this module supplies the parts ARIA needs
around it: a bounded synchronous bridge, an approved-launch path for stdio
providers, size limits, and the rule that a provider's output is data rather
than instruction.

Sessions are per-operation on purpose. A long-lived provider subprocess is an
orphan waiting to happen, so a session is opened, used and shut down inside one
async context, and a failure to connect is reported rather than retried forever.
"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
from concurrent.futures import Future
from typing import Any

from jarvis.mcp import definitions as defs

log = logging.getLogger("jarvis.mcp.client")


class McpUnavailable(RuntimeError):
    """The provider could not be reached, launched or initialized."""


class McpProtocolError(RuntimeError):
    """The provider answered, but not in a way MCP allows."""


class McpTimeout(TimeoutError):
    """ARIA stopped waiting. The remote may or may not still be running."""


# --------------------------------------------------------------- async bridge


class _Runner:
    """One background event loop for all MCP work.

    ARIA's action handlers are synchronous and may themselves be running inside
    FastAPI's threadpool, so starting a loop inline is not safe. A dedicated
    loop thread keeps MCP's async machinery away from the server's own loop and
    makes every wait explicitly bounded.
    """

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.RLock()

    def _ensure(self) -> asyncio.AbstractEventLoop:
        with self._lock:
            if self._loop and self._thread and self._thread.is_alive():
                return self._loop
            loop = asyncio.new_event_loop()

            def _run() -> None:
                asyncio.set_event_loop(loop)
                loop.run_forever()

            thread = threading.Thread(target=_run, name="aria-mcp", daemon=True)
            thread.start()
            self._loop, self._thread = loop, thread
            return loop

    def run(self, coro, timeout: float):
        """Run a coroutine, waiting at most `timeout` seconds."""
        loop = self._ensure()
        future: Future = asyncio.run_coroutine_threadsafe(coro, loop)
        try:
            return future.result(timeout=timeout)
        except TimeoutError as exc:
            # Stop waiting, and ask the remote side to stop too. Whether it
            # actually stops is the provider's business, not something to claim.
            future.cancel()
            raise McpTimeout(f"MCP operation exceeded {timeout}s") from exc


_runner = _Runner()


def run_bounded(coro, timeout: float):
    return _runner.run(coro, timeout)


# ------------------------------------------------------------------ transport


def _stdio_env(defn: defs.ProviderDefinition) -> dict[str, str]:
    """A deliberately small environment.

    A provider inherits only what it needs to run, never ARIA's whole
    environment, so tokens held for other integrations cannot leak into a
    third-party process.
    """
    keep = ("PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "SYSTEMROOT")
    env = {k: os.environ[k] for k in keep if k in os.environ}
    env.update({k: v for k, v in defn.env})
    return env


def _client_context(defn: defs.ProviderDefinition):
    """Build the SDK client context manager for this provider's transport."""
    if defn.transport == defs.STDIO:
        from mcp import StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(
            command=defn.command[0],
            args=list(defn.command[1:]),
            env=_stdio_env(defn),
            cwd=defn.cwd or None,
        )
        return stdio_client(params)
    if defn.transport == defs.HTTP:
        from mcp.client.streamable_http import streamablehttp_client

        return streamablehttp_client(defn.url)
    if defn.transport == defs.SSE:
        from mcp.client.sse import sse_client

        return sse_client(defn.url)
    raise McpUnavailable(f"transport {defn.transport!r} is not supported by the installed MCP SDK")


async def _session(defn: defs.ProviderDefinition):
    """Yield an initialized ClientSession. Caller must use `async with`."""
    from mcp import ClientSession

    return _SessionContext(defn, ClientSession)


class _SessionContext:
    """Connect → initialize → (use) → shut down, as one bounded scope."""

    def __init__(self, defn: defs.ProviderDefinition, session_cls) -> None:
        self.defn = defn
        self._session_cls = session_cls
        self._transport = None
        self._session = None
        self.capabilities: dict[str, Any] = {}
        self.server_info: dict[str, Any] = {}

    async def __aenter__(self):
        self._transport = _client_context(self.defn)
        streams = await self._transport.__aenter__()
        # streamablehttp_client yields a third element (a session id callback).
        read_stream, write_stream = streams[0], streams[1]
        self._session = self._session_cls(read_stream, write_stream)
        await self._session.__aenter__()
        init = await asyncio.wait_for(
            self._session.initialize(), timeout=defs.BOUNDS["init_timeout_s"]
        )
        caps = getattr(init, "capabilities", None)
        self.capabilities = {
            "tools": bool(getattr(caps, "tools", None)),
            "resources": bool(getattr(caps, "resources", None)),
            "prompts": bool(getattr(caps, "prompts", None)),
            "logging": bool(getattr(caps, "logging", None)),
        }
        info = getattr(init, "serverInfo", None)
        self.server_info = {
            "name": getattr(info, "name", "") or "",
            "version": getattr(info, "version", "") or "",
            "protocol_version": str(getattr(init, "protocolVersion", "") or ""),
        }
        return self

    async def __aexit__(self, *exc):
        # Shut down in reverse order; a failure to close must not mask the
        # original error, but must also not leave a subprocess behind.
        try:
            if self._session is not None:
                await self._session.__aexit__(*exc)
        except Exception:  # noqa: BLE001
            log.debug("MCP session close failed for %s", self.defn.provider_id, exc_info=True)
        try:
            if self._transport is not None:
                await self._transport.__aexit__(*exc)
        except Exception:  # noqa: BLE001
            log.debug("MCP transport close failed for %s", self.defn.provider_id, exc_info=True)
        return False

    @property
    def session(self):
        if self._session is None:
            raise McpUnavailable("session is not open")
        return self._session


# ------------------------------------------------------------------ operations


async def _describe(defn: defs.ProviderDefinition) -> dict[str, Any]:
    ctx = await _session(defn)
    async with ctx:
        out: dict[str, Any] = {
            "server_info": ctx.server_info,
            "capabilities": ctx.capabilities,
            "tools": [],
            "resources": [],
            "prompts": [],
        }
        if ctx.capabilities.get("tools"):
            listed = await ctx.session.list_tools()
            out["tools"] = [
                {
                    "name": t.name,
                    "description": (t.description or "")[:2000],
                    "input_schema": getattr(t, "inputSchema", None) or {},
                }
                for t in (listed.tools or [])
            ]
        if ctx.capabilities.get("resources"):
            try:
                res = await ctx.session.list_resources()
                out["resources"] = [
                    {
                        "uri": str(r.uri),
                        "name": getattr(r, "name", "") or "",
                        "description": (getattr(r, "description", "") or "")[:1000],
                        "mime_type": getattr(r, "mimeType", "") or "",
                    }
                    for r in (res.resources or [])
                ]
            except Exception as exc:  # noqa: BLE001 - a provider may advertise and refuse
                log.info("resource listing failed for %s: %s", defn.provider_id, exc)
        if ctx.capabilities.get("prompts"):
            try:
                pr = await ctx.session.list_prompts()
                out["prompts"] = [
                    {
                        "name": p.name,
                        "description": (getattr(p, "description", "") or "")[:1000],
                        "arguments": [
                            {"name": a.name, "required": bool(getattr(a, "required", False))}
                            for a in (getattr(p, "arguments", None) or [])
                        ],
                    }
                    for p in (pr.prompts or [])
                ]
            except Exception as exc:  # noqa: BLE001
                log.info("prompt listing failed for %s: %s", defn.provider_id, exc)
        return out


async def _call_tool(
    defn: defs.ProviderDefinition, tool: str, arguments: dict[str, Any], timeout: float
) -> dict[str, Any]:
    ctx = await _session(defn)
    async with ctx:
        result = await asyncio.wait_for(ctx.session.call_tool(tool, arguments), timeout=timeout)
        return _tool_result(result)


async def _read_resource(defn: defs.ProviderDefinition, uri: str, timeout: float) -> dict[str, Any]:
    ctx = await _session(defn)
    async with ctx:
        result = await asyncio.wait_for(ctx.session.read_resource(uri), timeout=timeout)
        contents = []
        for item in getattr(result, "contents", None) or []:
            contents.append(
                {
                    "uri": str(getattr(item, "uri", "") or uri),
                    "mime_type": getattr(item, "mimeType", "") or "",
                    "text": getattr(item, "text", None),
                    "blob": bool(getattr(item, "blob", None)),
                }
            )
        return {"uri": uri, "contents": contents}


async def _get_prompt(
    defn: defs.ProviderDefinition, name: str, arguments: dict[str, Any], timeout: float
) -> dict[str, Any]:
    ctx = await _session(defn)
    async with ctx:
        result = await asyncio.wait_for(
            ctx.session.get_prompt(name, arguments or {}), timeout=timeout
        )
        messages = []
        for m in getattr(result, "messages", None) or []:
            content = getattr(m, "content", None)
            messages.append(
                {
                    "role": str(getattr(m, "role", "") or ""),
                    "text": getattr(content, "text", None) or "",
                }
            )
        return {
            "name": name,
            "description": (getattr(result, "description", "") or "")[:1000],
            "messages": messages,
        }


def _tool_result(result: Any) -> dict[str, Any]:
    """Normalise an MCP tool result into plain, inspectable data."""
    blocks = []
    for item in getattr(result, "content", None) or []:
        kind = getattr(item, "type", "") or ""
        if kind == "text":
            blocks.append({"type": "text", "text": getattr(item, "text", "") or ""})
        elif kind == "image":
            blocks.append({"type": "image", "mime_type": getattr(item, "mimeType", "") or ""})
        else:
            blocks.append({"type": kind or "unknown"})
    text = "\n".join(b.get("text", "") for b in blocks if b.get("type") == "text").strip()
    return {
        # A provider reporting its own failure is a failure, not a success with
        # sad-looking text.
        "is_error": bool(getattr(result, "isError", False)),
        "content": blocks,
        "text": text,
        "structured": getattr(result, "structuredContent", None),
    }


# ------------------------------------------------------------- sync entrypoints


def describe(defn: defs.ProviderDefinition, *, timeout: float | None = None) -> dict[str, Any]:
    """Handshake, capability negotiation and discovery in one bounded session."""
    limit = timeout or defs.BOUNDS["connect_timeout_s"]
    try:
        return run_bounded(_describe(defn), limit)
    except McpTimeout:
        raise
    except Exception as exc:  # noqa: BLE001 - a dead provider must not kill ARIA
        raise McpUnavailable(f"{defn.provider_id}: {type(exc).__name__}: {exc}") from exc


def call_tool(
    defn: defs.ProviderDefinition,
    tool: str,
    arguments: dict[str, Any] | None = None,
    *,
    timeout: float | None = None,
) -> dict[str, Any]:
    limit = timeout or defn.timeout_s or defs.BOUNDS["call_timeout_s"]
    try:
        return run_bounded(_call_tool(defn, tool, dict(arguments or {}), limit), limit + 5.0)
    except McpTimeout:
        raise
    except Exception as exc:  # noqa: BLE001
        raise McpUnavailable(f"{defn.provider_id}:{tool}: {type(exc).__name__}: {exc}") from exc


def read_resource(
    defn: defs.ProviderDefinition, uri: str, *, timeout: float | None = None
) -> dict[str, Any]:
    limit = timeout or defs.BOUNDS["resource_timeout_s"]
    try:
        return run_bounded(_read_resource(defn, uri, limit), limit + 5.0)
    except McpTimeout:
        raise
    except Exception as exc:  # noqa: BLE001
        raise McpUnavailable(f"{defn.provider_id}:{uri}: {type(exc).__name__}: {exc}") from exc


def get_prompt(
    defn: defs.ProviderDefinition,
    name: str,
    arguments: dict[str, Any] | None = None,
    *,
    timeout: float | None = None,
) -> dict[str, Any]:
    limit = timeout or defs.BOUNDS["call_timeout_s"]
    try:
        return run_bounded(_get_prompt(defn, name, dict(arguments or {}), limit), limit + 5.0)
    except McpTimeout:
        raise
    except Exception as exc:  # noqa: BLE001
        raise McpUnavailable(f"{defn.provider_id}:{name}: {type(exc).__name__}: {exc}") from exc
