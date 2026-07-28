"""Specialist catalog — deep mappings to real Aria organs (not toy action stubs)."""

from __future__ import annotations

from typing import Any

# read_only specialists may run in parallel. write specialists need approval when budgets.require_write_approval.
SPECIALISTS: dict[str, dict[str, Any]] = {
    "planner": {
        "id": "planner",
        "name": "Planner",
        "role": "planning",
        "description": "Creates structured plans and tasks via Planner APIs.",
        "capabilities": ["plan", "tasks"],
        "permissions": ["planner"],
        "read_only": True,
        "organ": "planner",
        "documentation": "Proposes structured plans — does not auto-add Planner tasks.",
    },
    "researcher": {
        "id": "researcher",
        "name": "Researcher",
        "role": "research",
        "description": "Searches memory, documents, and knowledge for grounded answers.",
        "capabilities": ["search", "rag", "memory"],
        "permissions": ["memory", "documents"],
        "read_only": True,
        "organ": "search",
        "documentation": "unified_search + document_search + memory_search.",
    },
    "coder": {
        "id": "coder",
        "name": "Coder",
        "role": "coding",
        "description": "Delegates to CodingAgent propose→review loop (not a shallow read stub).",
        "capabilities": ["code", "diagnose", "propose"],
        "permissions": ["coding"],
        "read_only": False,
        "organ": "coding_agent",
        "documentation": "Calls CodingAgent.run / diagnose with assistant.coding._base(); stores proposals for Apply.",
    },
    "writer": {
        "id": "writer",
        "name": "Writer",
        "role": "documentation",
        "description": "Drafts summaries and documentation in-chat — does not auto-append journal.",
        "capabilities": ["draft", "summarize"],
        "permissions": ["chat"],
        "read_only": True,
        "organ": "draft",
        "documentation": "Returns a draft artifact; journal write requires explicit approval.",
    },
    "critic": {
        "id": "critic",
        "name": "Critic",
        "role": "qa",
        "description": "Reviews outputs and optionally runs tests.",
        "capabilities": ["review", "tests"],
        "permissions": ["coding", "tests"],
        "read_only": True,
        "organ": "qa",
        "documentation": "Critique notes + optional run_tests.",
    },
    "reviewer": {
        "id": "reviewer",
        "name": "Reviewer",
        "role": "qa",
        "description": "Alias of Critic for QA review.",
        "capabilities": ["review"],
        "permissions": ["coding"],
        "read_only": True,
        "organ": "qa",
        "alias_of": "critic",
    },
    "memory": {
        "id": "memory",
        "name": "Memory",
        "role": "memory",
        "description": "Recalls and summarizes relevant long-term memory.",
        "capabilities": ["recall"],
        "permissions": ["memory"],
        "read_only": True,
        "organ": "memory",
    },
    "documents": {
        "id": "documents",
        "name": "Documents",
        "role": "knowledge",
        "description": "Document / RAG search with citations when available.",
        "capabilities": ["documents", "rag"],
        "permissions": ["documents"],
        "read_only": True,
        "organ": "documents",
    },
    "graph": {
        "id": "graph",
        "name": "Knowledge Graph",
        "role": "knowledge",
        "description": "Searches Connections / knowledge graph.",
        "capabilities": ["graph"],
        "permissions": ["knowledge"],
        "read_only": True,
        "organ": "knowledge_graph",
    },
    "vision": {
        "id": "vision",
        "name": "Vision",
        "role": "vision",
        "description": "Real vision describe/OCR actions.",
        "capabilities": ["describe", "ocr"],
        "permissions": ["vision"],
        "read_only": True,
        "organ": "vision",
        "documentation": "describe_image / ocr_image — never vision_describe.",
    },
    "voice": {
        "id": "voice",
        "name": "Voice",
        "role": "voice",
        "description": "Voice smoke / status checks.",
        "capabilities": ["voice"],
        "permissions": ["voice"],
        "read_only": True,
        "organ": "voice",
    },
    "home": {
        "id": "home",
        "name": "Home",
        "role": "home",
        "description": "Home Assistant status (read-only by default).",
        "capabilities": ["ha_status"],
        "permissions": ["home_assistant"],
        "read_only": True,
        "organ": "home_assistant",
    },
    "operations": {
        "id": "operations",
        "name": "Operations",
        "role": "operations",
        "description": "Workstation diagnose / health.",
        "capabilities": ["diagnose"],
        "permissions": ["system"],
        "read_only": True,
        "organ": "workstation",
    },
    "automation": {
        "id": "automation",
        "name": "Automation",
        "role": "automation",
        "description": "Summarizes Automation Home status (does not enable rules).",
        "capabilities": ["automation_status"],
        "permissions": ["automation"],
        "read_only": True,
        "organ": "automation",
    },
    "synthesizer": {
        "id": "synthesizer",
        "name": "Synthesizer",
        "role": "synthesis",
        "description": "Merges specialist outputs into one coherent answer.",
        "capabilities": ["synthesize"],
        "permissions": ["chat"],
        "read_only": True,
        "organ": "synthesis",
        "internal": True,
    },
}

# Legacy coordinator role → specialist id
ROLE_TO_SPECIALIST: dict[str, str] = {
    "planning": "planner",
    "research": "researcher",
    "coding": "coder",
    "documentation": "writer",
    "qa": "critic",
    "knowledge": "documents",
    "memory": "memory",
    "automation": "automation",
    "operations": "operations",
    "monitoring": "operations",
    "deployment": "operations",
    "training": "operations",
    "vision": "vision",
    "voice": "voice",
    "home": "home",
}


def list_gallery(*, include_internal: bool = False) -> list[dict[str, Any]]:
    out = []
    for sid, meta in SPECIALISTS.items():
        if meta.get("internal") and not include_internal:
            continue
        if meta.get("alias_of"):
            continue
        out.append({**meta})
    return out


def get_specialist(specialist_id: str) -> dict[str, Any] | None:
    sid = (specialist_id or "").strip().lower()
    # map legacy roles
    sid = ROLE_TO_SPECIALIST.get(sid, sid)
    meta = SPECIALISTS.get(sid)
    if not meta:
        return None
    if meta.get("alias_of"):
        return get_specialist(str(meta["alias_of"]))
    return dict(meta)


def normalize_team(ids: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in ids:
        meta = get_specialist(raw)
        if not meta:
            continue
        sid = meta["id"]
        if sid in seen or sid == "synthesizer":
            continue
        seen.add(sid)
        out.append(sid)
    return out
