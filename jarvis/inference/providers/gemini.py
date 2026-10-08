"""Google Gemini API adapter (``generateContent`` / ``streamGenerateContent``).

The API key travels in the ``x-goog-api-key`` header, never in the URL (URLs
end up in logs). Completion is decided by ``finishReason``; a stream whose last
chunk carries none is an interruption.
"""

from __future__ import annotations

import json
import urllib.parse
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
from jarvis.inference.providers.openai_responses import _close

_FINISH = {
    "STOP": "stop",
    "MAX_TOKENS": "length",
    "SAFETY": "filtered",
    "RECITATION": "filtered",
    "BLOCKLIST": "filtered",
    "PROHIBITED_CONTENT": "filtered",
    "SPII": "filtered",
}


class GeminiAPI(ProviderAdapter):
    provider = "google"
    label = "Gemini"
    credential_field = "gemini_api_key"
    base_url = "https://generativelanguage.googleapis.com/v1beta"

    def headers(self, key: str) -> dict[str, str]:
        return {"x-goog-api-key": key, "Content-Type": "application/json"}

    def _contents(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        names: dict[str, str] = {}
        out: list[dict[str, Any]] = []
        for m in messages:
            role = m.get("role")
            if role == "assistant" and m.get("tool_calls"):
                parts: list[dict[str, Any]] = []
                if m.get("content"):
                    parts.append({"text": str(m["content"])})
                for call in m["tool_calls"]:
                    names[call.get("id") or ""] = call.get("name") or ""
                    parts.append({"functionCall": {"name": call.get("name"), "args": call.get("arguments") or {}}})
                out.append({"role": "model", "parts": parts})
            elif role == "tool":
                name = m.get("name") or names.get(m.get("tool_call_id") or "", "")
                if not name:
                    raise BadRequest("Gemini: a tool result must name its function")
                out.append(
                    {
                        "role": "user",
                        "parts": [{"functionResponse": {"name": name, "response": {"result": str(m.get("content") or "")}}}],
                    }
                )
            elif role in ("user", "assistant"):
                out.append(
                    {"role": "model" if role == "assistant" else "user", "parts": [{"text": str(m.get("content") or "")}]}
                )
        return out

    def _body(self, request: Request) -> dict[str, Any]:
        system, rest = split_system(request.messages)
        body: dict[str, Any] = {
            "contents": self._contents(rest),
            "generationConfig": {"maxOutputTokens": request.max_output_tokens},
        }
        if request.temperature is not None:
            body["generationConfig"]["temperature"] = request.temperature
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        if request.tools:
            body["tools"] = [
                {
                    "functionDeclarations": [
                        {
                            "name": t["function"]["name"],
                            "description": t["function"].get("description", ""),
                            "parameters": t["function"].get("parameters") or {"type": "object"},
                        }
                        for t in request.tools
                    ]
                }
            ]
        return body

    @staticmethod
    def _path(model: str, verb: str) -> str:
        return f"/models/{urllib.parse.quote(model, safe='-._')}:{verb}"

    @staticmethod
    def _candidate(data: dict[str, Any]) -> dict[str, Any]:
        cands = data.get("candidates") or []
        if not cands:
            block = (data.get("promptFeedback") or {}).get("blockReason")
            if block:
                return {"finishReason": "SAFETY", "content": {"parts": []}}
            return {}
        return cands[0]

    @staticmethod
    def _finish(reason: str | None, calls: list[ToolCall]) -> str:
        if reason not in _FINISH:
            raise boundary.ProviderUnavailable(f"Gemini: response ended without a known finish reason ({reason!r})")
        finish = _FINISH[reason]
        return "tool_calls" if calls and finish == "stop" else finish

    @staticmethod
    def _parts(cand: dict[str, Any]) -> tuple[str, list[ToolCall]]:
        texts, calls = [], []
        for i, part in enumerate((cand.get("content") or {}).get("parts") or []):
            if "text" in part and not part.get("thought"):
                texts.append(part.get("text") or "")
            elif "functionCall" in part:
                fc = part["functionCall"] or {}
                calls.append(ToolCall(fc.get("id") or f"call_{i}", fc.get("name") or "", tool_args(fc.get("args"))))
        return "".join(texts), calls

    def chat(self, request: Request) -> Result:
        def call():
            resp = self._send(
                "POST", self._path(request.model, "generateContent"), body=self._body(request),
                timeout=request.timeout, model=request.model,
            )
            return json.loads(resp.read().decode("utf-8"))

        data = self._with_retries(call, cancel_check=request.cancel_check)
        cand = self._candidate(data)
        text, calls = self._parts(cand)
        usage = data.get("usageMetadata") or {}
        return Result(
            text=text,
            tool_calls=calls,
            usage=Usage(usage.get("promptTokenCount"), usage.get("candidatesTokenCount")),
            finish=self._finish(cand.get("finishReason"), calls),
            model=data.get("modelVersion") or request.model,
            provider_request_id=str(data.get("responseId") or ""),
        )

    def stream(self, request: Request) -> Iterator[Event]:
        resp = self._with_retries(
            lambda: self._send(
                "POST", self._path(request.model, "streamGenerateContent") + "?alt=sse",
                body=self._body(request), timeout=request.timeout, model=request.model,
            ),
            cancel_check=request.cancel_check,
        )
        calls: list[ToolCall] = []
        usage: dict[str, Any] = {}
        model = request.model
        for _name, data in sse_events(resp):
            if request.cancel_check is not None and request.cancel_check():
                _close(resp)
                raise boundary.InferenceCancelled("Gemini: cancelled")
            if data.get("error"):
                raise BadRequest(f"Gemini stream error: {(data['error'].get('message') or '')[:200]}")
            usage = data.get("usageMetadata") or usage
            model = data.get("modelVersion") or model
            cand = self._candidate(data)
            text, new_calls = self._parts(cand)
            if text:
                yield Event("text", text=text)
            for call in new_calls:
                calls.append(call)
                yield Event("tool_call", tool_call=call)
            if cand.get("finishReason"):
                yield Event(
                    "usage",
                    usage=Usage(usage.get("promptTokenCount"), usage.get("candidatesTokenCount")),
                )
                yield Event("done", finish=self._finish(cand.get("finishReason"), calls), model=model)
                return
        raise boundary.ProviderUnavailable("Gemini: stream ended without a finish reason")

    def discover(self) -> list[ModelInfo]:
        found: list[ModelInfo] = []
        token = ""
        for _page in range(10):
            path = "/models?pageSize=100" + (f"&pageToken={urllib.parse.quote(token)}" if token else "")
            resp = self._with_retries(lambda p=path: self._send("GET", p, timeout=20, purpose="discovery"))
            data = json.loads(resp.read().decode("utf-8"))
            for m in data.get("models") or []:
                methods = set(m.get("supportedGenerationMethods") or [])
                if "generateContent" not in methods:
                    continue  # embedding-only and other non-chat models
                caps = {"completion"}
                if m.get("thinking"):
                    caps.add("thinking")
                found.append(
                    ModelInfo(
                        id=str(m.get("name") or "").removeprefix("models/"),
                        provider=self.provider,
                        capabilities=frozenset(caps),
                        context_window=m.get("inputTokenLimit"),
                        max_output_tokens=m.get("outputTokenLimit"),
                        display_name=m.get("displayName") or "",
                    )
                )
            token = data.get("nextPageToken") or ""
            if not token:
                break
        return found
