"""OpenAI Responses API adapter (``POST /v1/responses``).

``store: false`` is always sent: ARIA keeps its own history and does not ask
OpenAI to retain conversation state. Completion is decided by the response's
``status`` (``completed`` / ``incomplete`` / ``failed``), never by text alone.
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
    Request,
    Result,
    ToolCall,
    Usage,
    split_system,
    sse_events,
    tool_args,
)


class OpenAIResponses(ProviderAdapter):
    provider = "openai"
    label = "OpenAI"
    credential_field = "openai_api_key"
    base_url = "https://api.openai.com/v1"

    def headers(self, key: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    @property
    def subscription(self) -> bool:
        from jarvis.inference.chatgpt_oauth import enabled
        return enabled()

    @property
    def billing(self) -> str:
        return "chatgpt_subscription" if self.subscription else "api"

    def credential(self) -> str:
        if self.subscription:
            from jarvis.inference.chatgpt_oauth import access_token
            return access_token()  # Never fall back to the API key.
        return super().credential()

    def credential_status(self) -> dict[str, Any]:
        if self.subscription:
            from jarvis.inference.chatgpt_oauth import status
            return status()
        return super().credential_status()

    # ---- request ------------------------------------------------------

    def _input(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for m in messages:
            role = m.get("role")
            if role == "tool":
                items.append(
                    {
                        "type": "function_call_output",
                        "call_id": m.get("tool_call_id") or "",
                        "output": str(m.get("content") or ""),
                    }
                )
                continue
            if role == "assistant" and m.get("tool_calls"):
                if m.get("content"):
                    items.append({"role": "assistant", "content": str(m["content"])})
                for call in m["tool_calls"]:
                    items.append(
                        {
                            "type": "function_call",
                            "call_id": call.get("id") or "",
                            "name": call.get("name") or "",
                            "arguments": json.dumps(call.get("arguments") or {}),
                        }
                    )
                continue
            if role in ("user", "assistant"):
                items.append({"role": role, "content": str(m.get("content") or "")})
        return items

    def _body(self, request: Request, *, stream: bool) -> dict[str, Any]:
        system, rest = split_system(request.messages)
        body: dict[str, Any] = {
            "model": request.model,
            "input": self._input(rest),
            "max_output_tokens": request.max_output_tokens,
            "store": False,
            "stream": stream,
        }
        if system:
            body["instructions"] = system
        if request.temperature is not None:
            body["temperature"] = request.temperature
        if request.tools:
            body["tools"] = [
                {
                    "type": "function",
                    "name": t["function"]["name"],
                    "description": t["function"].get("description", ""),
                    "parameters": t["function"].get("parameters") or {"type": "object"},
                }
                for t in request.tools
            ]
        if self.subscription:
            body.pop("max_output_tokens", None)
            body.pop("temperature", None)
            body["stream"] = True
            if request.tools:
                body["tools"] = [{"type": "namespace", "name": "aria", "description": "ARIA local tools",
                                  "tools": body["tools"]}]
        return body

    # ---- response -----------------------------------------------------

    @staticmethod
    def _finish(data: dict[str, Any], calls: list[ToolCall]) -> str:
        status = data.get("status")
        if status == "failed":
            err = (data.get("error") or {}).get("message") or "response failed"
            raise boundary.ProviderUnavailable(f"OpenAI: {err}")
        if status == "incomplete":
            reason = (data.get("incomplete_details") or {}).get("reason") or ""
            return "filtered" if reason == "content_filter" else "length"
        if status != "completed":
            raise boundary.ProviderUnavailable(f"OpenAI: response not completed (status={status!r})")
        return "tool_calls" if calls else "stop"

    @staticmethod
    def _parse_output(data: dict[str, Any]) -> tuple[str, list[ToolCall]]:
        texts: list[str] = []
        calls: list[ToolCall] = []
        for item in data.get("output") or []:
            if item.get("type") == "message":
                for part in item.get("content") or []:
                    if part.get("type") == "output_text":
                        texts.append(part.get("text") or "")
            elif item.get("type") == "function_call":
                calls.append(
                    ToolCall(
                        id=item.get("call_id") or item.get("id") or "",
                        name=item.get("name") or "",
                        arguments=tool_args(item.get("arguments")),
                    )
                )
        return "".join(texts), calls

    def chat(self, request: Request) -> Result:
        if self.subscription:
            # Plan usage requires SSE even for callers asking for one result.
            texts, calls, usage, finish, model = [], [], Usage(), "", request.model
            for event in self.stream(request):
                if event.type == "text":
                    texts.append(event.text)
                elif event.type == "tool_call" and event.tool_call:
                    calls.append(event.tool_call)
                elif event.type == "usage" and event.usage:
                    usage = event.usage
                elif event.type == "done":
                    finish, model = event.finish, event.model or model
            return Result(text="".join(texts), tool_calls=calls, usage=usage, finish=finish, model=model)
        def call():
            resp = self._send(
                "POST", "/responses", body=self._body(request, stream=False),
                timeout=request.timeout, model=request.model,
            )
            return json.loads(resp.read().decode("utf-8")), resp

        data, resp = self._with_retries(call, cancel_check=request.cancel_check)
        text, calls = self._parse_output(data)
        usage = data.get("usage") or {}
        return Result(
            text=text,
            tool_calls=calls,
            usage=Usage(usage.get("input_tokens"), usage.get("output_tokens")),
            finish=self._finish(data, calls),
            model=data.get("model") or request.model,
            provider_request_id=str(data.get("id") or ""),
        )

    def stream(self, request: Request) -> Iterator[Event]:
        resp = self._with_retries(
            lambda: self._send(
                "POST", "/responses", body=self._body(request, stream=True),
                timeout=request.timeout, model=request.model,
            ),
            cancel_check=request.cancel_check,
        )
        calls: dict[str, ToolCall] = {}
        for name, data in sse_events(resp):
            if request.cancel_check is not None and request.cancel_check():
                _close(resp)
                raise boundary.InferenceCancelled("OpenAI: cancelled")
            kind = data.get("type") or name
            if kind == "response.output_text.delta":
                yield Event("text", text=data.get("delta") or "")
            elif kind == "response.output_item.done":
                item = data.get("item") or {}
                if item.get("type") == "function_call":
                    call = ToolCall(
                        id=item.get("call_id") or item.get("id") or "",
                        name=item.get("name") or "",
                        arguments=tool_args(item.get("arguments")),
                    )
                    calls[call.id] = call
                    yield Event("tool_call", tool_call=call)
            elif kind in ("response.completed", "response.incomplete", "response.failed"):
                final = data.get("response") or {}
                usage = final.get("usage") or {}
                yield Event("usage", usage=Usage(usage.get("input_tokens"), usage.get("output_tokens")))
                yield Event(
                    "done",
                    finish=self._finish(final, list(calls.values())),
                    model=final.get("model") or request.model,
                )
                return
            elif kind == "error":
                raise BadRequest(f"OpenAI stream error: {(data.get('message') or '')[:200]}")
        raise boundary.ProviderUnavailable("OpenAI: stream ended without a terminal event")

    def discover(self) -> list[ModelInfo]:
        resp = self._with_retries(lambda: self._send("GET", "/models", timeout=20, purpose="discovery"))
        data = json.loads(resp.read().decode("utf-8"))
        if self.subscription:
            return [ModelInfo(id=m["slug"], provider=self.provider, display_name=m.get("display_name", ""))
                    for m in data.get("models") or [] if m.get("slug") and m.get("visibility") == "list"]
        # The models endpoint lists ids only; capabilities stay unknown rather
        # than guessed from names.
        return [ModelInfo(id=m["id"], provider=self.provider) for m in data.get("data") or [] if m.get("id")]


def _close(resp) -> None:
    close = getattr(resp, "close", None)
    if close:
        try:
            close()
        except Exception:  # noqa: BLE001
            pass
