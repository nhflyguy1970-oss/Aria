"""Capability health — internal readiness report per capability."""

from __future__ import annotations

from typing import Any

from jarvis.capability_routing import (
    CAPABILITY_TO_ROLE,
    NON_LLM_CAPABILITIES,
    role_for_capability,
)
from jarvis.model_policy import select_model_for_role


def _check_ollama() -> bool:
    try:
        from jarvis.ollama_health import check_ollama

        return bool(check_ollama().get("running"))
    except Exception:
        return False


def _check_acm() -> bool:
    try:
        from aria_core import acm_bridge

        return acm_bridge.acm_is_authoritative()
    except Exception:
        return False


def _check_runtime() -> bool:
    try:
        from jarvis.runtime_client import get_runtime_client

        client = get_runtime_client()
        return client is not None
    except Exception:
        return False


def _check_speech() -> bool:
    try:
        from jarvis.config import load_audio_settings

        cfg = load_audio_settings()
        return bool(cfg.get("stt_model") or cfg.get("tts_voice"))
    except Exception:
        return False


_HEALTH_CHECKS: dict[str, Any] = {
    "memory": _check_acm,
    "mission_control": _check_runtime,
    "runtime": _check_runtime,
    "speech": _check_speech,
    "stt": _check_speech,
    "tts": _check_speech,
}


def capability_health_report() -> list[dict[str, Any]]:
    """Report role, configured/selected model, provider, and health per capability."""
    ollama_up = _check_ollama()
    rows: list[dict[str, Any]] = []

    all_caps = sorted(set(CAPABILITY_TO_ROLE) | NON_LLM_CAPABILITIES)
    display_order = [
        "conversation",
        "reasoning",
        "planning",
        "coding",
        "debugging",
        "code_review",
        "memory",
        "episodic_recall",
        "episodic_teaching",
        "mission_control",
        "vision",
        "ocr",
        "speech",
        "routing",
        "intent_classification",
        "tool_calling",
        "reflection",
        "learning",
        "summarization",
        "document_analysis",
        "web_research",
        "workflow_orchestration",
        "agent_coordination",
    ]
    ordered = [c for c in display_order if c in all_caps] + [
        c for c in all_caps if c not in display_order
    ]

    for capability in ordered:
        role = role_for_capability(capability)
        if role is None:
            provider = "acm" if capability.startswith("episodic") or capability == "memory" else (
                "mission_control" if capability in ("mission_control", "runtime") else "local"
            )
            check = _HEALTH_CHECKS.get(capability) or _HEALTH_CHECKS.get("memory" if "episodic" in capability else capability)
            healthy = bool(check()) if callable(check) else True
            rows.append(
                {
                    "capability": capability,
                    "role": "memory" if capability.startswith("episodic") or capability == "memory" else capability,
                    "configured_model": None,
                    "selected_model": None,
                    "provider": provider,
                    "healthy": healthy,
                    "fallback_active": False,
                    "status": "ok" if healthy else "degraded",
                }
            )
            continue

        selection = select_model_for_role(role)
        model = selection.selected_model
        healthy = True
        if selection.provider == "ollama":
            healthy = ollama_up and (not model or _model_installed(model))
        rows.append(
            {
                "capability": capability,
                "role": role,
                "configured_model": selection.configured_model,
                "selected_model": model,
                "provider": selection.provider,
                "healthy": healthy,
                "fallback_active": selection.fallback_active,
                "status": "ok" if healthy else "degraded",
                "policy_reason": selection.policy_reason,
            }
        )
    return rows


def _model_installed(name: str) -> bool:
    try:
        from jarvis.ollama_health import model_available

        return bool(model_available(name))
    except Exception:
        return True


def format_capability_health_markdown(rows: list[dict[str, Any]] | None = None) -> str:
    data = rows or capability_health_report()
    lines = ["## Capability health", ""]
    for row in data:
        mark = "✓" if row.get("healthy") else "✗"
        cap = row.get("capability", "?")
        role = row.get("role", "—")
        model = row.get("selected_model") or row.get("configured_model") or "none"
        provider = row.get("provider", "—")
        fb = " (fallback)" if row.get("fallback_active") else ""
        lines.append(f"- **{cap.title()}** {mark} — role `{role}`, model `{model}`{fb}, provider `{provider}`")
    return "\n".join(lines)
