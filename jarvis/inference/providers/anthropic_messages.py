"""Anthropic Messages API adapter (``POST /v1/messages``).

Completion is decided by ``stop_reason`` (or ``message_stop`` in a stream);
a stream that stops without ``message_stop`` is an interruption.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

from jarvis.inference import boundary
from jarvis.inference.providers.base import (
    BadRequest,
    Event,
    ModelInfo,
    ProviderAdapter,
    ProviderOverloaded,
    Request,
    Result,
    ToolCall,
    Usage,
    split_system,
    sse_events,
    tool_args,
)
from jarvis.inference.providers.openai_responses import _close

API_VERSION = "2023-06-01"
_FINISH = {
    "end_turn": "stop",
    "stop_sequence": "stop",
    "tool_use": "tool_calls",
    "max_tokens": "length",
    "refusal": "filtered",
}


class AnthropicMessages(ProviderAdapter):
    provider = "anthropic"
    label = "Anthropic"
    credential_field = "anthropic_api_key"
    base_url = "https://api.anthropic.com/v1"

    def headers(self, key: str) -> dict[str, str]:
        return {
            "x-api-key": key,
            "anthropic-version": API_VERSION,
            "content-type": "application/json",
        }

    def _messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for m in messages:
            role = m.get("role")
            if role == "tool":
                block = {
                    "type": "tool_result",
                    "tool_use_id": m.get("tool_call_id") or "",
                    "content": str(m.get("content") or ""),
                }
                # Consecutive tool results belong to one user turn.
                if out and out[-1]["role"] == "user" and isinstance(out[-1]["content"], list) and all(
                    b.get("type") == "tool_result" for b in out[-1]["content"]
                ):
                    out[-1]["content"].append(block)
                else:
                    out.append({"role": "user", "content": [block]})
            elif role == "assistant" and m.get("tool_calls"):
                blocks: list[dict[str, Any]] = []
                if m.get("content"):
                    blocks.append({"type": "text", "text": str(m["content"])})
                for call in m["tool_calls"]:
                    blocks.append(
                        {
                            "type": "tool_use",
                            "id": call.get("id") or "",
                            "name": call.get("name") or "",
                            "input": call.get("arguments") or {},
                        }
                    )
                out.append({"role": "assistant", "content": blocks})
            elif role in ("user", "assistant"):
                out.append({"role": role, "content": str(m.get("content") or "")})
        return out

    def _body(self, request: Request, *, stream: bool) -> dict[str, Any]:
        system, rest = split_system(request.messages)
        body: dict[str, Any] = {
            "model": request.model,
            "max_tokens": request.max_output_tokens,
            "messages": self._messages(rest),
            "stream": stream,
        }
        if system:
            body["system"] = system
        if request.temperature is not None:
            body["temperature"] = request.temperature
        if request.tools:
            body["tools"] = [
                {
                    "name": t["function"]["name"],
                    "description": t["function"].get("description", ""),
                    "input_schema": t["function"].get("parameters") or {"type": "object"},
                }
                for t in request.tools
            ]
        return body

    @staticmethod
    def _finish(stop_reason: str | None) -> str:
        if stop_reason not in _FINISH:
            raise boundary.ProviderUnavailable(
                f"Anthropic: response ended without a known stop reason ({stop_reason!r})"
            )
        return _FINISH[stop_reason]

    def chat(self, request: Request) -> Result:
        def call():
            resp = self._send(
                "POST", "/messages", body=self._body(request, stream=False),
                timeout=request.timeout, model=request.model,
            )
            return json.loads(resp.read().decode("utf-8"))

        data = self._with_retries(call, cancel_check=request.cancel_check)
        texts, calls = [], []
        for block in data.get("content") or []:
            if block.get("type") == "text":
                texts.append(block.get("text") or "")
            elif block.get("type") == "tool_use":
                calls.append(ToolCall(block.get("id") or "", block.get("name") or "", tool_args(block.get("input"))))
        usage = data.get("usage") or {}
        return Result(
            text="".join(texts),
            tool_calls=calls,
            usage=Usage(usage.get("input_tokens"), usage.get("output_tokens")),
            finish=self._finish(data.get("stop_reason")),
            model=data.get("model") or request.model,
            provider_request_id=str(data.get("id") or ""),
        )

    def stream(self, request: Request) -> Iterator[Event]:
        resp = self._with_retries(
            lambda: self._send(
                "POST", "/messages", body=self._body(request, stream=True),
                timeout=request.timeout, model=request.model,
            ),
            cancel_check=request.cancel_check,
        )
        blocks: dict[int, dict[str, Any]] = {}
        input_tokens = output_tokens = None
        stop_reason = None
        model = request.model
        for name, data in sse_events(resp):
            if request.cancel_check is not None and request.cancel_check():
                _close(resp)
                raise boundary.InferenceCancelled("Anthropic: cancelled")
            kind = data.get("type") or name
            if kind == "message_start":
                msg = data.get("message") or {}
                model = msg.get("model") or model
                input_tokens = (msg.get("usage") or {}).get("input_tokens")
            elif kind == "content_block_start":
                block = dict(data.get("content_block") or {})
                block["_json"] = ""
                blocks[int(data.get("index") or 0)] = block
            elif kind == "content_block_delta":
                delta = data.get("delta") or {}
                block = blocks.setdefault(int(data.get("index") or 0), {"_json": ""})
                if delta.get("type") == "text_delta":
                    yield Event("text", text=delta.get("text") or "")
                elif delta.get("type") == "input_json_delta":
                    block["_json"] += delta.get("partial_json") or ""
            elif kind == "content_block_stop":
                block = blocks.get(int(data.get("index") or 0)) or {}
                if block.get("type") == "tool_use":
                    yield Event(
                        "tool_call",
                        tool_call=ToolCall(
                            block.get("id") or "", block.get("name") or "",
                            tool_args(block.get("_json") or block.get("input") or "{}"),
                        ),
                    )
            elif kind == "message_delta":
                stop_reason = (data.get("delta") or {}).get("stop_reason") or stop_reason
                output_tokens = (data.get("usage") or {}).get("output_tokens", output_tokens)
            elif kind == "message_stop":
                yield Event("usage", usage=Usage(input_tokens, output_tokens))
                yield Event("done", finish=self._finish(stop_reason), model=model)
                return
            elif kind == "error":
                err = data.get("error") or {}
                if err.get("type") == "overloaded_error":
                    raise ProviderOverloaded("Anthropic: overloaded")
                raise BadRequest(f"Anthropic stream error: {(err.get('message') or '')[:200]}")
        raise boundary.ProviderUnavailable("Anthropic: stream ended without message_stop")

    def discover(self) -> list[ModelInfo]:
        found: list[ModelInfo] = []
        after = ""
        for _page in range(10):
            path = "/models?limit=100" + (f"&after_id={after}" if after else "")
            resp = self._with_retries(lambda p=path: self._send("GET", p, timeout=20, purpose="discovery"))
            data = json.loads(resp.read().decode("utf-8"))
            for m in data.get("data") or []:
                caps = set()
                declared = m.get("capabilities") or {}
                for name, key in (("vision", "image_input"), ("tools", "tool_use"), ("thinking", "thinking")):
                    if isinstance(declared, dict) and declared.get(key):
                        caps.add(name)
                found.append(
                    ModelInfo(
                        id=m.get("id") or "",
                        provider=self.provider,
                        capabilities=frozenset(caps | ({"completion"} if caps else set())),
                        context_window=m.get("max_input_tokens"),
                        max_output_tokens=m.get("max_tokens"),
                        display_name=m.get("display_name") or "",
                    )
                )
            if not data.get("has_more"):
                break
            after = data.get("last_id") or ""
        return found
