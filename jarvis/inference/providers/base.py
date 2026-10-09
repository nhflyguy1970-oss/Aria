"""Shared machinery for native cloud provider adapters.

Every adapter speaks one internal contract so the gateway can treat providers
alike:

  ``chat(request) -> Result``           one completed response
  ``stream(request) -> Iterator[Event]``  text deltas, tool calls, usage, then
                                         exactly one terminal event
  ``discover() -> list[ModelInfo]``      what this account can use

and every byte that leaves the machine goes through ``ProviderAdapter._send``,
which re-checks the cloud policy (cloud enabled, not offline, provider
permitted, paid inference authorised) immediately before transmission. Nothing
else in an adapter opens a connection.

Retries happen only before any output exists, only for faults that can
succeed on a second try (rate limits, overload, transient network/5xx), and
honour the provider's Retry-After. A per-provider circuit breaker stops
hammering a provider that keeps failing. A stream that ends without the
provider's terminal event is reported as interrupted, never as complete.
"""

from __future__ import annotations

import json
import logging
import random
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any

from jarvis.inference import boundary

log = logging.getLogger("jarvis.inference.providers")

DEFAULT_TIMEOUT_S = 120.0
MAX_RETRIES = 2
MAX_RETRY_AFTER_S = 30.0
CIRCUIT_FAILURES = 3
CIRCUIT_COOLDOWN_S = 120.0


# ------------------------------------------------------------------ errors


class ProviderAuthError(boundary.ProviderUnavailable):
    """Credential missing, locked, rejected or without access to the model."""


class RateLimited(boundary.ProviderUnavailable):
    def __init__(self, message: str, *, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class ProviderOverloaded(boundary.ProviderUnavailable):
    pass


class BadRequest(boundary.InferenceError):
    """The provider rejected the request itself; another try would fail too."""


class ContextTooLong(boundary.CapabilityMismatch):
    pass


# ------------------------------------------------------------------ data


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class Usage:
    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass
class Result:
    text: str
    tool_calls: list[ToolCall]
    usage: Usage
    finish: str  # "stop" | "tool_calls" | "length" | "filtered"
    model: str  # what the provider says it ran
    provider_request_id: str = ""


@dataclass
class Event:
    type: str  # "text" | "tool_call" | "usage" | "done"
    text: str = ""
    tool_call: ToolCall | None = None
    usage: Usage | None = None
    finish: str = ""
    model: str = ""


@dataclass
class ModelInfo:
    id: str  # provider-native model id
    provider: str
    capabilities: frozenset[str] = frozenset()
    context_window: int | None = None
    max_output_tokens: int | None = None
    display_name: str = ""

    @property
    def aria_id(self) -> str:
        return f"{self.provider}/{self.id}"


@dataclass
class Request:
    model: str  # provider-native id (no "openai/" prefix)
    messages: list[dict[str, Any]]  # ARIA messages: role, content[, tool_calls][, tool_call_id]
    tools: list[dict[str, Any]] | None = None  # OpenAI-style function tool schemas
    max_output_tokens: int = 1024
    temperature: float | None = None
    timeout: float = DEFAULT_TIMEOUT_S
    cancel_check: Callable[[], bool] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


# ------------------------------------------------------------------ circuit breaker

_circuit_lock = threading.Lock()
_circuit: dict[str, dict[str, float]] = {}


def circuit_open(provider: str) -> bool:
    with _circuit_lock:
        state = _circuit.get(provider) or {}
        return state.get("open_until", 0.0) > time.time()


def _record_outcome(provider: str, ok: bool) -> None:
    with _circuit_lock:
        state = _circuit.setdefault(provider, {"failures": 0.0, "open_until": 0.0})
        if ok:
            state["failures"] = 0.0
            state["open_until"] = 0.0
            return
        state["failures"] += 1
        if state["failures"] >= CIRCUIT_FAILURES:
            state["open_until"] = time.time() + CIRCUIT_COOLDOWN_S
            log.warning("%s circuit opened after %d failures", provider, int(state["failures"]))


def circuit_status() -> dict[str, dict[str, float]]:
    with _circuit_lock:
        return {k: dict(v) for k, v in _circuit.items()}


def reset_circuits() -> None:
    with _circuit_lock:
        _circuit.clear()


# ------------------------------------------------------------------ transport

# Swappable for tests: (method, url, headers, body, timeout) -> response object
# with .status, .headers (mapping), .read(), and line iteration for streams.
Transport = Callable[[str, str, dict[str, str], bytes | None, float], Any]


def _urllib_transport(method: str, url: str, headers: dict[str, str], body: bytes | None, timeout: float):
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    return urllib.request.urlopen(req, timeout=timeout)  # noqa: S310 - https only, see _send


_transport: Transport = _urllib_transport


def set_transport(transport: Transport | None) -> None:
    """Tests install a simulated provider here; None restores the real one."""
    global _transport
    _transport = transport or _urllib_transport


def _retry_after(headers: Any) -> float | None:
    if not headers:
        return None
    raw = headers.get("retry-after") or headers.get("Retry-After")
    if raw is None:
        return None
    try:
        return min(MAX_RETRY_AFTER_S, max(0.0, float(raw)))
    except ValueError:
        return None


class ProviderAdapter:
    """Base adapter. Subclasses implement the provider's wire format."""

    provider = ""  # "openai" | "anthropic" | "google"
    label = ""
    credential_field = ""  # Owner Vault field
    billing = "api"  # these adapters always bill the API account, never a subscription
    base_url = ""

    # ---- credentials -------------------------------------------------

    def credential(self) -> str:
        from jarvis.security.owner.provider_credentials import resolve_provider_secret

        found = resolve_provider_secret(self.credential_field)
        if found is not None and found.source == "locked":
            raise ProviderAuthError(f"{self.label}: Owner Vault is locked")
        if found is None or found.source == "missing" or not found.value:
            raise ProviderAuthError(f"{self.label}: no API credential configured")
        return found.value

    def credential_status(self) -> dict[str, Any]:
        """Presence only — never the value, never a network call."""
        from jarvis.security.owner.provider_credentials import resolve_provider_secret

        try:
            found = resolve_provider_secret(self.credential_field)
        except Exception as exc:  # noqa: BLE001
            return {"state": "error", "detail": type(exc).__name__}
        if found is None or not found.value:
            state = "locked" if found is not None and found.source == "locked" else "unconfigured"
            return {"state": state, "source": getattr(found, "source", "missing")}
        return {"state": "credentials_present", "source": found.source}

    # ---- the only way out --------------------------------------------

    def headers(self, key: str) -> dict[str, str]:  # pragma: no cover - per provider
        raise NotImplementedError

    def _send(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        timeout: float = DEFAULT_TIMEOUT_S,
        model: str = "",
        purpose: str = "inference",
    ):
        """Policy re-check, then transmit. Raises before any byte leaves if not allowed."""
        aria_model = f"{self.provider}/{model or '*'}"
        refusal = boundary.cloud_refusal(aria_model)
        if refusal:
            raise boundary.CloudNotPermitted(f"{self.label}: {refusal}")
        if purpose == "inference":
            # Paid traffic leaves only under an owner-authorized, priced reservation.
            from jarvis.inference.cloud_policy import require_reservation

            require_reservation(self.provider)
        if circuit_open(self.provider):
            raise boundary.ProviderUnavailable(f"{self.label}: temporarily disabled after repeated failures")
        url = f"{self.base_url}{path}"
        if not url.startswith("https://"):
            raise boundary.CloudNotPermitted(f"{self.label}: refusing non-HTTPS endpoint")
        key = self.credential()
        headers = self.headers(key)
        payload = json.dumps(body).encode("utf-8") if body is not None else None
        try:
            return _transport(method, url, headers, payload, timeout)
        except urllib.error.HTTPError as exc:
            detail = _scrub(_read_error(exc), key)
            raise self._classify_http(exc.code, exc.headers, detail) from None
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            raise boundary.ProviderUnavailable(f"{self.label}: network error ({type(exc).__name__})") from None

    def _classify_http(self, status: int, headers: Any, detail: str) -> boundary.InferenceError:
        # Provider error bodies can echo the request; never the key (it is a
        # header), but keep the text short.
        detail = (detail or "")[:300]
        if status in (401, 403):
            return ProviderAuthError(f"{self.label}: authentication failed ({status})")
        if status == 404:
            return BadRequest(f"{self.label}: model or endpoint not available to this account ({status})")
        if status == 429:
            return RateLimited(f"{self.label}: rate limited or out of quota", retry_after=_retry_after(headers))
        if status in (500, 502, 503, 504, 529):
            return ProviderOverloaded(f"{self.label}: provider error {status}")
        if status == 413 or "context" in detail.lower() and "length" in detail.lower():
            return ContextTooLong(f"{self.label}: request exceeds the model's context window")
        return BadRequest(f"{self.label}: request rejected ({status}): {detail}")

    def _with_retries(self, fn: Callable[[], Any], *, cancel_check=None) -> Any:
        """Retry transient faults before output exists. Never after."""
        attempt = 0
        while True:
            if cancel_check is not None and cancel_check():
                raise boundary.InferenceCancelled(f"{self.label}: cancelled before sending")
            try:
                out = fn()
                _record_outcome(self.provider, True)
                return out
            except (RateLimited, ProviderOverloaded, boundary.ProviderUnavailable) as exc:
                if isinstance(exc, ProviderAuthError):
                    _record_outcome(self.provider, False)
                    raise
                _record_outcome(self.provider, False)
                if attempt >= MAX_RETRIES or circuit_open(self.provider):
                    raise
                wait = getattr(exc, "retry_after", None)
                if wait is None:
                    wait = min(MAX_RETRY_AFTER_S, (2**attempt) + random.uniform(0, 0.5))
                attempt += 1
                log.info("%s: %s; retry %d in %.1fs", self.label, exc, attempt, wait)
                _sleep(wait)

    # ---- contract ------------------------------------------------------

    def chat(self, request: Request) -> Result:  # pragma: no cover - per provider
        raise NotImplementedError

    def stream(self, request: Request) -> Iterator[Event]:  # pragma: no cover - per provider
        raise NotImplementedError

    def discover(self) -> list[ModelInfo]:  # pragma: no cover - per provider
        raise NotImplementedError


def _scrub(text: str, key: str) -> str:
    """Provider error bodies can echo the request; never let a credential through."""
    from jarvis.inference.cloud_policy import _SECRET_SHAPES

    if key:
        text = text.replace(key, "[redacted]")
    return _SECRET_SHAPES.sub("[redacted]", text)


def _sleep(seconds: float) -> None:
    time.sleep(seconds)


def _read_error(exc: urllib.error.HTTPError) -> str:
    try:
        return exc.read().decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return ""


def sse_events(resp) -> Iterator[tuple[str, dict[str, Any]]]:
    """Parse a server-sent-events body into (event name, JSON data) pairs."""
    event = ""
    data_lines: list[str] = []
    for raw in resp:
        line = raw.decode("utf-8", errors="replace").rstrip("\r\n") if isinstance(raw, bytes) else raw.rstrip("\r\n")
        if not line:
            if data_lines:
                blob = "\n".join(data_lines)
                data_lines = []
                if blob.strip() == "[DONE]":
                    yield event or "done", {}
                else:
                    try:
                        yield event, json.loads(blob)
                    except json.JSONDecodeError:
                        pass
            event = ""
            continue
        if line.startswith(":"):
            continue
        if line.startswith("event:"):
            event = line[6:].strip()
        elif line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
    if data_lines:
        blob = "\n".join(data_lines)
        try:
            yield event, json.loads(blob)
        except json.JSONDecodeError:
            pass


def split_system(messages: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    system = "\n\n".join(
        str(m.get("content") or "") for m in messages if m.get("role") == "system"
    )
    return system, [m for m in messages if m.get("role") != "system"]


def tool_args(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    try:
        value = json.loads(raw or "{}")
    except (TypeError, json.JSONDecodeError):
        return {"_unparsed": str(raw)}
    return value if isinstance(value, dict) else {"_value": value}
