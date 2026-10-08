"""The inference execution boundary — what may run where, and what really ran.

Every model call goes through jarvis.inference.gateway, and the gateway asks
this module four questions at the moment of execution, not at planning time:

1. May this target run? A cloud target needs cloud inference enabled, ARIA
   not in offline mode, a request that is not local-only (private health
   context is always local-only), and — when an allowlist is configured — a
   permitted provider. An explicit model choice cannot override any of these.
2. If it may not, or its provider fails before producing output, what runs
   instead? Only an *installed local* model configured for the role. A cloud
   model id is never handed to Ollama.
3. Can the target do what is asked? Tool calls, JSON output and images are
   checked against capabilities the provider itself reports.
4. What actually happened? Every call produces a receipt: each attempt's
   provider, model, locality, outcome, latency and usage, plus the policy
   decisions that shaped it.

Streaming has one extra rule: once an attempt has produced output, its
failure is final. A replacement attempt would silently splice two different
answers together, so the interruption is raised instead.
"""

from __future__ import annotations

import json
import os
import threading
import time
import urllib.request
import uuid
from collections import deque
from dataclasses import asdict, dataclass, field
from typing import Any

LOCAL = "local"
CLOUD = "cloud"
STANDARD = "standard"
LOCAL_ONLY = "local_only"

# Model-id prefixes → provider. Recognising a provider is not permission to use it.
_PROVIDER_PREFIXES = (
    ("openai/", "openai"),
    ("gpt-", "openai"),
    ("anthropic/", "anthropic"),
    ("claude-", "anthropic"),
    ("gemini/", "google"),
    ("google/", "google"),
    ("gemini-", "google"),
)

# Context that must never leave the machine, recognised by the markers the
# subsystems that produce it already write.
_LOCAL_ONLY_MARKERS = ("Health record context (authoritative local PHR",)


# ------------------------------------------------------------------ errors


class InferenceError(RuntimeError):
    """A model call did not produce a usable answer. Message is user-safe."""

    fallback_eligible = False


class ProviderUnavailable(InferenceError):
    """The provider failed before producing any output; a fallback may run."""

    fallback_eligible = True


class CloudNotPermitted(InferenceError):
    """Policy refused a cloud target. A decision, never a fault to retry."""


class CapabilityMismatch(InferenceError):
    """The model cannot do what the request needs (tools, JSON, images)."""


class StreamInterrupted(InferenceError):
    """A stream failed after producing output. Never continued elsewhere."""

    def __init__(self, message: str, *, provider: str, model: str, partial_chars: int):
        super().__init__(message)
        self.provider = provider
        self.model = model
        self.partial_chars = partial_chars


class InferenceCancelled(InferenceError):
    """The caller cancelled. Never a reason to try another model."""


# ------------------------------------------------------------------ targets


# Local model families whose names collide with a cloud prefix.
_LOCAL_EXCEPTIONS = ("gpt-oss",)


def provider_of(model: str) -> str:
    lower = (model or "").strip().lower()
    if lower.startswith("ollama/") or lower.startswith(_LOCAL_EXCEPTIONS):
        return "ollama"
    for prefix, provider in _PROVIDER_PREFIXES:
        if lower.startswith(prefix):
            return provider
    return "ollama"


def is_cloud_model(model: str) -> bool:
    return provider_of(model) != "ollama"


def offline() -> bool:
    return os.getenv("JARVIS_OFFLINE", "0").strip().lower() in ("1", "true", "yes", "on")


def cloud_enabled() -> bool:
    return os.getenv("JARVIS_CLOUD_INFERENCE", "0").strip().lower() in ("1", "true", "yes", "on")


def permitted_providers() -> set[str] | None:
    """Configured cloud provider allowlist; None means "any, once cloud is enabled"."""
    raw = os.getenv("JARVIS_CLOUD_PROVIDERS", "").strip()
    if not raw:
        return None
    return {p.strip().lower() for p in raw.split(",") if p.strip()}


def privacy_class(messages: list[dict] | None, requested: str = "") -> str:
    if (requested or "").strip().lower() == LOCAL_ONLY:
        return LOCAL_ONLY
    for message in messages or []:
        content = message.get("content")
        text = content if isinstance(content, str) else json.dumps(content or "")
        if any(marker in text for marker in _LOCAL_ONLY_MARKERS):
            return LOCAL_ONLY
    return STANDARD


def cloud_refusal(model: str, *, privacy: str = STANDARD) -> str:
    """Why this cloud target may not run now, or "" if it may."""
    if not is_cloud_model(model):
        return ""
    if offline():
        return "ARIA is in offline mode (JARVIS_OFFLINE=1)"
    if not cloud_enabled():
        return "cloud inference is disabled (JARVIS_CLOUD_INFERENCE=0)"
    if privacy == LOCAL_ONLY:
        return "the request carries local-only (private) context"
    allowed = permitted_providers()
    provider = provider_of(model)
    if allowed is not None and provider not in allowed:
        return f"provider {provider!r} is not in JARVIS_CLOUD_PROVIDERS"
    return ""


def needs_local_runtime(model: str, *, privacy: str = STANDARD) -> bool:
    """Will this request run on local Ollama? A permitted cloud target will not;
    a refused one is answered locally, so it does."""
    return not (is_cloud_model(model) and not cloud_refusal(model, privacy=privacy))


def require_local_model_name(model: str) -> None:
    """Hard stop: a cloud model id must never be sent to local Ollama."""
    if is_cloud_model(model):
        raise InferenceError(
            f"refusing to send cloud model id {model!r} to local Ollama; "
            "a local fallback must name an installed local model"
        )


# ------------------------------------------------------------------ local models

_INSTALLED: dict[str, Any] = {"at": 0.0, "models": None}
_INSTALLED_TTL_S = 30.0


def installed_local_models(*, refresh: bool = False) -> set[str] | None:
    """Installed Ollama model tags, or None if Ollama could not be asked."""
    now = time.monotonic()
    if not refresh and _INSTALLED["models"] is not None and now - _INSTALLED["at"] < _INSTALLED_TTL_S:
        return set(_INSTALLED["models"])
    try:
        from jarvis.ollama_health import check_ollama

        status = check_ollama(soft_probe=False)
        if not status.get("running"):
            return None
        models = {str(m) for m in (status.get("models") or [])}
    except Exception:  # noqa: BLE001 - "unknown" is an answer
        return None
    _INSTALLED.update(at=now, models=models)
    return set(models)


def _installed(model: str, installed: set[str] | None) -> bool:
    if installed is None:
        return True  # cannot tell; let the call fail honestly if it is missing
    name = (model or "").strip()
    return name in installed or f"{name}:latest" in installed or (
        ":" not in name and any(m.split(":")[0] == name for m in installed)
    )


def local_fallback(role: str, *, exclude: str = "") -> str:
    """The installed local model configured for this role (never a cloud id)."""
    from jarvis.model_store import model_for

    installed = installed_local_models()
    seen: list[str] = []
    for candidate_role in (role, "conversation", "general"):
        try:
            candidate = (model_for(candidate_role) or "").strip()
        except Exception:  # noqa: BLE001
            candidate = ""
        if not candidate or candidate in seen or is_cloud_model(candidate):
            continue
        seen.append(candidate)
        if candidate != exclude and _installed(candidate, installed):
            return candidate
    raise ProviderUnavailable(
        f"no installed local model is configured for role {role!r}; "
        "cannot fall back without one"
    )


# ------------------------------------------------------------------ capabilities

_CAPS: dict[str, tuple[float, frozenset[str] | None]] = {}
_CAPS_TTL_S = 300.0


def model_capabilities(model: str) -> frozenset[str] | None:
    """Capabilities the provider reports for a model, or None if unknown.

    Ollama reports them per model (``/api/show``: completion, tools, vision,
    insert, embedding, thinking). For cloud models served via LiteLLM the
    gateway's own model metadata is used when it publishes it. Nothing here
    runs inference.
    """
    now = time.monotonic()
    cached = _CAPS.get(model)
    if cached and now - cached[0] < _CAPS_TTL_S:
        return cached[1]
    caps: frozenset[str] | None = None
    try:
        if is_cloud_model(model):
            caps = _litellm_capabilities(model)
        else:
            from ollama import show

            info = show(model)
            raw = getattr(info, "capabilities", None)
            if raw is None and isinstance(info, dict):
                raw = info.get("capabilities")
            caps = frozenset(str(c) for c in raw) if raw else None
    except Exception:  # noqa: BLE001 - unknown, not "none"
        caps = None
    _CAPS[model] = (now, caps)
    return caps


def _litellm_capabilities(model: str) -> frozenset[str] | None:
    from jarvis.inference.gateway import litellm_url

    try:
        with urllib.request.urlopen(f"{litellm_url()}/model/info", timeout=3) as resp:
            data = json.loads(resp.read().decode())
    except Exception:  # noqa: BLE001
        return None
    name = model.split("/", 1)[-1]
    for item in data.get("data") or []:
        if item.get("model_name") not in (model, name):
            continue
        info = item.get("model_info") or {}
        caps = {"completion"}
        if info.get("supports_function_calling"):
            caps.add("tools")
        if info.get("supports_vision"):
            caps.add("vision")
        if info.get("supports_response_schema"):
            caps.add("json")
        return frozenset(caps)
    return None


def discover_cloud_models() -> list[dict[str, Any]]:
    """What the configured gateway says it can serve — no hardcoded model names."""
    from jarvis.inference.gateway import litellm_url

    try:
        with urllib.request.urlopen(f"{litellm_url()}/v1/models", timeout=3) as resp:
            data = json.loads(resp.read().decode())
    except Exception as exc:  # noqa: BLE001
        return [{"error": f"{type(exc).__name__}: {exc}"}]
    return [
        {"id": m.get("id"), "provider": provider_of(str(m.get("id") or ""))}
        for m in data.get("data") or []
    ]


def requirements_from_kwargs(kwargs: dict[str, Any], messages: list[dict]) -> set[str]:
    needs: set[str] = set()
    if kwargs.get("tools"):
        needs.add("tools")
    if any(m.get("images") for m in messages or []):
        needs.add("vision")
    return needs


def check_capabilities(model: str, needs: set[str]) -> None:
    if not needs:
        return
    caps = model_capabilities(model)
    if caps is None:
        return  # unknown: the provider's own error will be reported if unsupported
    missing = needs - set(caps)
    if missing:
        raise CapabilityMismatch(
            f"model {model!r} does not support {', '.join(sorted(missing))} "
            f"(reports: {', '.join(sorted(caps)) or 'nothing'})"
        )


# ------------------------------------------------------------------ receipts


@dataclass
class Attempt:
    provider: str
    model: str
    locality: str
    status: str = "started"  # started | completed | failed | interrupted | cancelled
    error: str = ""
    started_at: float = field(default_factory=time.time)
    first_token_ms: float | None = None
    duration_ms: float | None = None
    output_chars: int = 0
    prompt_tokens: int | None = None
    completion_tokens: int | None = None

    def finish(self, status: str, *, error: str = "") -> None:
        self.status = status
        self.error = error[:300]
        self.duration_ms = round((time.time() - self.started_at) * 1000, 1)


@dataclass
class Receipt:
    role: str
    requested_model: str
    privacy: str
    stream: bool
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    policy: list[str] = field(default_factory=list)
    attempts: list[Attempt] = field(default_factory=list)
    status: str = "started"

    def attempt(self, model: str) -> Attempt:
        att = Attempt(
            provider=provider_of(model) if is_cloud_model(model) else "ollama",
            model=model,
            locality=CLOUD if is_cloud_model(model) else LOCAL,
        )
        self.attempts.append(att)
        return att

    @property
    def final(self) -> Attempt | None:
        return self.attempts[-1] if self.attempts else None

    def close(self, status: str) -> None:
        self.status = status
        _remember(self)

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        final = self.final
        out["executed_provider"] = final.provider if final else ""
        out["executed_model"] = final.model if final else ""
        out["executed_locality"] = final.locality if final else ""
        out["fallback_used"] = len(self.attempts) > 1
        return out


_RECENT: deque[dict[str, Any]] = deque(maxlen=50)
_RECENT_LOCK = threading.Lock()


def _remember(receipt: Receipt) -> None:
    with _RECENT_LOCK:
        _RECENT.append(receipt.to_dict())


def recent_receipts(limit: int = 20) -> list[dict[str, Any]]:
    with _RECENT_LOCK:
        return list(_RECENT)[-limit:]
