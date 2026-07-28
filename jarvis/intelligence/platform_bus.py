"""System integration bus — wires memory, RAG, agents, graph, automation, vision, voice."""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger("jarvis.intelligence.platform_bus")


def platform_status() -> dict[str, Any]:
    """Report health of all intelligence subsystems."""
    subsystems: dict[str, Any] = {}

    def probe(name: str, fn) -> None:
        try:
            subsystems[name] = fn()
        except Exception as exc:
            subsystems[name] = {"ok": False, "error": str(exc)}

    probe("memory", lambda: __import__("jarvis.intelligence.memory_platform", fromlist=["memory_status"]).memory_status())
    probe(
        "rag",
        lambda: {
            "ok": True,
            "module": "jarvis.intelligence.hybrid_rag",
            "capabilities": ["hybrid", "rerank", "citations", "query_expansion"],
        },
    )
    probe(
        "reasoning",
        lambda: {"ok": True, "module": "jarvis.intelligence.reasoning"},
    )
    probe(
        "agents",
        lambda: {"ok": True, "module": "jarvis.intelligence.multi_agent"},
    )
    probe(
        "knowledge_graph",
        lambda: {
            "ok": True,
            **__import__("jarvis.intelligence.knowledge_graph", fromlist=["search_graph"]).search_graph("", limit=1),
        },
    )
    probe(
        "automation",
        lambda: __import__("jarvis.intelligence.automation_engine", fromlist=["status"]).status(),
    )
    probe(
        "workflows",
        lambda: {
            "ok": True,
            "templates": list(
                __import__("jarvis.intelligence.workflow_engine", fromlist=["TEMPLATES"]).TEMPLATES.keys()
            ),
            "saved": __import__("jarvis.intelligence.workflow_engine", fromlist=["list_workflows"]).list_workflows(),
        },
    )
    probe(
        "plugins",
        lambda: {"ok": True, "plugins": __import__("jarvis.intelligence.plugin_sdk", fromlist=["list_plugins"]).list_plugins()},
    )
    probe(
        "connectors",
        lambda: {
            "ok": True,
            "connectors": __import__("jarvis.intelligence.connectors", fromlist=["list_connectors"]).list_connectors(),
        },
    )
    probe(
        "documents",
        lambda: {
            "ok": True,
            "extensions": __import__(
                "jarvis.intelligence.document_intel", fromlist=["supported_extensions"]
            ).supported_extensions(),
        },
    )

    # Existing strong systems (presence probes)
    for name, mod in (
        ("home_assistant", "jarvis.home_assistant"),
        ("vision", "jarvis.modules.vision"),
        ("voice_stt", "jarvis.stt"),
        ("coding", "jarvis.coding_agent"),
        ("models", "jarvis.model_store"),
    ):
        def _check(m=mod):
            __import__(m)
            return {"ok": True, "module": m}

        probe(name, _check)

    ok = all(isinstance(v, dict) and v.get("ok", True) for v in subsystems.values())
    return {"ok": ok, "subsystems": subsystems}


def intelligent_query(
    query: str,
    *,
    assistant: Any | None = None,
    use_agents: bool = False,
    use_reasoning: bool = True,
    use_rag: bool = True,
    use_graph: bool = True,
    use_memory: bool = True,
) -> dict[str, Any]:
    """End-to-end intelligence path: memory + RAG + graph + reasoning (+ optional agents)."""
    q = (query or "").strip()
    if not q:
        return {"ok": False, "error": "empty_query"}

    result: dict[str, Any] = {"ok": True, "query": q, "parts": {}}

    if use_memory:
        from jarvis.intelligence.memory_platform import search_memories

        result["parts"]["memory"] = search_memories(q, limit=5)

    if use_rag:
        from jarvis.intelligence.hybrid_rag import hybrid_search

        result["parts"]["rag"] = hybrid_search(q, limit=5)

    if use_graph:
        from jarvis.intelligence.knowledge_graph import search_graph

        # Read-only: never soft-ingest queries (graph pollution prevention)
        result["parts"]["graph"] = search_graph(q, limit=8)

    if use_reasoning:
        from jarvis.intelligence.reasoning import reason

        result["parts"]["reasoning"] = reason(q, assistant=assistant, use_rag=False)

    if use_agents and assistant is not None:
        from jarvis.intelligence.multi_agent import run_multi_agent

        result["parts"]["agents"] = run_multi_agent(assistant, q, stop_on_error=False, max_agents=4)

    # Compose answer scaffold
    citations = (result["parts"].get("rag") or {}).get("citations") or []
    plan = (result["parts"].get("reasoning") or {}).get("plan") or []
    confidence = (result["parts"].get("reasoning") or {}).get("confidence")
    result["answer"] = {
        "plan": plan,
        "confidence": confidence,
        "citations": citations,
        "summary": (result["parts"].get("reasoning") or {}).get("summary") or "",
    }
    return result


def bootstrap_platform(*, start_automation: bool = True) -> dict[str, Any]:
    """Initialize connectors, optional example plugin, automation engine."""
    import os

    from jarvis.intelligence.connectors import bootstrap_default_connectors
    from jarvis.intelligence.plugin_sdk import create_example_plugin, load_all

    if os.getenv("JARVIS_DISABLE_INTEL_BOOTSTRAP", "").strip().lower() in ("1", "true", "yes"):
        return {"ok": True, "skipped": True}

    created = []
    connectors = bootstrap_default_connectors()
    try:
        path = create_example_plugin()
        created.append(str(path))
    except Exception as exc:
        log.debug("example plugin: %s", exc)

    plugins = load_all()

    # Ensure default pipeline templates exist on disk once (reuse by name — no spam)
    saved_wf = []
    try:
        from jarvis.automation.pipelines.storage import create_from_template

        for tid in ("morning_routine", "doc_ingest", "evening_wrap"):
            wf = create_from_template(tid)
            if not wf.get("reused"):
                saved_wf.append(wf["id"])
    except Exception as exc:
        log.debug("workflow bootstrap: %s", exc)

    automation = {"running": False}
    disable_auto = os.getenv("JARVIS_DISABLE_INTEL_AUTOMATION", "").strip().lower() in ("1", "true", "yes")
    if start_automation and not disable_auto:
        from jarvis.intelligence.automation_engine import start_engine

        automation = start_engine()

    return {
        "ok": True,
        "connectors": connectors,
        "example_plugins": created,
        "plugins": plugins,
        "workflows_seeded": saved_wf,
        "automation": automation,
        "status": platform_status(),
    }
