# Aria Next-Generation Intelligence Platform

**Date:** 2026-07-27  
**Package:** `jarvis/intelligence/`  
**API prefix:** `/api/intelligence/*`

---

## Executive summary

Aria already had strong local organs (ACM memory, HA, vision, voice, coding, models). This platform layer **closes production gaps** and **integrates** them into one local-first intelligence operating environment:

| Phase | Capability | Module |
|------|------------|--------|
| 1 | Long-term memory facade (search/consolidate/import/export) | `memory_platform.py` |
| 2 | Multi-step reasoning + self-check + confidence | `reasoning.py` |
| 3 | Document intelligence (csv/xlsx/pptx/code + tags/entities/OCR) | `document_intel.py` (+ `document_pipeline` extensions) |
| 4 | Hybrid RAG (keyword+vector, expansion, rerank, citations) | `hybrid_rag.py` |
| 5 | Multi-agent specialists + shared scratchpad | `multi_agent.py` |
| 6 | User automations (cron/interval/watch) | `automation_engine.py` |
| 7 | Workflow DAG (templates, retries, conditions) | `workflow_engine.py` |
| 8–12 | HA / Vision / Voice / Coding / Models | Existing strong modules — probed by `platform_bus` |
| 13 | Plugin SDK (manifest, permissions, sandbox context) | `plugin_sdk.py` |
| 14 | Unified connectors (retry, rate limit, cache) | `connectors.py` |
| 15 | Knowledge graph ingest/search | `knowledge_graph.py` + **Connections** UI (`connections_services.py`) |
| 16 | System integration bus | `platform_bus.py` |

GUI was **not** redesigned. Routes are API-first; existing UI can call them.

---

## Architecture

```
Chat / API / Scheduler
        │
        ▼
 platform_bus.intelligent_query / bootstrap_platform
        │
 ┌──────┼──────────────┬─────────────┬──────────────┐
 ▼      ▼              ▼             ▼              ▼
memory  hybrid_rag   reasoning   multi_agent   knowledge_graph
  │        │             │            │              │
  └────────┴──────┬──────┴────────────┴──────┐       │
                  ▼                          ▼       ▼
           workflow_engine            automation_engine
                  │                          │
                  └──────────┬───────────────┘
                             ▼
                    connectors / plugins
```

Graceful degradation: if embeddings, HA, vision OCR, or actions are missing, subsystems return structured errors and continue.

---

## API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/intelligence/status` | Subsystem health matrix |
| POST | `/api/intelligence/bootstrap` | Seed connectors/plugins/workflows/automation |
| POST | `/api/intelligence/query` | End-to-end memory+RAG+graph+reasoning (+agents) |
| POST | `/api/intelligence/rag/search` | Hybrid RAG with citations |
| POST | `/api/intelligence/reason` | Reasoning trace |
| POST | `/api/intelligence/agents/run` | Multi-agent run |
| GET/POST | `/api/intelligence/memory/*` | Status/search/consolidate/export/import |
| GET/POST | `/api/intelligence/graph/*` | Ingest(propose)/search/neighbors — product UI is `/api/connections/*` |
| GET/POST/DELETE | `/api/intelligence/automation*` | Rules + run + start |
| GET/POST | `/api/intelligence/workflows*` | List/templates/run |
| GET/POST | `/api/intelligence/plugins*` | Discover/load |
| GET | `/api/intelligence/connectors` | Registered connectors |
| POST/GET | `/api/intelligence/documents/*` | Analyze + extensions |

Routes register from `extra_routes` via `register_intelligence_routes`. Bootstrap also runs softly from `platform_runtime.bootstrap_runtime_connection`.

---

## Configuration

| Env / path | Role |
|------------|------|
| `DATA_DIR/user_automations.json` | Automation rules |
| `DATA_DIR/workflows/*.json` | Saved workflow definitions |
| `DATA_DIR/plugins/*/aria_plugin.json` | Plugin manifests |
| `DATA_DIR/memory_exports/` | Memory export snapshots |
| `JARVIS_GRAPH_BACKEND` | `sqlite` (default) / `memgraph` / `neo4j` |
| `JARVIS_REASONING_LLM` | Set `1` to allow optional LLM plan revision |

---

## Testing

```bash
venv/bin/pytest tests/test_intelligence_platform.py -q
```

Coverage includes: hybrid RAG, reasoning, graph ingest, automation CRUD, workflow retries, plugin load, connectors, document CSV analysis, multi-agent specialist resolution, route registration, and HTTP status/RAG endpoints.

---

## Examples

**Hybrid search**
```bash
curl -s -X POST http://127.0.0.1:8765/api/intelligence/rag/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"planner tasks","limit":5}'
```

**Intelligent query**
```bash
curl -s -X POST http://127.0.0.1:8765/api/intelligence/query \
  -H 'Content-Type: application/json' \
  -d '{"query":"Summarize what Aria remembers about projects","use_agents":false}'
```

**Create + run workflow**
```bash
curl -s -X POST http://127.0.0.1:8765/api/intelligence/workflows/from-template \
  -H 'Content-Type: application/json' \
  -d '{"template":"morning_routine"}'
# then POST /api/intelligence/workflows/{id}/run
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| RAG mode=`keyword` | Embed model offline — start Ollama embed role |
| Graph empty | Open **Connections** → Import for review → Approve; or POST `/api/connections/propose` |
| Query pollution | Soft-ingest disabled; use Cleanup → queries namespace |
| Automation not firing | POST `/api/intelligence/automation/start`; check rule `enabled` |
| Plugin load error | Validate `aria_plugin.json` entry `module:attr` and permissions |
| Document xlsx/pptx fail | Install `openpyxl` / `python-pptx` |

---

## Future extension points

1. Cross-encoder rerank models for RAG  
2. True inotify watchers (currently mtime polling)  
3. Visual workflow editor wired to `workflow_engine` JSON  
4. Stronger capability isolation (process/WASM) — see `docs/CAPABILITIES_IMPLEMENTATION.md`  
5. OAuth connector profiles — see `docs/INTEGRATIONS_IMPLEMENTATION.md` (experimental)  
6. Stream reasoning traces over WebSocket to Chat UI  

**Operator note:** Provider keys and health are managed as **Integrations**.  
“External APIs” refers to the connector runtime architecture.  
See `docs/INTEGRATIONS_IMPLEMENTATION.md` and `docs/CAPABILITIES_IMPLEMENTATION.md`.

See also: `docs/ARIA_COGNITIVE_MEMORY.md`, `docs/KNOWLEDGE.md`, capability inventory under `docs/aria_core/`.
