"""Experimental Integrations surfaces — honest research stubs."""

from __future__ import annotations

from typing import Any


def experimental_status() -> dict[str, Any]:
    return {
        "ok": True,
        "items": [
            {
                "id": "os_keychain",
                "name": "OS keychain / libsecret",
                "available": False,
                "status": "research",
                "summary": "Store secrets in the OS keyring instead of plaintext jarvis.env. Not implemented.",
            },
            {
                "id": "encrypted_vault",
                "name": "Encrypted vault",
                "available": False,
                "status": "research",
                "summary": "Local encrypted secret store. Not implemented — current storage is plaintext.",
            },
            {
                "id": "oauth_profiles",
                "name": "OAuth connector profiles",
                "available": False,
                "status": "research",
                "summary": "OAuth for calendar/email providers. Placeholder auth_type only today.",
            },
            {
                "id": "platform_secrets_unify",
                "name": "AI-Platform SecretsManager unification",
                "available": False,
                "status": "research",
                "summary": "Merge Jarvis jarvis.env with Platform secrets.json carefully — not auto-merged.",
            },
            {
                "id": "async_connectors",
                "name": "Async connector runtime",
                "available": False,
                "status": "research",
                "summary": "Replace blocking rate-limit sleeps with async scheduling.",
            },
            {
                "id": "nl_setup",
                "name": "Natural-language provider setup",
                "available": True,
                "status": "prototype_ready",
                "summary": "Suggest which provider to configure from a short prompt — never auto-saves keys.",
            },
        ],
    }


def nl_setup_suggest(prompt: str) -> dict[str, Any]:
    text = (prompt or "").lower()
    suggestions = []
    mapping = [
        (("cloud live", "gemini", "google voice"), "gemini", "Add Gemini API key for Cloud Live voice."),
        (("openai", "realtime"), "openai", "Add OpenAI key (Realtime client still gated)."),
        (("claude", "anthropic"), "anthropic", "Add Anthropic key for LiteLLM cloud chat."),
        (("openrouter",), "openrouter", "Add OpenRouter key for multi-model routing."),
        (("meshy", "3d", "cad"), "meshy", "Add Meshy key for Engineering text-to-3D."),
        (("home assistant", "ha "), "home_assistant", "Configure Home Assistant in Smart Home Home."),
        (("webhook", "n8n", "automation"), "automation_webhook", "Manage inbound webhook in Automation Home."),
    ]
    for needles, pid, msg in mapping:
        if any(n in text for n in needles):
            suggestions.append({"provider_id": pid, "message": msg})
    if not suggestions:
        suggestions.append(
            {
                "provider_id": "gemini",
                "message": "Most operators start with Gemini for Cloud Live. Open Integrations Home to paste a key.",
            }
        )
    return {
        "ok": True,
        "suggestions": suggestions,
        "note": "Suggestions only — Aria never auto-creates cloud accounts or auto-saves keys from chat.",
    }
