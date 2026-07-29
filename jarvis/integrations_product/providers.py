"""Provider matrix, unlocks, and connection tests."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

from jarvis.integrations_product.secrets_bus import (
    get_secret,
    is_provider_enabled,
    is_set,
    secrets_status,
)
from jarvis.integrations_product.usage import record_usage


def _provider(
    *,
    id: str,
    name: str,
    category: str,
    purpose: str,
    owner_product: str,
    secret_field: str = "",
    managed_elsewhere: bool = False,
    managed_path: str = "",
    unlocks: list[str] | None = None,
    docs: str = "",
    kind: str = "cloud",
    experimental: bool = False,
) -> dict[str, Any]:
    return {
        "id": id,
        "name": name,
        "category": category,
        "purpose": purpose,
        "owner_product": owner_product,
        "secret_field": secret_field,
        "managed_elsewhere": managed_elsewhere,
        "managed_path": managed_path,
        "unlocks": unlocks or [],
        "docs": docs,
        "kind": kind,
        "experimental": experimental,
    }


PROVIDERS: list[dict[str, Any]] = [
    _provider(
        id="gemini",
        name="Google Gemini",
        category="Cloud AI",
        purpose="Cloud Live voice and optional Gemini models",
        owner_product="Voice",
        secret_field="gemini_api_key",
        unlocks=["Cloud Live (Gemini)", "Models wizard (Gemini key presence)"],
        docs="docs/VOICE_IMPLEMENTATION.md",
    ),
    _provider(
        id="openai",
        name="OpenAI",
        category="Cloud AI",
        purpose="Optional OpenAI key for future Realtime / LiteLLM routes",
        owner_product="Voice",
        secret_field="openai_api_key",
        unlocks=["Cloud Live (OpenAI Realtime — client gated)", "Models via LiteLLM if configured"],
        docs="docs/VOICE_IMPLEMENTATION.md",
    ),
    _provider(
        id="anthropic",
        name="Anthropic",
        category="Cloud AI",
        purpose="Optional Anthropic key for LiteLLM / cloud chat prefixes",
        owner_product="Models",
        secret_field="anthropic_api_key",
        unlocks=["Models via LiteLLM when JARVIS_CLOUD_INFERENCE enabled"],
        docs="docs/MODELS_IMPLEMENTATION.md",
    ),
    _provider(
        id="openrouter",
        name="OpenRouter",
        category="Cloud AI",
        purpose="Route multi-model cloud chat via OpenRouter / LiteLLM",
        owner_product="Models",
        secret_field="openrouter_api_key",
        unlocks=["Models wizard", "LiteLLM OpenRouter routes"],
        docs="docs/MODELS_IMPLEMENTATION.md",
    ),
    _provider(
        id="huggingface",
        name="Hugging Face",
        category="Cloud AI",
        purpose="Optional HF token for diarization / hub downloads",
        owner_product="Voice",
        secret_field="hf_token",
        unlocks=["Optional voice/ML hub features"],
        docs="docs/CONFIG.md",
    ),
    _provider(
        id="meshy",
        name="Meshy",
        category="Engineering",
        purpose="Text-to-3D for Engineering lab",
        owner_product="Engineering",
        secret_field="meshy_api_key",
        unlocks=["Engineering Meshy text-to-3D"],
        docs="docs/INTEGRATIONS_IMPLEMENTATION.md",
    ),
    _provider(
        id="ollama",
        name="Ollama",
        category="Local AI",
        purpose="Local model runtime (no cloud key)",
        owner_product="Models",
        secret_field="",
        unlocks=["Chat", "Embeddings", "Local vision models"],
        docs="docs/MODELS_IMPLEMENTATION.md",
        kind="local",
    ),
    _provider(
        id="litellm",
        name="LiteLLM Gateway",
        category="Gateway",
        purpose="Local gateway that may proxy cloud providers",
        owner_product="Models",
        secret_field="",
        unlocks=["Unified model gateway"],
        docs="docs/MODELS_IMPLEMENTATION.md",
        kind="gateway",
    ),
    _provider(
        id="home_assistant",
        name="Home Assistant",
        category="Smart Home",
        purpose="HA URL + token — managed in Smart Home",
        owner_product="Smart Home",
        secret_field="",
        managed_elsewhere=True,
        managed_path="#smarthome / Smart Home Home",
        unlocks=["Device control", "Scenes", "Home status"],
        docs="docs/HOME_ASSISTANT_IMPLEMENTATION.md",
        kind="product",
    ),
    _provider(
        id="automation_webhook",
        name="Inbound Automation Webhook",
        category="Automation",
        purpose="External systems call Aria — owned by Automation",
        owner_product="Automation",
        secret_field="",
        managed_elsewhere=True,
        managed_path="Automation Home · webhook",
        unlocks=["Inbound chat/briefing/HA scene triggers"],
        docs="docs/automation-webhook.md",
        kind="inbound",
    ),
    _provider(
        id="searxng",
        name="SearXNG",
        category="Search",
        purpose="Local web search (optional URL)",
        owner_product="Browser",
        secret_field="",
        unlocks=["Web search without paid API"],
        docs="docs/CONFIG.md",
        kind="local",
    ),
    _provider(
        id="aria_host",
        name="Aria Host API Key",
        category="Host",
        purpose="Protect Aria /api on LAN — not an outbound provider key",
        owner_product="Security",
        secret_field="",
        managed_elsewhere=True,
        managed_path="LAN / Security settings",
        unlocks=["LAN API authentication"],
        docs="docs/CONFIG.md",
        kind="host",
    ),
]


def list_provider_defs() -> list[dict[str, Any]]:
    return [dict(p) for p in PROVIDERS]


def get_provider_def(provider_id: str) -> dict[str, Any] | None:
    for p in PROVIDERS:
        if p["id"] == provider_id:
            return dict(p)
    return None


def enrich_provider(defn: dict[str, Any]) -> dict[str, Any]:
    pid = defn["id"]
    enabled = is_provider_enabled(pid, default=True)
    configured = False
    preview = ""
    field = defn.get("secret_field") or ""
    if field:
        configured = is_set(field)
        st = secrets_status()
        preview = st.get(f"{field}_preview") or ""
    elif pid == "ollama":
        configured = True  # local expected
    elif pid == "litellm":
        configured = bool(os.getenv("JARVIS_LITELLM_URL"))
    elif pid == "home_assistant":
        try:
            from jarvis.home_assistant import ha_enabled, ha_token

            configured = bool(ha_enabled() and ha_token())
        except Exception:
            configured = bool(os.getenv("JARVIS_HA_TOKEN"))
    elif pid == "automation_webhook":
        configured = bool(os.getenv("JARVIS_AUTOMATION_SECRET"))
    elif pid == "searxng":
        configured = bool(os.getenv("JARVIS_SEARXNG_URL"))
    elif pid == "aria_host":
        configured = bool(os.getenv("JARVIS_API_KEY"))

    status = "disabled" if not enabled else ("configured" if configured else "available")
    if defn.get("managed_elsewhere") and configured:
        status = "managed_elsewhere"

    return {
        **defn,
        "enabled": enabled,
        "configured": configured,
        "status": status,
        "secret_preview": preview,
        "health": "unknown",
        "last_test": None,
    }


def provider_matrix(*, q: str = "", category: str = "", configured_only: bool = False) -> list[dict[str, Any]]:
    items = [enrich_provider(p) for p in PROVIDERS]
    ql = (q or "").strip().lower()
    out = []
    for item in items:
        if category and item.get("category", "").lower() != category.lower():
            continue
        if configured_only and not item.get("configured"):
            continue
        if ql:
            blob = " ".join(
                [
                    item.get("id", ""),
                    item.get("name", ""),
                    item.get("purpose", ""),
                    item.get("owner_product", ""),
                    " ".join(item.get("unlocks") or []),
                ]
            ).lower()
            if ql not in blob:
                continue
        out.append(item)
    return out


def test_connection(provider_id: str) -> dict[str, Any]:
    """Run a live or presence connection test for a provider."""
    defn = get_provider_def(provider_id)
    if not defn:
        return {"ok": False, "provider_id": provider_id, "error": "unknown_provider"}
    if not is_provider_enabled(provider_id, default=True):
        return {
            "ok": False,
            "provider_id": provider_id,
            "error": "provider_disabled",
            "recovery": "Enable the provider in Integrations Home.",
        }

    started = time.perf_counter()
    result: dict[str, Any]
    try:
        if provider_id == "gemini":
            result = _test_gemini()
        elif provider_id == "openai":
            result = _test_openai()
        elif provider_id == "anthropic":
            result = _test_key_presence("anthropic", "anthropic_api_key")
        elif provider_id == "openrouter":
            result = _test_openrouter()
        elif provider_id == "huggingface":
            result = _test_key_presence("huggingface", "hf_token")
        elif provider_id == "meshy":
            result = _test_meshy()
        elif provider_id == "ollama":
            from jarvis.models_product.providers import validate_provider

            result = validate_provider("ollama")
        elif provider_id == "litellm":
            from jarvis.models_product.providers import validate_provider

            result = validate_provider("litellm")
        elif provider_id == "home_assistant":
            result = _test_home_assistant()
        elif provider_id == "automation_webhook":
            result = _test_webhook_config()
        elif provider_id == "searxng":
            result = _test_searxng()
        elif provider_id == "aria_host":
            result = {
                "ok": bool(os.getenv("JARVIS_API_KEY")),
                "provider": "aria_host",
                "message": "Host API key set" if os.getenv("JARVIS_API_KEY") else "Host API key not set",
                "managed_elsewhere": True,
                "recovery": "Set JARVIS_API_KEY in Security / LAN settings if exposing Aria on LAN.",
            }
        else:
            result = {"ok": False, "error": "no_test_implemented"}
    except Exception as exc:
        result = {"ok": False, "error": str(exc), "recovery": "Check credentials and network."}

    latency = int((time.perf_counter() - started) * 1000)
    result.setdefault("provider_id", provider_id)
    result.setdefault("latency_ms", latency)
    result.setdefault("owner_product", defn.get("owner_product"))
    result.setdefault("unlocks", defn.get("unlocks") or [])
    if "message" not in result and result.get("ok"):
        result["message"] = "Connection OK"
    if not result.get("ok") and "recovery" not in result:
        result["recovery"] = "Open Integrations Home, re-save the key, then Test Connection again."

    record_usage(
        provider_id,
        action="test_connection",
        ok=bool(result.get("ok")),
        latency_ms=latency,
        status=str(result.get("status") or ("ok" if result.get("ok") else "fail")),
        message=str(result.get("message") or result.get("error") or ""),
    )
    return result


def _test_key_presence(provider: str, field: str) -> dict[str, Any]:
    key = get_secret(field)
    if not key:
        return {
            "ok": False,
            "provider": provider,
            "error": "key_missing",
            "message": f"{provider} key not set",
            "recovery": f"Paste the key in Integrations Home ({field}).",
        }
    return {
        "ok": True,
        "provider": provider,
        "auth": "key_present",
        "message": f"{provider} key present (presence check only — no remote call).",
        "note": "Live API validation may be limited for this provider.",
    }


def _test_gemini() -> dict[str, Any]:
    key = get_secret("gemini_api_key")
    if not key:
        return {
            "ok": False,
            "provider": "gemini",
            "error": "key_missing",
            "message": "Gemini API key not set",
            "recovery": "Add Gemini API key in Integrations Home to unlock Cloud Live.",
        }
    # Lightweight models list probe
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}&pageSize=1"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            data = json.loads(raw) if raw else {}
            status = getattr(resp, "status", 200)
        return {
            "ok": True,
            "provider": "gemini",
            "status": status,
            "auth": "ok",
            "message": "Gemini API authenticated",
            "version": "v1beta",
            "sample": list((data.get("models") or [])[:1]),
        }
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "provider": "gemini",
            "status": exc.code,
            "error": f"HTTP {exc.code}",
            "message": "Gemini authentication failed",
            "recovery": "Verify the key in Google AI Studio and re-save.",
        }
    except Exception as exc:
        return {"ok": False, "provider": "gemini", "error": str(exc), "message": "Gemini unreachable"}


def _test_openai() -> dict[str, Any]:
    key = get_secret("openai_api_key")
    if not key:
        return {
            "ok": False,
            "provider": "openai",
            "error": "key_missing",
            "recovery": "Add OpenAI API key in Integrations Home.",
        }
    try:
        req = urllib.request.Request(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {key}"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            status = getattr(resp, "status", 200)
            _ = resp.read(2000)
        from jarvis.cloud_live_voice import OPENAI_WEBRTC_CLIENT_READY

        return {
            "ok": True,
            "provider": "openai",
            "status": status,
            "auth": "ok",
            "message": "OpenAI API authenticated",
            "note": (
                "OpenAI Realtime Cloud Live client is not ready yet."
                if not OPENAI_WEBRTC_CLIENT_READY
                else "Realtime client ready"
            ),
        }
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "provider": "openai",
            "status": exc.code,
            "error": f"HTTP {exc.code}",
            "recovery": "Check the key at platform.openai.com and re-save.",
        }
    except Exception as exc:
        return {"ok": False, "provider": "openai", "error": str(exc)}


def _test_openrouter() -> dict[str, Any]:
    key = get_secret("openrouter_api_key")
    if not key:
        return {"ok": False, "provider": "openrouter", "error": "key_missing", "recovery": "Set OpenRouter key in Integrations."}
    try:
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {key}"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            status = getattr(resp, "status", 200)
            _ = resp.read(2000)
        return {"ok": True, "provider": "openrouter", "status": status, "auth": "ok", "message": "OpenRouter authenticated"}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "provider": "openrouter", "status": exc.code, "error": f"HTTP {exc.code}"}
    except Exception as exc:
        return {"ok": False, "provider": "openrouter", "error": str(exc)}


def _test_meshy() -> dict[str, Any]:
    key = get_secret("meshy_api_key")
    if not key:
        return {
            "ok": False,
            "provider": "meshy",
            "error": "key_missing",
            "recovery": "Add Meshy API key in Integrations Home (Engineering unlock).",
        }
    try:
        # Balance/status style endpoint — fall back to authenticated probe
        req = urllib.request.Request(
            "https://api.meshy.ai/openapi/v2/text-to-3d",
            headers={"Authorization": f"Bearer {key}"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                status = getattr(resp, "status", 200)
                _ = resp.read(500)
            return {"ok": True, "provider": "meshy", "status": status, "auth": "ok", "message": "Meshy API reachable"}
        except urllib.error.HTTPError as exc:
            # 405/404 with auth still proves key accepted vs 401
            if exc.code in (401, 403):
                return {
                    "ok": False,
                    "provider": "meshy",
                    "status": exc.code,
                    "error": f"HTTP {exc.code}",
                    "recovery": "Verify Meshy API key.",
                }
            return {
                "ok": True,
                "provider": "meshy",
                "status": exc.code,
                "auth": "accepted",
                "message": f"Meshy key accepted (HTTP {exc.code} on probe endpoint)",
            }
    except Exception as exc:
        return {"ok": False, "provider": "meshy", "error": str(exc)}


def _test_home_assistant() -> dict[str, Any]:
    try:
        from jarvis.home_assistant import check_connection, ha_enabled

        if not ha_enabled():
            return {
                "ok": False,
                "provider": "home_assistant",
                "managed_elsewhere": True,
                "message": "Home Assistant not enabled",
                "recovery": "Configure in Smart Home Home.",
            }
        st = check_connection()
        ok = bool((st or {}).get("ok") or (st or {}).get("connected"))
        return {
            "ok": ok,
            "provider": "home_assistant",
            "managed_elsewhere": True,
            "message": "HA connected" if ok else str((st or {}).get("error") or "HA not connected"),
            "detail": {k: v for k, v in (st or {}).items() if k != "token"},
            "recovery": None if ok else "Open Smart Home → Connect.",
        }
    except Exception as exc:
        return {
            "ok": False,
            "provider": "home_assistant",
            "managed_elsewhere": True,
            "error": str(exc),
            "recovery": "Open Smart Home Home.",
        }


def _test_webhook_config() -> dict[str, Any]:
    secret_set = bool(os.getenv("JARVIS_AUTOMATION_SECRET"))
    return {
        "ok": secret_set,
        "provider": "automation_webhook",
        "managed_elsewhere": True,
        "auth": "secret_set" if secret_set else "unset",
        "message": "Inbound webhook secret set" if secret_set else "Automation secret not set",
        "docs": "docs/automation-webhook.md",
        "recovery": None if secret_set else "Set JARVIS_AUTOMATION_SECRET; manage webhook in Automation Home.",
        "note": "Integrations shows visibility only — Automation owns execution.",
    }


def _test_searxng() -> dict[str, Any]:
    url = (os.getenv("JARVIS_SEARXNG_URL") or "").rstrip("/")
    if not url:
        return {
            "ok": True,
            "provider": "searxng",
            "message": "SearXNG URL not set — DuckDuckGo fallback may be used",
            "note": "Optional local search.",
        }
    try:
        with urllib.request.urlopen(f"{url}/", timeout=3) as resp:
            status = getattr(resp, "status", 200)
        return {"ok": True, "provider": "searxng", "status": status, "url": url, "message": "SearXNG reachable"}
    except Exception as exc:
        return {"ok": False, "provider": "searxng", "url": url, "error": str(exc)}
