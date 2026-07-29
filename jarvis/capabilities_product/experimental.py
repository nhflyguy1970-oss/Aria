"""Experimental surfaces — honest stubs (isolation, signing, MCP, NL generator)."""

from __future__ import annotations

from typing import Any


def experimental_status() -> dict[str, Any]:
    return {
        "ok": True,
        "items": [
            {
                "id": "process_isolation",
                "name": "Process isolation",
                "status": "research",
                "available": False,
                "summary": "Run untrusted capabilities in a subprocess with IPC. Not implemented.",
            },
            {
                "id": "wasm",
                "name": "WASM sandbox",
                "status": "research",
                "available": False,
                "summary": "Execute constrained WASM guests. Not implemented.",
            },
            {
                "id": "seccomp",
                "name": "Seccomp / firejail",
                "status": "research",
                "available": False,
                "summary": "Host already has firejail for code execution; not wired to Capabilities.",
            },
            {
                "id": "signed_bundles",
                "name": "Signed local bundles",
                "status": "research",
                "available": False,
                "summary": "Local signature verification for capability packs. No public marketplace.",
            },
            {
                "id": "mcp_bridge",
                "name": "MCP import/export bridge",
                "status": "prototype_ready",
                "available": True,
                "summary": "List Aria contribution tools in MCP-shaped descriptors; import is dry-run only.",
            },
            {
                "id": "nl_generator",
                "name": "Natural-language capability stub generator",
                "status": "prototype_ready",
                "available": True,
                "summary": "Writes a local stub under data/plugins for operator review — never auto-enables.",
            },
        ],
    }


def mcp_export_tools() -> dict[str, Any]:
    from jarvis.capabilities_product.contributions import list_agent_tools

    tools = list_agent_tools()
    return {
        "ok": True,
        "format": "mcp_tool_descriptors_v0",
        "tools": [
            {
                "name": t.get("name") or t.get("id"),
                "description": t.get("description") or "",
                "inputSchema": t.get("input_schema") or {"type": "object", "properties": {}},
                "capability_id": t.get("capability_id"),
            }
            for t in tools
        ],
        "note": "Export only — does not start an MCP server.",
    }


def mcp_import_preview(servers: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "ok": True,
        "imported": 0,
        "preview": servers or [],
        "message": (
            "MCP import is dry-run only. Enabling foreign MCP servers as live Capabilities "
            "requires explicit trust review and is not automatic."
        ),
    }


def nl_generate_stub(prompt: str) -> dict[str, Any]:
    """Create a disabled local capability stub from a short description."""
    import json
    import re
    from pathlib import Path

    from jarvis.config import DATA_DIR
    from jarvis.capabilities_product.history import record_activity

    text = (prompt or "").strip()
    if not text:
        return {"ok": False, "message": "prompt required"}
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:40] or "custom_capability"
    slug = f"nl_{slug}"
    root = Path(DATA_DIR) / "plugins" / slug
    root.mkdir(parents=True, exist_ok=True)
    manifest = {
        "id": slug,
        "name": text[:80],
        "version": "0.1.0",
        "description": f"NL-generated stub (review before enable): {text}",
        "entry": "plugin:register",
        "permissions": [],
        "sandbox": False,
        "experimental": True,
        "category": "Experimental",
        "contributions": {
            "actions": [
                {
                    "name": f"{slug}_info",
                    "description": f"Info for {text[:40]}",
                    "patterns": [f"tell me about {slug.replace('_', ' ')}"],
                    "reply": f"Capability stub '{text[:60]}' is installed but experimental. Review permissions in Capabilities Home before relying on it.",
                    "info": True,
                }
            ]
        },
    }
    (root / "aria_plugin.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (root / "plugin.py").write_text(
        "def register(ctx):\n"
        "    return {'ok': True, 'experimental': True}\n",
        encoding="utf-8",
    )
    from jarvis.capabilities_product import policy as cap_policy

    cap_policy.set_enabled(f"sdk:{slug}", False)
    cap_policy.set_trust_override(f"sdk:{slug}", "experimental")
    record_activity("nl_stub", capability_id=f"sdk:{slug}", message="Generated experimental stub (disabled)")
    return {
        "ok": True,
        "id": f"sdk:{slug}",
        "path": str(root),
        "enabled": False,
        "message": "Stub written and left DISABLED for review. No automatic enable.",
    }
