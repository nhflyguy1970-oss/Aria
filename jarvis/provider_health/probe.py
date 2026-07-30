"""Provider probes & capability discovery — wraps existing ollama_health / services."""

from __future__ import annotations

import time
from typing import Any


def list_providers() -> list[dict[str, Any]]:
    """Discovered providers and capabilities (local + optional cloud)."""
    providers: list[dict[str, Any]] = []

    ollama = _ollama_snapshot()
    providers.append(
        {
            "id": "ollama",
            "name": "Ollama",
            "kind": "local",
            "endpoint": ollama.get("host"),
            "alive": bool(ollama.get("running")),
            "health_state": ollama.get("health_state") or "unknown",
            "models": ollama.get("models") or [],
            "capabilities": ["chat", "stream", "embeddings", "vision"],
            "version": ollama.get("version"),
        }
    )

    try:
        from jarvis.inference.gateway import litellm_available, litellm_url

        litellm_ok = litellm_available()
        providers.append(
            {
                "id": "litellm",
                "name": "LiteLLM / OpenRouter gateway",
                "kind": "router",
                "endpoint": litellm_url(),
                "alive": litellm_ok,
                "health_state": "healthy" if litellm_ok else "disconnected",
                "models": [],
                "capabilities": ["chat", "cloud_route"],
            }
        )
    except Exception:
        pass

    # Capability stubs — credentials owned by Integrations / Models
    for pid, name, caps in (
        ("openai", "OpenAI", ["chat", "cloud"]),
        ("anthropic", "Anthropic", ["chat", "cloud"]),
        ("openrouter", "OpenRouter", ["chat", "cloud"]),
        ("lmstudio", "LM Studio", ["chat", "stream", "local"]),
        ("opencode", "OpenCode", ["chat", "tools"]),
    ):
        providers.append(
            {
                "id": pid,
                "name": name,
                "kind": "external",
                "alive": None,
                "health_state": "unknown",
                "models": [],
                "capabilities": caps,
                "note": "Configured via Integrations / Models when enabled",
            }
        )
    return providers


def _ollama_snapshot() -> dict[str, Any]:
    try:
        from jarvis.ollama_health import check_ollama, ollama_host, ollama_version

        health = check_ollama() or {}
        ver = ""
        try:
            ver = ollama_version() or ""
        except Exception:
            ver = ""
        return {
            "host": ollama_host(),
            "running": bool(health.get("running") or health.get("ok")),
            "health_state": health.get("health_state") or ("healthy" if health.get("running") else "disconnected"),
            "models": health.get("models") or health.get("installed") or [],
            "detail": health.get("detail") or health.get("error") or "",
            "version": ver,
            "probe": health.get("inference_probe") or health.get("probe"),
        }
    except Exception as exc:
        return {"host": "", "running": False, "health_state": "unknown", "models": [], "detail": str(exc)}


def ping_provider(provider: str = "ollama", *, force_probe: bool = True) -> dict[str, Any]:
    """Lightweight liveness + optional generate probe."""
    started = time.perf_counter()
    provider = (provider or "ollama").lower().strip()
    if provider in ("", "ollama", "local"):
        snap = _ollama_snapshot()
        probe = None
        if force_probe and snap.get("running"):
            try:
                from jarvis.ollama_health import refresh_inference_probe

                probe = refresh_inference_probe(force=True)
            except Exception as exc:
                probe = {"ok": False, "detail": str(exc)}
        alive = bool(snap.get("running"))
        if probe is not None and probe.get("ok") is False and "timeout" in str(probe.get("detail") or "").lower():
            state = "degraded"
        elif alive:
            state = snap.get("health_state") or "healthy"
        else:
            state = "disconnected"
        return {
            "ok": alive,
            "alive": alive,
            "provider": "ollama",
            "state": state,
            "host": snap.get("host"),
            "models": snap.get("models") or [],
            "probe": probe,
            "detail": snap.get("detail") or (probe or {}).get("detail") or "",
            "elapsed_ms": int((time.perf_counter() - started) * 1000),
        }

    if provider == "litellm":
        try:
            from jarvis.inference.gateway import litellm_available, litellm_url

            ok = litellm_available()
            return {
                "ok": ok,
                "alive": ok,
                "provider": "litellm",
                "state": "healthy" if ok else "disconnected",
                "host": litellm_url(),
                "elapsed_ms": int((time.perf_counter() - started) * 1000),
            }
        except Exception as exc:
            return {"ok": False, "alive": False, "provider": "litellm", "state": "unknown", "detail": str(exc)}

    return {
        "ok": False,
        "alive": None,
        "provider": provider,
        "state": "unknown",
        "detail": "No active probe adapter for this provider yet",
        "elapsed_ms": int((time.perf_counter() - started) * 1000),
    }


def list_models(provider: str = "ollama") -> dict[str, Any]:
    snap = ping_provider(provider, force_probe=False)
    models = snap.get("models") or []
    current = ""
    try:
        from jarvis.llm import general_model

        current = general_model() or ""
    except Exception:
        pass
    return {
        "ok": True,
        "provider": snap.get("provider") or provider,
        "models": models,
        "current": current,
        "alive": snap.get("alive"),
    }


def resource_snapshot() -> dict[str, Any]:
    out: dict[str, Any] = {}
    try:
        from jarvis.system_monitor import collect_stats

        stats = collect_stats() or {}
        out["cpu_percent"] = stats.get("cpu_percent")
        out["ram"] = stats.get("ram")
        out["gpu"] = stats.get("gpu") or stats.get("gpus")
        out["ollama_using_gpu"] = (stats.get("gpu") or {}).get("ollama_using_gpu") if isinstance(stats.get("gpu"), dict) else None
    except Exception as exc:
        out["error"] = str(exc)
    return out
